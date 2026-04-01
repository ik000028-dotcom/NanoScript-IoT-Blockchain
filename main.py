from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg2
import hashlib
import json

app = FastAPI(title="IoT Data API - Single Hash Source")

def get_db_connection():
    return psycopg2.connect(host="localhost", database="iot_data", user="ikramsmac")

class SensorData(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@app.post("/data")
async def receive_data(data: SensorData):
    """L3: Compute hash ONCE here, store in DB"""
    try:
        data_dict = {k: v for k, v in data.dict().items() if v is not None}
        canonical_json = json.dumps(data_dict, sort_keys=True, separators=(',',':'))
        data_hash = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO sensor_data (time, temperature, humidity, latitude, longitude, data_hash)
            VALUES (NOW(), %s, %s, %s, %s, %s)
        """, (data.temperature, data.humidity, data.latitude, data.longitude, data_hash))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "status": "success", 
            "hash": data_hash,
            "source": "L3_FastAPI"
        }
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batch/unconfirmed")
async def get_unconfirmed_batch(limit: int = 10):
    """L5: Read pre-computed hashes from DB"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT time, temperature, humidity, latitude, longitude, data_hash 
        FROM sensor_data 
        WHERE blockchain_tx IS NULL AND data_hash IS NOT NULL
        ORDER BY time ASC 
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
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

@app.post("/confirm")
async def confirm_batch(blockchain_tx: str, limit: int = 10):
    """Mark oldest unconfirmed records as confirmed"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE sensor_data 
        SET blockchain_tx = %s, confirmed_at = NOW()
        WHERE time IN (
            SELECT time FROM sensor_data 
            WHERE blockchain_tx IS NULL 
            ORDER BY time ASC 
            LIMIT %s
        )
    """, (blockchain_tx, limit))
    updated = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "confirmed", "count": updated, "tx": blockchain_tx}

@app.get("/")
async def root():
    return {"message": "IoT API - L3 computes hash, L5 reuses", "endpoints": ["/data", "/batch/unconfirmed", "/confirm"]}
