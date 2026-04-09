#!/bin/bash
# Org1 Environment Variables
# NanoScript IoT Blockchain
# Loaded: Org1MSP (peer0.org1.example.com:7051)

export PATH=$PATH:$HOME/fabric-samples/bin
export FABRIC_CFG_PATH=$HOME/fabric-samples/config
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_ADDRESS=localhost:7051
export CORE_PEER_MSPCONFIGPATH=$HOME/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_TLS_ROOTCERT_FILE=$HOME/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo "=========================================="
echo "Org1 Environment Loaded"
echo "MSP ID: Org1MSP"
echo "Peer: localhost:7051"
echo "=========================================="