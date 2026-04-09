#!/bin/bash
# NanoScript IoT Blockchain - Full Test Suite
# Date: 2026-03-19
# Version: 1.0

echo "=========================================="
echo "NANOSCRIPT IOT BLOCKCHAIN TEST SUITE"
echo "=========================================="

# Setup environment
export PATH=$PATH:$HOME/fabric-samples/bin
export FABRIC_CFG_PATH=$HOME/fabric-samples/config
export CORE_PEER_TLS_ENABLED=true

# Org1 Environment
ORG1="export CORE_PEER_LOCALMSPID=\"Org1MSP\" && export CORE_PEER_ADDRESS=localhost:7051 && export CORE_PEER_MSPCONFIGPATH=$HOME/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp && export CORE_PEER_TLS_ROOTCERT_FILE=$HOME/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"

# Org2 Environment  
ORG2="export CORE_PEER_LOCALMSPID=\"Org2MSP\" && export CORE_PEER_ADDRESS=localhost:9051 && export CORE_PEER_MSPCONFIGPATH=$HOME/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp && export CORE_PEER_TLS_ROOTCERT_FILE=$HOME/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"

# Orderer TLS
ORDERER_TLS="--ordererTLSHostnameOverride orderer.example.com --tls --cafile $HOME/fabric-samples/test-network/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem"

# Peer endpoints
PEERS="--peerAddresses localhost:7051 --tlsRootCertFiles $HOME/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem --peerAddresses localhost:9051 --tlsRootCertFiles $HOME/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/tlsca/tlsca.org2.example.com-cert.pem"

echo ""
echo "TEST 1: Basic Store"
eval "$ORG1 && peer chaincode invoke -o localhost:7050 $ORDERER_TLS -C mychannel -n iot_hash -c '{\"function\":\"storeHash\",\"Args\":[\"test_sensor\",\"test_hash\"]}' $PEERS"

echo ""
echo "TEST 2: Basic Query"
eval "$ORG1 && peer chaincode query -C mychannel -n iot_hash -c '{\"function\":\"queryHash\",\"Args\":[\"test_sensor\"]}'"

echo ""
echo "TEST 3: Batch Store"
eval "$ORG1 && peer chaincode invoke -o localhost:7050 $ORDERER_TLS -C mychannel -n iot_hash -c '{\"function\":\"storeBatchHash\",\"Args\":[\"batch_test\",\"[\\\"s1\\\",\\\"s2\\\"]\",\"[\\\"h1\\\",\\\"h2\\\"]\"]}' $PEERS"

echo ""
echo "TEST 4: History Store"
eval "$ORG1 && peer chaincode invoke -o localhost:7050 $ORDERER_TLS -C mychannel -n iot_hash -c '{\"function\":\"storeHashWithHistory\",\"Args\":[\"hist_sensor\",\"hash_v1\"]}' $PEERS"

sleep 2

echo ""
echo "TEST 5: History Second Version"
eval "$ORG1 && peer chaincode invoke -o localhost:7050 $ORDERER_TLS -C mychannel -n iot_hash -c '{\"function\":\"storeHashWithHistory\",\"Args\":[\"hist_sensor\",\"hash_v2\"]}' $PEERS"

echo ""
echo "TEST 6: Get History"
eval "$ORG1 && peer chaincode query -C mychannel -n iot_hash -c '{\"function\":\"getHistory\",\"Args\":[\"hist_sensor\"]}'"

echo ""
echo "TEST 7: Verify Integrity"
eval "$ORG1 && peer chaincode query -C mychannel -n iot_hash -c '{\"function\":\"verifyIntegrity\",\"Args\":[\"hist_sensor\",\"hash_v1\"]}'"

echo ""
echo "TEST 8: Private Store"
eval "$ORG1 && peer chaincode invoke -o localhost:7050 $ORDERER_TLS -C mychannel -n iot_hash -c '{\"function\":\"storeHashPrivate\",\"Args\":[\"private_test\",\"secret\",\"[\\\"Org1MSP\\\",\\\"Org2MSP\\\"]\"]}' $PEERS"

echo ""
echo "TEST 9: Query Private as Org1"
eval "$ORG1 && peer chaincode query -C mychannel -n iot_hash -c '{\"function\":\"queryHashPrivate\",\"Args\":[\"private_test\"]}'"

echo ""
echo "TEST 10: Query Private as Org2"
eval "$ORG2 && peer chaincode query -C mychannel -n iot_hash -c '{\"function\":\"queryHashPrivate\",\"Args\":[\"private_test\"]}'"

echo ""
echo "=========================================="
echo "TEST SUITE COMPLETE"
echo "=========================================="