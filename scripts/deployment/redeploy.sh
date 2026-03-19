#!/bin/bash
# Redeployment Script for IoT Hash Chaincode
# Usage: ./redeploy.sh

CHAINCODE_PATH=~/fabric-samples/iot-hash-chaincode
NETWORK_PATH=~/fabric-samples/test-network

echo "=========================================="
echo "REDEPLOYING IOT HASH CHAINCODE"
echo "=========================================="

cd $NETWORK_PATH

echo ""
echo "Step 1: Bringing down network..."
./network.sh down

echo ""
echo "Step 2: Cleaning Docker volumes..."
docker volume prune -f

echo ""
echo "Step 3: Starting network with CA..."
./network.sh up createChannel -c mychannel -ca

echo ""
echo "Step 4: Deploying chaincode..."
./network.sh deployCC -ccn iot_hash -ccp ../iot-hash-chaincode -ccl javascript

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo ""
echo "Next steps:"
echo "1. source ~/NanoScript-IoT-Blockchain/env/org1/env.sh"
echo "2. ~/NanoScript-IoT-Blockchain/scripts/testing/full-test-suite.sh"
echo "=========================================="