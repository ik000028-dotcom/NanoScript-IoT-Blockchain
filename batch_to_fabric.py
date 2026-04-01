#!/usr/bin/env python3
"""
Batch Hash Generator - Reads from PostgreSQL, submits to Hyperledger Fabric
Uses CLI (proven working method)
"""

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
        """Setup Fabric environment"""
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
        
        self.orderer_tls = f"--ordererTLSHostnameOverride orderer.example.com --tls --cafile {tn}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem"
        self.peers = f"--peerAddresses localhost:7051 --tlsRootCertFiles {tn}/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem --peerAddresses localhost:9051 --tlsRootCertFiles {tn}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
    
    def get_unbatched_records(self, limit=10):
        """Read records from PostgreSQL"""
        conn = psycopg2.connect(
            dbname="iot_data",
            user="ikramsmac",
            password="",
            host="/tmp"
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT id, temperature, humidity, gps_fix, data_hash 
            FROM sensor_readings 
            ORDER BY id DESC 
            LIMIT %s
        """, (limit,))
        records = cur.fetchall()
        cur.close()
        conn.close()
        return records
    
    def submit_batch(self, batch_id, records):
        """Submit batch to Fabric using storeBatchHash"""
        sensor_ids = [f"reading_{r[0]}" for r in records]
        hash_values = [r[4] for r in records]  # data_hash column
        
        ids_json = json.dumps(sensor_ids).replace('"', '\\"')
        hashes_json = json.dumps(hash_values).replace('"', '\\"')
        
        cmd = (
            f"peer chaincode invoke -o localhost:7050 {self.orderer_tls} "
            f"-C {self.channel} -n {self.chaincode} "
            f"-c '{{\\\"function\\\":\\\"storeBatchHash\\\",\\\"Args\\\":[\\\"{batch_id}\\\",\\\"{ids_json}\\\",\\\"{hashes_json}\\\"]}}' "
            f"{self.peers}"
        )
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=self.env)
        return result.returncode == 0, result.stdout, result.stderr

# Run it
if __name__ == "__main__":
    submitter = FabricBatchSubmitter()
    
    # Get last 5 records
    records = submitter.get_unbatched_records(5)
    print(f"Found {len(records)} records")
    
    # Submit batch
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    success, stdout, stderr = submitter.submit_batch(batch_id, records)
    
    if success:
        print(f"✅ Batch {batch_id} submitted successfully!")
        print("Output:", stdout[:200])
    else:
        print(f"❌ Failed to submit batch")
        print("Error:", stderr[:200])
