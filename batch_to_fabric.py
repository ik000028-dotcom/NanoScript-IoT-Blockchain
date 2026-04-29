#!/usr/bin/env python3
import subprocess
import json
import os
import hashlib
import psycopg2
from datetime import datetime

class FabricBatchSubmitter:
    def __init__(self):
        self._setup_env()
        self.channel = "mychannel"
        self.chaincode = "iot_hash"

    def _setup_env(self):
        home = os.path.expanduser("~")
        fabric = f"{home}/fabric-samples"
        tn = f"{fabric}/test-network"

        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.env.get('PATH', '')}:{fabric}/bin"
        self.env["FABRIC_CFG_PATH"] = f"{fabric}/config"
        self.env["CORE_PEER_TLS_ENABLED"] = "true"
        self.env["CORE_PEER_LOCALMSPID"] = "Org1MSP"
        self.env["CORE_PEER_ADDRESS"] = "localhost:7051"
        self.env["CORE_PEER_MSPCONFIGPATH"] = f"{tn}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
        self.env["CORE_PEER_TLS_ROOTCERT_FILE"] = f"{tn}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"

        self.tn = tn
        self.fabric = fabric

    def get_records(self, limit=200):
        conn = psycopg2.connect(dbname="iot_data", user="ikramsmac", password="", host="/tmp")
        cur = conn.cursor()
        cur.execute("""
            SELECT time, temperature, humidity, latitude, longitude, data_hash
            FROM sensor_data
            WHERE blockchain_tx IS NULL AND data_hash IS NOT NULL
            AND (temperature IS NOT NULL OR humidity IS NOT NULL)
            ORDER BY time ASC
            LIMIT %s
        """, (limit,))
        records = cur.fetchall()
        cur.close()
        conn.close()
        return records

    def submit_batch(self, batch_id, records):
        # Compute master hash
        hash_values = [r[5] for r in records]
        combined = ''.join(hash_values)
        master_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        print(f"Master hash to seal: {master_hash}")

        payload = json.dumps({
            "function": "storeHash",
            "Args": [batch_id, master_hash]
        })

        cmd = [
            "peer", "chaincode", "invoke",
            "-o", "localhost:7050",
            "--ordererTLSHostnameOverride", "orderer.example.com",
            "--tls", "--cafile",
            f"{self.tn}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem",
            "-C", self.channel,
            "-n", self.chaincode,
            "-c", payload,
            "--peerAddresses", "localhost:7051",
            "--tlsRootCertFiles",
            f"{self.tn}/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem",
            "--peerAddresses", "localhost:9051",
            "--tlsRootCertFiles",
            f"{self.tn}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, env=self.env)
        return result.returncode == 0, result.stdout, result.stderr, master_hash

if __name__ == "__main__":
    submitter = FabricBatchSubmitter()
    records = submitter.get_records(200)
    print(f"Found {len(records)} unconfirmed complete records")

    if len(records) < 200:
        print(f"⚠️  Need 200 records, only have {len(records)}")
    else:
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success, stdout, stderr, master_hash = submitter.submit_batch(batch_id, records)

        if success:
            print(f"✅ Batch {batch_id} sealed on blockchain!")
            print(f"✅ Master hash: {master_hash}")
            # Mark these 200 records as confirmed in PostgreSQL
            hash_values = [r[5] for r in records]
            conn = psycopg2.connect(dbname="iot_data", user="ikramsmac", password="", host="/tmp")
            cur = conn.cursor()
            cur.execute("""
                UPDATE sensor_data
                SET blockchain_tx = %s, confirmed_at = NOW()
                WHERE data_hash = ANY(%s)
            """, (batch_id, hash_values))
            conn.commit()
            cur.close()
            conn.close()
            print(f"✅ {cur.rowcount} records marked as confirmed in PostgreSQL")
        else:
            print(f"❌ Failed to submit batch")
            print("Error:", stderr[:300])
