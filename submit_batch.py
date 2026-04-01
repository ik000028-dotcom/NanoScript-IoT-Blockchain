import json
from hfc.fabric import Client as FabricClient

# Initialize client
cli = FabricClient(net_profile="network.json")  # your Fabric network profile

# Get channel
channel = cli.get_channel('mychannel')  # replace with your channel name

# User and organization
org1_admin = cli.get_user('Org1', 'Admin')  # change if needed

# Load batch from file (or you can directly use the batch from previous script)
with open("batch.json") as f:
    batch = json.load(f)

# Submit each record as a transaction
for record in batch:
    args = [record["sensor_id"], record["type"], str(record["value"]), record["hash"]]
    response = cli.chaincode_invoke(
        requestor=org1_admin,
        channel_name='mychannel',
        peers=['peer0.org1.example.com'],
        args=args,
        cc_name='sensorcc',   # your chaincode name
        fcn='addSensorData',  # function in your chaincode
        wait_for_event=True
    )
    print(f"Submitted {record['sensor_id']}, tx_id: {response['txid']}")
    

# At the end of batch_hash_generator.py, add:
with open("batch.json", "w") as f:
    json.dump(batch, f, indent=2)
    

