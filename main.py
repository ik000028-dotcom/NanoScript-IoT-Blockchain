from fastapi import FastAPI, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
import psycopg2
import requests
from psycopg2 import pool
import hashlib
import json

app = FastAPI(title="IoT Data API - Single Hash Source")

connection_pool = pool.SimpleConnectionPool(
    minconn=2,
    maxconn=20,
    host="/tmp",
    database="iot_data",
    user="ikramsmac"
)

def get_db_connection():
    return connection_pool.getconn()

def release_db_connection(conn):
    connection_pool.putconn(conn)

class SensorData(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_fix: Optional[bool] = None

@app.post("/data")
async def receive_data(data: SensorData):
    """L3: Compute hash ONCE here, store in DB"""
    data_dict = {k: v for k, v in data.dict().items() if v is not None}
    if not data_dict:
        raise HTTPException(status_code=400, detail="Empty payload — no sensor values provided")
    
    conn = get_db_connection()
    try:
        # Use ONE timestamp for both hash and DB insert
        ts = datetime.now(timezone.utc)
        ts_iso = ts.isoformat()

        data_dict_with_ts = data_dict.copy()
        data_dict_with_ts['timestamp'] = ts_iso
        canonical_json = json.dumps(data_dict_with_ts, sort_keys=True, separators=(',',':'))
        data_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sensor_data (time, temperature, humidity, latitude, longitude, data_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ts, data.temperature, data.humidity, data.latitude, data.longitude, data_hash))
        conn.commit()
        cur.close()
        return {
            "status": "success",
            "hash": data_hash,
            "source": "L3_FastAPI"
        }
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_connection(conn)

@app.get("/batch/unconfirmed")
async def get_unconfirmed_batch(limit: int = 10):
    """L5: Read pre-computed hashes from DB"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT time, temperature, humidity, latitude, longitude, data_hash 
            FROM sensor_data 
            WHERE blockchain_tx IS NULL AND data_hash IS NOT NULL
            AND (temperature IS NOT NULL OR humidity IS NOT NULL)
            ORDER BY time ASC 
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        batch = []
        for row in rows:
            batch.append({
                "time": str(row[0]),
                "data": {
                    "temperature": row[1],
                    "humidity": row[2],
                    "latitude": row[3],
                    "longitude": row[4]
                },
                "hash": row[5]
            })
        return {"batch": batch, "count": len(batch), "recomputed": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_connection(conn)

@app.post("/confirm")
async def confirm_batch(blockchain_tx: str, hashes: list[str]):
    """Mark specific records as confirmed using their hashes"""
    if not hashes:
        raise HTTPException(status_code=400, detail="No hashes provided")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE sensor_data 
            SET blockchain_tx = %s, confirmed_at = NOW()
            WHERE data_hash = ANY(%s)
        """, (blockchain_tx, hashes))
        updated = cur.rowcount
        conn.commit()
        cur.close()
        return {"status": "confirmed", "count": updated, "tx": blockchain_tx, "hashes": hashes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_connection(conn)

@app.post("/generate-batch")
async def generate_batch():
    """L5: Fetch 200 hashes, compute master hash, seal on Hyperledger via CLI"""
    import subprocess, os
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Step 1: Fetch exactly 200 complete unconfirmed records
        cur.execute("""
            SELECT data_hash, time FROM sensor_data
            WHERE blockchain_tx IS NULL AND data_hash IS NOT NULL
            AND temperature IS NOT NULL AND humidity IS NOT NULL
            ORDER BY time ASC
            LIMIT 200
        """)
        rows = cur.fetchall()

        if len(rows) < 200:
            cur.close()
            return {
                "status": "waiting",
                "message": f"Only {len(rows)} complete records available, need 200"
            }

        # Step 2: Compute master hash from all 200 individual hashes
        individual_hashes = [row[0] for row in rows]
        combined = ''.join(individual_hashes)
        master_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        batch_start = rows[0][1]
        batch_id = f"batch_{batch_start.strftime('%Y%m%d_%H%M%S')}"

        # Step 3: Submit to Hyperledger via Fabric CLI
        home = os.path.expanduser("~")
        tn = f"{home}/fabric-samples/test-network"
        env = os.environ.copy()
        env["FABRIC_CFG_PATH"] = f"{home}/fabric-samples/config"
        env["CORE_PEER_TLS_ENABLED"] = "true"
        env["CORE_PEER_LOCALMSPID"] = "Org1MSP"
        env["CORE_PEER_ADDRESS"] = "localhost:7051"
        env["CORE_PEER_MSPCONFIGPATH"] = f"{tn}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
        env["CORE_PEER_TLS_ROOTCERT_FILE"] = f"{tn}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
        env["PATH"] = f"{home}/fabric-samples/bin:" + env.get("PATH", "")

        payload = json.dumps({"function": "storeHash", "Args": [batch_id, master_hash]})
        cmd = [
            f"{home}/fabric-samples/bin/peer", "chaincode", "invoke",
            "-o", "localhost:7050",
            "--ordererTLSHostnameOverride", "orderer.example.com",
            "--tls", "--cafile",
            f"{tn}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem",
            "-C", "mychannel", "-n", "iot_hash",
            "-c", payload,
            "--peerAddresses", "localhost:7051",
            "--tlsRootCertFiles",
            f"{tn}/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem",
            "--peerAddresses", "localhost:9051",
            "--tlsRootCertFiles",
            f"{tn}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)

        if result.returncode == 0:
            blockchain_tx = batch_id
            blockchain_status = "sealed"
        else:
            # Fabric failed — store pending with master hash
            blockchain_tx = f"pending_{master_hash[:16]}"
            blockchain_status = "pending_blockchain"
            print(f"Fabric error: {result.stderr[:200]}")

        # Step 4: Mark those 200 records as confirmed in Postgres
        cur.execute("""
            UPDATE sensor_data
            SET blockchain_tx = %s, confirmed_at = NOW()
            WHERE data_hash = ANY(%s)
        """, (blockchain_tx, individual_hashes))
        conn.commit()
        cur.close()

        return {
            "status": blockchain_status,
            "master_hash": master_hash,
            "blockchain_tx": blockchain_tx,
            "records_sealed": len(individual_hashes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_db_connection(conn)

@app.get("/")
async def root():
    return {"message": "IoT API - L3 computes hash, L5 reuses", "endpoints": ["/data", "/batch/unconfirmed", "/confirm", "/generate-batch"]}
