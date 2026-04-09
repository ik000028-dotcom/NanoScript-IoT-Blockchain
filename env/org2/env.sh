#!/bin/bash
# Org2 Environment Variables
# NanoScript IoT Blockchain
# Loaded: Org2MSP (peer0.org2.example.com:9051)

export PATH=$PATH:$HOME/fabric-samples/bin
export FABRIC_CFG_PATH=$HOME/fabric-samples/config
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_ADDRESS=localhost:9051
export CORE_PEER_MSPCONFIGPATH=$HOME/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_TLS_ROOTCERT_FILE=$HOME/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

echo "=========================================="
echo "Org2 Environment Loaded"
echo "MSP ID: Org2MSP"
echo "Peer: localhost:9051"
echo "=========================================="