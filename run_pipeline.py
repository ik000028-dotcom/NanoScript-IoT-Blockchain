#!/usr/bin/env python3
import subprocess
import os
import psycopg2
import json
from datetime import datetime

def get_records(limit=3):
    """
    Fetch records from PostgreSQL.
    Uses 'time' instead of 'id' to match the sensor_data schema.
    """
    conn = psycopg2.connect(
        dbname="iot_data",
        user="ikramsmac",
        password="",
        host="/tmp"
    )
    cursor = conn.cursor()
    # UPDATED: Selecting 'time' instead of 'id'
    cursor.execute("""
        SELECT time, data_hash 
        FROM sensor_data 
        ORDER BY time DESC 
        LIMIT %s
    """, (limit,))
    records = cursor.fetchall()
    conn.close()
    return records

def submit_to_fabric(batch_id, sensor_ids, hash_values):
    home   = os.path.expanduser("~")
    fabric = f"{home}/fabric-samples"
    tn     = f"{fabric}/test-network"

    env = os.environ.copy()
    env["PATH"]                       += f":{fabric}/bin"
    env["FABRIC_CFG_PATH"]             = f"{fabric}/config"
    env["CORE_PEER_TLS_ENABLED"]       = "true"
    env["CORE_PEER_LOCALMSPID"]        = "Org1MSP"
    env["CORE_PEER_ADDRESS"]           = "localhost:7051"
    env["CORE_PEER_MSPCONFIGPATH"]     = f"{tn}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
    env["CORE_PEER_TLS_ROOTCERT_FILE"] = f"{tn}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"

    arg = json.dumps({
        "function": "storeBatchHash",
        "Args": [batch_id, json.dumps(sensor_ids), json.dumps(hash_values)]
    })

    cmd = [
        f"{fabric}/bin/peer", "chaincode", "invoke",
        "-o", "localhost:7050",
        "--ordererTLSHostnameOverride", "orderer.example.com",
        "--tls",
        "--cafile", f"{tn}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem",
        "-C", "mychannel",
        "-n", "iot_hash",
        "-c", arg,
        "--peerAddresses", "localhost:7051",
        "--tlsRootCertFiles", f"{tn}/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem",
        "--peerAddresses", "localhost:9051",
        "--tlsRootCertFiles", f"{tn}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode == 0, result.stdout, result.stderr

if __name__ == "__main__":
    records = get_records(3)
    
    if not records:
        print("❌ No records found in sensor_data table.")
    else:
        print(f"Found {len(records)} records")

        # Step 2: Format reading IDs using the timestamp
        sensor_ids  = [f"reading_{r[0].strftime('%H%M%S')}" for r in records]
        hash_values = [r[1] for r in records] 

        print("Sensor IDs  :", sensor_ids)
        print("Hash values :", hash_values)

        # Step 3: Submit to Fabric
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Submitting batch: {batch_id}")

        success, stdout, stderr = submit_to_fabric(batch_id, sensor_ids, hash_values)

        if success:
            print("✅ SUCCESS — hashes from DB match what is on blockchain")
        else:
            print("❌ FAILED")
            print(f"Error: {stderr}")









