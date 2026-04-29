#!/usr/bin/env python3
"""
Batch Hash Generator - Fixed version
"""

import subprocess
import json
import os
import psycopg2
from datetime import datetime

def get_records(limit=5):
    """Read from PostgreSQL"""
    conn = psycopg2.connect(
        dbname="iot_data",
        user="ikramsmac",
        password="",
        host="/tmp"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT id, temperature, humidity, gps_fix, data_hash 
        FROM sensor_data 
        ORDER BY id DESC 
        LIMIT %s
    """, (limit,))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return records

def submit_to_fabric(batch_id, sensor_ids, hash_values):
    """Submit using CLI with proper JSON handling"""
    home = os.path.expanduser("~")
    fabric = f"{home}/fabric-samples"
    tn = f"{fabric}/test-network"
    
    env = os.environ.copy()
    env["PATH"] = f"{env.get('PATH', '')}:{fabric}/bin"
    env["FABRIC_CFG_PATH"] = f"{fabric}/config"
    env["CORE_PEER_TLS_ENABLED"] = "true"
    env["CORE_PEER_LOCALMSPID"] = "Org1MSP"
    env["CORE_PEER_ADDRESS"] = "localhost:7051"
    env["CORE_PEER_MSPCONFIGPATH"] = f"{tn}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
    env["CORE_PEER_TLS_ROOTCERT_FILE"] = f"{tn}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
    
    orderer_tls = f"--ordererTLSHostnameOverride orderer.example.com --tls --cafile {tn}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem"
    peers = f"--peerAddresses localhost:7051 --tlsRootCertFiles {tn}/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem --peerAddresses localhost:9051 --tlsRootCertFiles {tn}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
    
    # Create JSON arrays
    ids_json = json.dumps(sensor_ids)
    hashes_json = json.dumps(hash_values)
    
    # Build the chaincode argument
    arg = json.dumps({
        "function": "storeBatchHash",
        "Args": [batch_id, ids_json, hashes_json]
    })
    
    cmd = f'peer chaincode invoke -o localhost:7050 {orderer_tls} -C mychannel -n iot_hash -c \'{arg}\' {peers}'
    
    print(f"Running command...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    
    return result.returncode == 0, result.stdout, result.stderr

# Main
if __name__ == "__main__":
    records = get_records(3)
    print(f"Found {len(records)} records")
    
    sensor_ids = [f"reading_{r[0]}" for r in records]
    hash_values = [r[4] for r in records]
    
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Submitting batch: {batch_id}")
    print(f"Sensor IDs: {sensor_ids}")
    
    success, stdout, stderr = submit_to_fabric(batch_id, sensor_ids, hash_values)
    
    if success:
        print(f"✅ SUCCESS!")
        print(f"Output: {stdout[:300]}")
    else:
        print(f"❌ FAILED")
        print(f"Error: {stderr[:300]}")
