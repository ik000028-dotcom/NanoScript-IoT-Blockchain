import os
import json
import hashlib
import asyncio
from hfc.fabric import Client

# === CONFIGURE NETWORK PROFILE ===
NETWORK_JSON_PATH = '/Users/ikramsmac/Documents/PlatformIO/Projects/MKRZeroTest/network.json'

if not os.path.exists(NETWORK_JSON_PATH):
    raise Exception(f"Network profile not found: {NETWORK_JSON_PATH}")

# === INIT FABRIC CLIENT ===
cli = Client(net_profile=NETWORK_JSON_PATH)

# === ORG AND ADMIN INFO ===
ORG_NAME = 'Org1MSP'

# Load admin user from network.json
admin = cli.get_user(
    org_name=ORG_NAME,
    name='Admin'
)
if admin is None:
    raise Exception(f"Failed to get admin user for {ORG_NAME}")

# === CHANNEL ===
CHANNEL_NAME = 'mychannel'
channel = cli.new_channel(CHANNEL_NAME)

# === SAMPLE BATCH DATA ===
batch = [
    {"sensor_id": "temperature_4273", "type": "temperature", "value": 22.0},
    {"sensor_id": "humidity_4273", "type": "humidity", "value": 17.0},
    {"sensor_id": "gps_fix_4273", "type": "gps_fix", "value": False},
    # ... add more sensor readings here
]

# Compute hash for each item
for item in batch:
    item_string = f"{item['sensor_id']}{item['type']}{item['value']}"
    item['hash'] = hashlib.sha256(item_string.encode()).hexdigest()

print("Batch prepared for blockchain:")
print(json.dumps(batch, indent=2))

# === FUNCTION TO SEND BATCH TO FABRIC ===
async def send_to_fabric(batch_data):
    # Chaincode info — modify these as per your deployed chaincode
    CC_NAME = 'mycc'        # your chaincode name
    CC_VERSION = '1.0'      # your chaincode version
    CC_FUNCTION = 'addBatch' # your chaincode function name

    for record in batch_data:
        args = [json.dumps(record)]
        print(f"Sending record to Fabric: {record['sensor_id']}")
        # Async call to chaincode_invoke
        response = await cli.chaincode_invoke(
            requestor=admin,
            channel_name=CHANNEL_NAME,
            peer_names=['peer0.org1.example.com'],  # list of peers
            args=args,
            cc_name=CC_NAME,
            fcn=CC_FUNCTION,
            wait_for_event=True
        )
        print(f"Response: {response}")

# === MAIN ENTRY ===
if __name__ == '__main__':
    asyncio.run(send_to_fabric(batch))
    


