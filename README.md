# NanoScript IoT Blockchain System

This document provides a step-by-step installation and configuration guide for a testing environment implementing an IoT data integrity system based on a permissioned blockchain network, integrated with a RAG pipeline and LLM for intelligent data querying.


> This repository provides a complete installation and configuration guide for a testing environment implementing an IoT monitoring system based on a permissioned blockchain network, integrated with a Retrieval-Augmented Generation (RAG) pipeline and a local Large Language Model for intelligent data querying. The system captures real-time environmental data (temperature, humidity, GPS) from an Arduino MKR Zero, validates and hashes every record through a FastAPI backend, anchors cryptographic proofs on a Hyperledger Fabric blockchain requiring dual-organisation endorsement, and exposes all verified data through a natural language chatbot interface powered by LangChain and llama3.2.

---

## Project Overview

This system was built to solve a fundamental problem in IoT deployments: **raw sensor data cannot be trusted by default**. A database administrator, a software bug, or a malicious insider can modify historical readings without leaving any trace. This project addresses that problem by combining three technologies:

- **Arduino MKR Zero + DHT11 + GPS** — physical sensing layer collecting temperature, humidity, and location data
- **Hyperledger Fabric Blockchain** — permissioned ledger that anchors a SHA-256 hash of every sensor record, requiring endorsement from two independent organisations before any data is written
- **RAG Pipeline (LangChain + ChromaDB + llama3.2)** — AI layer that makes blockchain-verified data queryable through natural language

Any tampering with a stored record produces a hash mismatch detectable by the `verifyIntegrity` chaincode function, providing a cryptographic guarantee of data integrity from sensor to storage.


Any tampering with a stored record produces a hash mismatch detectable by the `verifyIntegrity` chaincode function, providing a cryptographic guarantee of data integrity from sensor to storage.


## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Hardware Requirements](#hardware-requirements)
4. [Software Stack](#software-stack)
5. [Installation Guide](#installation-guide)
6. [Layer-by-Layer Validation](#layer-by-layer-validation)
7. [API Documentation](#api-documentation)
8. [Blockchain Integration](#blockchain-integration)
9. [Troubleshooting](#troubleshooting)
10. [Project Configuration](#project-configuration)
11. [API Testing](#api-testing)


---

## System Architecture
![System Architecture Diagram](./assets/arch.png)

---

## Hardware Requirements

### Required Components

| Component | Model | Purpose | Connection |
|-----------|-------|---------|------------|
| Microcontroller | Arduino MKR Zero | Main processing unit | USB to PC |
| Temperature/Humidity | DHT11 | Environmental sensing | Pin A1 |
| GPS Module | MKR GPS Shield | Location tracking | UART (Pins 13/14) |
| USB Cable | Micro-USB | Power + Data | USB port |

### Pin Connections

**DHT11 Sensor:**
- VCC → VCC (3.3V)
- GND → GND
- DATA → A1

**GPS Shield:**
- VCC → VCC
- GND → GND
- TX → RX1 (Pin 14)
- RX → TX1 (Pin 13)


---

## Software Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| L1 | Arduino C++ | - | Sensor reading |
| L2 | Python 3.10 | 3.10.x | Gateway script |
| L3 | FastAPI | 0.110.x | REST API |
| L3 | Pydantic | 2.6.x | Data validation |
| L4 | PostgreSQL | 17.x | Relational DB |
| L4 | TimescaleDB | 2.26.x | Time-series |
| L5 | Python | 3.10.x | Batch processing |
| L6 | Hyperledger Fabric | 2.5.15 | Blockchain |
| L6 | Go (Chaincode) | 1.21.x | Smart contracts |
| L7 | Docker | Latest | Containerization |
| L8-11 | LangChain | Latest | RAG pipeline |
| L8-11 | OpenAI | GPT-3.5 | LLM processing |


---

## Installation Guide

### Prerequisites

```bash
brew install postgresql@17
brew install timescaledb
brew install docker
brew install git

python3.10 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn psycopg2-binary pydantic

⛓️ Hyperledger Fabric Installation Guide
This guide details the step-by-step process for installing a permissioned blockchain environment to support the NanoScript-IoT-Blockchain framework.

1. System Prerequisites
Hyperledger Fabric requires several underlying technologies. Run the following commands to ensure your environment is ready:

Docker & Docker Compose: To host the blockchain nodes (Peers, Orderers, CAs).

Node.js (v18.x): Required for the JavaScript chaincode execution.

Python (3.10+): Required for the FastAPI backend and RAG gateway.

Bash
# For macOS (Using Homebrew)
brew install git curl node@18 python@3.10 docker docker-compose
2. Install Fabric Binaries and Docker Images
This project is optimized for Hyperledger Fabric v2.5.4 (LTS). Execute the official bootstrap script to download the Fabric samples, the required binaries (peer, orderer, configtxgen), and the official Docker images:

Bash
# Downloads binaries and Docker images for version 2.5.4
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.4 1.5.7
3. Environment Configuration
Add the downloaded binaries to your system's PATH and define the configuration path so the system can locate the peer CLI:

Bash
# Add these lines to your ~/.zshrc or ~/.bashrc
export PATH=$PWD/bin:$PATH
export FABRIC_CFG_PATH=$PWD/config/
4. Smart Contract (Chaincode) Dependencies
Since the project uses Node.js for the Smart Contract (iot_hash.js), you must install the Fabric Contract SDK dependencies before deployment:

Bash
cd chaincode/src
npm install⛓️ Hyperledger Fabric Installation Guide
This guide details the step-by-step process for installing a permissioned blockchain environment to support the NanoScript-IoT-Blockchain framework.

1. System Prerequisites
Hyperledger Fabric requires several underlying technologies. Run the following commands to ensure your environment is ready:

Docker & Docker Compose: To host the blockchain nodes (Peers, Orderers, CAs).

Node.js (v18.x): Required for the JavaScript chaincode execution.

Python (3.10+): Required for the FastAPI backend and RAG gateway.

Bash
# For macOS (Using Homebrew)
brew install git curl node@18 python@3.10 docker docker-compose
2. Install Fabric Binaries and Docker Images
This project is optimized for Hyperledger Fabric v2.5.4 (LTS). Execute the official bootstrap script to download the Fabric samples, the required binaries (peer, orderer, configtxgen), and the official Docker images:

Bash
# Downloads binaries and Docker images for version 2.5.4
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.4 1.5.7
3. Environment Configuration
Add the downloaded binaries to your system's PATH and define the configuration path so the system can locate the peer CLI:

Bash
# Add these lines to your ~/.zshrc or ~/.bashrc
export PATH=$PWD/bin:$PATH
export FABRIC_CFG_PATH=$PWD/config/
4. Smart Contract (Chaincode) Dependencies
Since the project uses Node.js for the Smart Contract (iot_hash.js), you must install the Fabric Contract SDK dependencies before deployment:

Bash
cd chaincode/src
npm install
cd ../..
cd ../..

---
```

## Layer-by-Layer Validation

This section provides a step-by-step validation process for each layer of the system. It ensures that every component works correctly in isolation before running the full pipeline.

---

## L1 — IoT Device Validation (Arduino + Sensors)

### Objective
Verify that the Arduino correctly reads sensor data and outputs valid JSON.

### Steps
1. Connect the Arduino via USB  
2. Open Arduino Serial Monitor  
3. Set baud rate to 9600  

### Expected Output
```json
{"type":"temperature","value":24.5}
{"type":"humidity","value":60}
{"type":"gps","gps_fix":false,"lat":null,"lon":null}
Validation Checks
Data updates every ~2 seconds
No malformed JSON
GPS:
gps_fix: false indoors
gps_fix: true outdoors
L2 — Gateway Validation (gateway.py)
Objective

Ensure data is correctly sent from serial to FastAPI backend.

Steps
python gateway.py
Expected Behavior
JSON printed in console
HTTP POST sent to backend
Retry works if backend is down
L3 — FastAPI Backend Validation
Objective

Confirm API receives data and hashes it correctly.

Steps
uvicorn main:app --reload

Test:

curl -X POST http://localhost:8000/data \
-H "Content-Type: application/json" \
-d '{"type":"temperature","value":25}'
Expected
200 OK response
Data stored with SHA-256 hash
L4 — Database Validation (PostgreSQL + TimescaleDB)
Objective

Verify data storage.

Query
SELECT * FROM sensor_data ORDER BY time DESC LIMIT 5;
Expected
Timestamp
Sensor values
Hash
blockchain_tx = NULL
L5 — Batch Generator Validation
Objective

Ensure unconfirmed records are retrieved.

Test
curl http://localhost:8000/batch/unconfirmed
Expected
[
  {
    "id": 123,
    "hash": "abc123...",
    "recomputed": false
  }
]
L6 — Chaincode Validation (Hyperledger Fabric)
Objective

Verify blockchain logic.

Steps
peer chaincode invoke ...
peer chaincode query ...
Expected
Endorsed by Org1 and Org2
Hash stored successfully
L7 — Blockchain Ledger Validation
Objective

Ensure immutability.

Test
peer chaincode query -C mychannel -n iot -c '{"Args":["queryHash","abc123"]}'
Expected
Valid transaction
Same result across peers
L8 — Vector Database Validation (ChromaDB)
Objective

Verify embeddings.

Expected
~1000 documents
Each contains sensor + hash
L9 — LangChain Validation
Test Query

"What is the weather like?"

Expected
Relevant sensor data retrieved
L10 — LLM Validation (Ollama)
Test
ollama run llama3.2
Expected
Grounded answers
No hallucination
L11 — Streamlit Interface Validation
Run
streamlit run app.py
Expected
Chat interface loads
Answers + raw data visible
Final Validation

If all layers pass:

Data flows end-to-end
Blockchain verification works
AI responses are accurate

```

## API Documentation

This section documents all HTTP endpoints exposed by the FastAPI backend (`main.py`), running on `http://localhost:8000`.

---

### Base URL

```
http://localhost:8000
```

---

### Endpoints

---

#### `POST /data`

Receives a sensor reading from the gateway, validates it, computes a SHA-256 hash, and stores it in PostgreSQL.

**Request Headers**

| Header         | Value              |
|----------------|--------------------|
| Content-Type   | application/json   |

**Request Body**

For a temperature reading:
```json
{
  "type": "temperature",
  "value": 24.5
}
```

For a humidity reading:
```json
{
  "type": "humidity",
  "value": 60
}
```

For a GPS reading (indoors):
```json
{
  "type": "gps",
  "gps_fix": false,
  "lat": null,
  "lon": null
}
```

For a GPS reading (outdoors):
```json
{
  "type": "gps",
  "gps_fix": true,
  "lat": 51.5074,
  "lon": -0.1278
}
```

**Response**

```json
{
  "status": "ok",
  "hash": "e3b0c44298fc1c149afb..."
}
```

| Field    | Type   | Description                              |
|----------|--------|------------------------------------------|
| `status` | string | `"ok"` on successful storage            |
| `hash`   | string | SHA-256 hash of the stored payload       |

**Example cURL**

```bash
curl -X POST http://localhost:8000/data \
  -H "Content-Type: application/json" \
  -d '{"type":"temperature","value":25}'
```

**Expected Result**
- `200 OK` response
- Data stored in PostgreSQL with SHA-256 hash
- `blockchain_tx` field set to `NULL` (pending blockchain confirmation)

---

#### `GET /batch/unconfirmed`

Returns all sensor records that have not yet been submitted to the Hyperledger Fabric blockchain (i.e. where `blockchain_tx IS NULL`). Used by the Batch Hash Generator (L5) to prepare records for blockchain submission.

**Request**

No body or parameters required.

```bash
curl http://localhost:8000/batch/unconfirmed
```

**Response**

```json
[
  {
    "id": 1,
    "timestamp": "2025-04-22T13:00:01.123Z",
    "type": "temperature",
    "value": 24.5,
    "hash": "e3b0c44298fc1c149afb...",
    "recomputed": false,
    "blockchain_tx": null
  },
  {
    "id": 2,
    "timestamp": "2025-04-22T13:00:03.456Z",
    "type": "humidity",
    "value": 60,
    "hash": "a87ff679a2f3e71d9181...",
    "recomputed": false,
    "blockchain_tx": null
  }
]
```

| Field           | Type    | Description                                                  |
|-----------------|---------|--------------------------------------------------------------|
| `id`            | integer | Auto-incremented record ID                                   |
| `timestamp`     | string  | ISO 8601 timestamp of the reading                            |
| `type`          | string  | Sensor type: `temperature`, `humidity`, or `gps`            |
| `value`         | float   | Sensor reading value                                         |
| `hash`          | string  | SHA-256 hash computed at ingestion time (L3)                |
| `recomputed`    | boolean | `false` = hash came from L3, not recomputed later           |
| `blockchain_tx` | null    | `null` until the record is confirmed on the blockchain       |

---

### Error Responses

| HTTP Code | Meaning                                      |
|-----------|----------------------------------------------|
| `200 OK`  | Request successful                           |
| `422 Unprocessable Entity` | Payload failed Pydantic validation |
| `500 Internal Server Error` | Database or hashing failure       |

---

### Notes

- All hashes are computed using **SHA-256** at ingestion time and are never recomputed after storage.
- The `blockchain_tx` field is populated once the hash is anchored on **Hyperledger Fabric** (L6–L7).
- The FastAPI backend uses **Pydantic** for strict payload validation — malformed or missing fields will return a `422` error.


## Blockchain Integration

This section explains how the Hyperledger Fabric blockchain is integrated into the system and how to start, interact with, and verify the blockchain network — including on a new machine such as a supervisor's PC.

---

### Overview

The blockchain layer (L6–L7) anchors the SHA-256 hashes of all sensor readings onto an immutable ledger. Even if the PostgreSQL database is fully compromised and all records are altered, the hashes on the blockchain remain unchanged — making any tampering immediately detectable.

The network consists of:

| Component | Details |
|-----------|---------|
| Fabric version | Hyperledger Fabric v2.5.15 |
| Chaincode | `iot_hash.js` (Node.js) |
| Channel | `mychannel` |
| Org1 Peer | `peer0.org1.example.com` — port `7051` |
| Org2 Peer | `peer0.org2.example.com` — port `9051` |
| Endorsement policy | Both Org1 AND Org2 must sign every transaction |

---

### Prerequisites (Supervisor PC Setup)

Before running the blockchain, ensure the following are installed:

**1. Docker and Docker Compose**
```bash
docker --version        # Docker 20.x or higher
docker compose version  # v2.x or higher
```

If not installed:
```bash
# macOS
brew install docker

# Ubuntu/Debian
sudo apt-get install docker.io docker-compose-v2
```

**2. Node.js (v18 or higher)**
```bash
node --version   # should be v18+
npm --version
```

**3. Hyperledger Fabric Binaries and Docker Images**
```bash
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.15 1.5.9
```

This downloads the `fabric-samples` binaries (`peer`, `orderer`, `configtxgen`, etc.) and all required Docker images.

**4. Add Fabric binaries to PATH**
```bash
export PATH=$PATH:$(pwd)/fabric-samples/bin
export FABRIC_CFG_PATH=$(pwd)/fabric-samples/config/
```

> Add these lines to your `~/.bashrc` or `~/.zshrc` to make them permanent.

---

### Starting the Blockchain Network

From the root of the project:

**Step 1 — Start the Fabric test network**
```bash
cd fabric-samples/test-network
./network.sh up createChannel -c mychannel -ca
```

Expected output:
```
Creating channel 'mychannel'...
Channel 'mychannel' joined
```

**Step 2 — Deploy the chaincode**
```bash
./network.sh deployCC -ccn iot_hash -ccp ../../chaincode -ccl node
```

Expected output:
```
Chaincode definition committed on channel 'mychannel'
```

> Both Org1 and Org2 must approve the chaincode before it is committed — this is enforced automatically by the script and reflects the endorsement policy.

---

### Chaincode Functions

The chaincode (`iot_hash.js`) exposes four functions:

#### `storeHashWithHistory`
Stores a sensor hash on the ledger with a full history trail.

```bash
peer chaincode invoke \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem" \
  -C mychannel -n iot_hash \
  --peerAddresses localhost:7051 \
  --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt" \
  --peerAddresses localhost:9051 \
  --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt" \
  -c '{"function":"storeHashWithHistory","Args":["sensor_001","e3b0c44298fc1c149afb...","2025-04-22T13:00:01Z"]}'
```

Expected output:
```
[chaincodeCmd] chaincodeInvokeOrQuery -> INFO Chaincode invoke successful. result: status:200
```

---

#### `queryHash`
Retrieves the stored hash for a given sensor ID.

```bash
peer chaincode query \
  -C mychannel -n iot_hash \
  -c '{"function":"queryHash","Args":["sensor_001"]}'
```

Expected output:
```json
{
  "sensorId": "sensor_001",
  "hash": "e3b0c44298fc1c149afb...",
  "timestamp": "2025-04-22T13:00:01Z"
}
```

---

#### `getHistory`
Returns the full submission history for a sensor ID — every hash ever stored for that sensor.

```bash
peer chaincode query \
  -C mychannel -n iot_hash \
  -c '{"function":"getHistory","Args":["sensor_001"]}'
```

---

#### `verifyIntegrity`
Checks whether a given hash matches any historical record for a sensor. Returns `true` if the data is intact, `false` if tampering is detected.

```bash
peer chaincode query \
  -C mychannel -n iot_hash \
  -c '{"function":"verifyIntegrity","Args":["sensor_001","e3b0c44298fc1c149afb..."]}'
```

Expected output:
```
true
```

---

### Verifying the Ledger Status

To confirm both peers have committed the same blocks:

```bash
# Check Org1 peer
peer channel getinfo -c mychannel --peerAddress localhost:7051 \
  --tlsRootCertFiles organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

# Check Org2 peer
peer channel getinfo -c mychannel --peerAddress localhost:9051 \
  --tlsRootCertFiles organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
```

Both peers should report the same block height — confirming the ledger is in sync.

---

### Stopping the Network

```bash
./network.sh down
```

This stops all Docker containers and removes the channel artifacts. The ledger data is not persisted after this command unless an external volume is configured.

---

### How Integrity Works End-to-End

```
Arduino → FastAPI (SHA-256 computed) → PostgreSQL (hash stored)
                                              ↓
                                   Batch Generator reads unconfirmed hashes
                                              ↓
                              Hyperledger Fabric (both Org1 + Org2 endorse)
                                              ↓
                                   blockchain_tx field updated in PostgreSQL
                                              ↓
                              verifyIntegrity() → true (data untampered)
```

If any record in PostgreSQL is modified after blockchain submission, `verifyIntegrity()` will return `false` — proving tampering occurred.


## Troubleshooting

This section documents real errors encountered during system verification and their exact fixes.

---

### Gateway fails to start — Serial port not found

**Error:**
```
SerialException: could not open port /dev/tty.usbmodem101: No such file or directory
```

**Cause:** The Arduino's USB port enumerated with a different name (`usbmodem1101` instead 
of `usbmodem101`).

**Fix:**
```bash
# First confirm the actual port name
ls -la /dev/tty.usbmodem*

# Then update gateway.py automatically
sed -i '' 's/tty.usbmodem101/tty.usbmodem1101/g' \
  ~/Documents/PlatformIO/Projects/MKRZeroTest/gateway.py && echo "✅ Port updated"
```

---

### Blockchain peer refuses connection

**Error:**
```
connection error: desc = "transport: error while dialing: dial tcp [::1]:7051: connect: connection refused"
```

**Cause:** The Hyperledger Fabric Docker containers are not running.

**Fix:**
```bash
cd ~/fabric-samples/test-network
./network.sh up
```

Then re-source the org environment and retry:
```bash
source ~/NanoScript-IoT-Blockchain/env/org1/env.sh
peer chaincode query -C mychannel -n iot_hash \
  -c '{"function":"getAllSensors","Args":["","","10"]}'
```

---

### Gateway shows "Failed to send" errors

**Cause:** FastAPI backend is not yet running. The gateway starts before FastAPI and 
cannot reach `http://localhost:8000/data`.

**Fix:** This is expected behavior. Start FastAPI (Step 3) and the errors will stop 
automatically. The gateway retries every reading — no data is lost.

---

### Streamlit shows `ModuleNotFoundError: No module named 'torchvision'`

**Error:**
```
ModuleNotFoundError: No module named 'torchvision'
```

**Cause:** A `transformers` library sub-module tries to import `torchvision`, which is 
not installed. This does not affect any functionality used by this project.

**Fix:** This is a harmless warning — not an error. Confirm Streamlit started correctly:
```bash
curl -s http://localhost:8501 | head -5
```

If HTML is returned, the app is running. Open `http://localhost:8501` in your browser normally.

---

### GPS always shows `gps_fix: false`

**Cause:** The Arduino GPS shield requires a clear view of the sky to acquire a satellite 
fix. Indoors, walls block the signal and no fix is possible.

**Fix:** Take the Arduino outside and wait 1–2 minutes. Once a fix is acquired, the 
output will change from:
```json
{"type":"gps","gps_fix":false,"lat":null,"lon":null}
```
to:
```json
{"type":"gps","gps_fix":true,"lat":51.5074,"lon":-0.1278}
```

> All four services (Fabric, Gateway, FastAPI, Streamlit) must be running before going 
> outdoors so that GPS coordinates are stored automatically when the fix is acquired.

---

### PostgreSQL connection refused

**Cause:** The PostgreSQL service is not running.

**Fix (macOS):**
```bash
brew services start postgresql
# or
pg_ctl -D /usr/local/var/postgres start
```

Verify the database is reachable:
```bash
psql -U ikramsmac -d iot_data -c "SELECT 1;"
```

---

### ChromaDB collection not found

**Error:**
```
ValueError: Collection 'sensor_logs' does not exist
```

**Cause:** The ChromaDB persistent directory is missing or the ingestion script has 
not been run yet.

**Fix:** Re-run the ingestion script to populate the vector database:
```bash
cd ~/Documents/PlatformIO/Projects/MKRZeroTest
source venv/bin/activate
python ingest.py
```

Verify after ingestion:
```bash
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
col = client.get_collection('sensor_logs')
print(f'Total documents: {col.count()}')
"
```

Expected: `Total documents: 1000`

---

### verifyIntegrity returns false

**Cause:** The hash stored in PostgreSQL no longer matches the hash anchored on the 
blockchain — this indicates the database record was modified after blockchain submission.

**Diagnosis:**
```bash
# Query the blockchain hash
peer chaincode query -C mychannel -n iot_hash \
  -c '{"function":"queryHash","Args":["sensor001"]}'

# Compare with the PostgreSQL hash
psql -U ikramsmac -d iot_data \
  -c "SELECT hash FROM sensor_data WHERE id = 1;"
```

If the two hashes differ, the PostgreSQL record has been altered. The blockchain hash 
is the authoritative source of truth.


## Project Configuration

This section describes the exact sequence of steps to start the full system from scratch. 
Every command must be run in the order shown below. Each step requires its own terminal 
window — do not close any terminal once a service is running.

---

### Prerequisites Check

Before starting, confirm the Arduino is connected:

```bash
ls -la /dev/tty.usbmodem* 2>/dev/null && echo "✅ Arduino CONNECTED" || echo "❌ Arduino NOT connected"
```

Expected output:
```
crw-rw-rw-  1 root  wheel  0x9000004 Apr 22 01:32 /dev/tty.usbmodem1101
✅ Arduino CONNECTED
```

> If the port shown is `/dev/tty.usbmodem1101`, make sure `gateway.py` uses that exact value.
> If it was previously set to `/dev/tty.usbmodem101`, fix it with:
> ```bash
> sed -i '' 's/tty.usbmodem101/tty.usbmodem1101/g' \
>   ~/Documents/PlatformIO/Projects/MKRZeroTest/gateway.py
> ```

---

### Step 1 — Start the Hyperledger Fabric Network (Terminal 1)

```bash
cd ~/fabric-samples/test-network
./network.sh up
```

Wait until you see all containers running, then verify the chaincode is reachable:

```bash
source ~/NanoScript-IoT-Blockchain/env/org1/env.sh
peer chaincode query -C mychannel -n iot_hash \
  -c '{"function":"getAllSensors","Args":["","","10"]}'
```

Expected: a JSON response containing `sensorID`, `hashValue`, and `transactionID`.

---

### Step 2 — Start the Python Gateway (Terminal 2)

```bash
cd ~/Documents/PlatformIO/Projects/MKRZeroTest
source venv/bin/activate
python gateway.py
```

Expected output (continuous stream):
```
{"type":"temperature","value":24.5} → sent
{"type":"humidity","value":60} → sent
{"type":"gps","gps_fix":false,"lat":null,"lon":null} → sent
```

> Keep this terminal open. The gateway reads from the Arduino every ~2 seconds and forwards 
> each reading to FastAPI. If FastAPI is not yet running, you will see "Failed to send" — 
> this is normal and the gateway will retry automatically.

---

### Step 3 — Start the FastAPI Backend (Terminal 3)

```bash
cd ~/Documents/PlatformIO/Projects/MKRZeroTest
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected output once ready:
```
Application startup complete.
INFO: 127.0.0.1 - "POST /data HTTP/1.1" 200 OK
INFO: 127.0.0.1 - "POST /data HTTP/1.1" 200 OK
```

A continuous stream of `200 OK` responses confirms that sensor data is being validated, 
hashed, and stored in PostgreSQL in real time.

---

### Step 4 — Verify the Database (Optional Spot Check)

In any terminal with the venv active:

```bash
psql -U ikramsmac -d iot_data -c \
  "SELECT COUNT(*) as total_records, MAX(time) as latest_record FROM sensor_data;"
```

Expected output:
```
 total_records |         latest_record
---------------+-------------------------------
         14101 | 2026-04-22 01:37:32.585723-07
(1 row)
```

---

### Step 5 — Start the Streamlit Chatbot (Terminal 4)

```bash
cd ~/Documents/PlatformIO/Projects/MKRZeroTest
source venv/bin/activate
streamlit run app.py
```

Once started, open your browser at:
```
http://localhost:8501
```

The chatbot sidebar will show the live document count from ChromaDB (1,000 documents) 
and the verified record count from the blockchain.

---

### Step 6 — GPS Outdoor Test (Optional)

Once all four services are running (Fabric, Gateway, FastAPI, Streamlit), take the 
Arduino MKR Zero outside. The GPS shield will acquire a satellite fix within 1–2 minutes. 
Once fixed, the gateway will automatically forward real coordinates:

```json
{"type":"gps","gps_fix":true,"lat":51.5074,"lon":-0.1278}
```

No extra steps are needed — the coordinates will be stored and hashed in real time. 
You can verify in the Streamlit chatbot by asking:
> *"Show me the GPS status of the latest readings"*

---

### System Startup Summary

| Order | Service | Command | Terminal |
|-------|---------|---------|----------|
| 1 | Hyperledger Fabric | `./network.sh up` | Terminal 1 |
| 2 | Python Gateway | `python gateway.py` | Terminal 2 |
| 3 | FastAPI Backend | `uvicorn main:app --reload` | Terminal 3 |
| 4 | Streamlit Chatbot | `streamlit run app.py` | Terminal 4 |


## API Testing

This section demonstrates the full functionality of the system end-to-end, using real 
outputs captured during live system verification. All tests assume the system is fully 
running as described in the [Project Configuration](#project-configuration) section.

---

### Test 1 — Send a Sensor Reading to FastAPI

Simulates what the gateway does every 2 seconds. Sends a temperature reading directly 
to the backend and confirms it is validated, hashed, and stored.

**Command:**
```bash
curl -X POST http://localhost:8000/data \
  -H "Content-Type: application/json" \
  -d '{"type":"temperature","value":25}'
```

**Expected Response:**
```json
{
  "status": "ok",
  "hash": "e3b0c44298fc1c149afb..."
}
```

**What this confirms:**
- FastAPI received and validated the payload via Pydantic ✅
- SHA-256 hash was computed and returned ✅
- Record written to PostgreSQL with `blockchain_tx = NULL` ✅

---

### Test 2 — Retrieve Unconfirmed Hashes (Batch Generator)

Returns all records that have been stored in PostgreSQL but not yet submitted to the 
blockchain. This is the input the Batch Hash Generator (L5) prepares for Hyperledger Fabric.

**Command:**
```bash
curl -s http://localhost:8000/batch/unconfirmed | python -c "
import sys, json
d = json.load(sys.stdin)
print(f'Count: {d[\"count\"]}')
print(f'Recomputed: {d[\"recomputed\"]}')
print(f'Sample hash: {d[\"batch\"][0][\"hash\"][:20]}...')
"
```

**Real Output (captured during verification):**
```
Count: 10
Recomputed: False
Sample hash: d15da927ec5905233c86...
```

**What this confirms:**
- 10 records pending blockchain submission ✅
- `Recomputed: False` — hashes originated at L3, never recomputed ✅
- Hashes are ready for Hyperledger Fabric submission ✅

---

### Test 3 — Query the Blockchain Ledger

Queries Hyperledger Fabric directly to retrieve the most recently stored sensor hash 
from the immutable ledger.

**Command:**
```bash
source ~/NanoScript-IoT-Blockchain/env/org1/env.sh

peer chaincode query -C mychannel -n iot_hash \
  -c '{"function":"getAllSensors","Args":["","","10"]}'
```

**Real Output (captured during verification):**
```json
{
  "totalReturned": 1,
  "startKey": "sensor0",
  "records": [
    {
      "key": "sensor001",
      "record": {
        "sensorID": "sensor001",
        "hashValue": "d15da927ec5905233c86e8c9b1b436a696ff251406455701e8383ec2b9dd1c40",
        "timestamp": "2026-03-31T19:25:45.000Z",
        "transactionID": "efdd05510ec7fbd35883d4b58ce804c3b0b0d7df4dda94963e84f71b50613120"
      }
    }
  ]
}
```

**What this confirms:**
- Hyperledger Fabric peer is responding ✅
- Hash and transaction ID are permanently recorded on the ledger ✅
- Both Org1 and Org2 endorsed the transaction before commit ✅

---

### Test 4 — Verify Data Integrity Against the Blockchain

The core integrity check of the entire system. Takes the hash from PostgreSQL and 
verifies it against the blockchain ledger. Returns `true` if the data is untampered, 
`false` if any modification is detected.

**Command:**
```bash
peer chaincode query -C mychannel -n iot_hash \
  -c '{"function":"verifyIntegrity","Args":["sensor001","d15da927ec5905233c86e8c9b1b436a696ff251406455701e8383ec2b9dd1c40"]}'
```

**Real Output (captured during verification):**
```json
{
  "sensorID": "sensor001",
  "verified": true,
  "matchFoundAt": "2026-03-31T19:38:51.000Z",
  "version": 1,
  "transactionID": "de725296afb9fa18ec33636ab3aa82c0fda36cdfaf466a4f4ce6773cc71de8ed",
  "message": "Hash verified against blockchain history"
}
```

**What this confirms:**
- `verified: true` — data is completely untampered ✅
- Hash matched against full blockchain history ✅
- Transaction ID traceable on the ledger ✅

---

### Test 5 — Semantic Search via ChromaDB

Queries the vector database directly using natural language, bypassing the LLM. 
Confirms that the embedding model can retrieve relevant sensor records by meaning 
rather than exact keyword match.

**Command:**
```bash
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
col = client.get_collection('sensor_logs')
print(f'Total documents: {col.count()}')
results = col.query(query_texts=['current temperature reading'], n_results=2)
print('Sample query result:')
for doc in results['documents'][0]:
    print(f'  -> {doc[:100]}')
"
```

**Real Output (captured during verification):**
```
Total documents: 1000
Sample query result:
  -> Time: 2026-03-31 17:17:12, Temp: 20.0C, Hum: 18.0%, GPS: indoor. Hash: 0826ebb310514908
  -> Time: 2026-03-31 17:17:12, Temp: 20.0C, Hum: 18.0%, GPS: indoor. Hash: 0826ebb310514908
```

**What this confirms:**
- 1,000 documents stored as 384-dimensional vectors ✅
- Semantic search returns relevant temperature records without exact keyword match ✅
- Each document includes the blockchain hash for traceability ✅

---

### Test 6 — Full RAG Pipeline (LangChain + LLM)

The end-to-end AI pipeline test. A natural language question is embedded, the most 
relevant sensor records are retrieved from ChromaDB, and llama3.2 generates a grounded 
answer based only on the retrieved data.

**Command:**
```bash
python -c "
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
vector_db = Chroma(
    persist_directory='./chroma_db',
    embedding_function=embeddings,
    collection_name='sensor_logs'
)
llm = ChatOllama(model='llama3.2', temperature=0)

query = 'What is the latest temperature reading?'
docs = vector_db.similarity_search_by_vector(
    embeddings.embed_query(query), k=3
)
context = '\n'.join([d.page_content for d in docs])
response = llm.invoke(f'Based on this data: {context}\n\nAnswer: {query}')
print(f'LLM Response: {response.content}')
"
```

**Real Output (captured during verification):**
```
LLM Response: The latest temperature reading is 20.0C.
```

**What this confirms:**
- HuggingFace embeddings loaded correctly ✅
- ChromaDB similarity search returned relevant context ✅
- llama3.2 answered accurately from blockchain-verified data at temperature=0 ✅
- No data left the machine — fully local and private ✅

---

### Test 7 — Streamlit Chatbot Interface

The final user-facing test. Questions are asked through the web interface at 
`http://localhost:8501` to confirm the full pipeline works end-to-end for a 
non-technical user.

**Start the interface:**
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser and ask the following questions:

| Question | What it tests |
|----------|--------------|
| *"What is the current temperature and humidity?"* | Basic sensor retrieval |
| *"What is the average temperature across all records?"* | Aggregation over stored data |
| *"Show me the GPS status of the latest readings"* | GPS field parsing and retrieval |

The sidebar confirms:
- Live document count from ChromaDB
- Number of blockchain-verified records

The **"View raw data points"** expander under each answer shows the exact documents 
retrieved from ChromaDB to generate that response — allowing full transparency and 
verification that answers are grounded in real blockchain-verified sensor data.

---

### End-to-End Data Flow Summary

```
Arduino MKR Zero (sensor reading every 2s)
        ↓
Python Gateway (serial → HTTP POST)
        ↓
FastAPI /data  (Pydantic validation + SHA-256 hash)
        ↓
PostgreSQL + TimescaleDB  (14,101+ records stored)
        ↓
GET /batch/unconfirmed  (hashes batched for blockchain)
        ↓
Hyperledger Fabric  (Org1 + Org2 endorse → ledger committed)
        ↓
verifyIntegrity() → verified: true
        ↓
ChromaDB (1,000 vector embeddings, semantic search)
        ↓
LangChain + llama3.2  (RAG pipeline, fully local)
        ↓
Streamlit chatbot  (plain language answers at localhost:8501)
```
