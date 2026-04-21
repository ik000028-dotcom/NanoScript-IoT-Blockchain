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

## 🔍 Layer-by-Layer Validation
To ensure the integrity of the 11-layer pipeline, follow these validation steps:

1. **Perception Layer (L1-L2):** Open the Arduino Serial Monitor. Verify JSON packets are transmitting: `{"temp": 21.0, "hum": 17.0, "gps": [...]}`.
2. **Blockchain Layer (L6-L7):** Verify the ledger is recording hashes by querying the channel:
   \`\`\`bash
   peer chaincode query -C mychannel -n iot_hash -c '{"function":"getAllSensors","Args":["","","10"]}'
   \`\`\`
3. **Intelligence Layer (L9-L11):** Run the local test script to verify RAG retrieval:
   \`\`\`bash
   python test_llm.py
   \`\`\`
   *Success Condition:* The AI returns a response labeled "Verified" based on the last 50 ledger records.

## 📝 API Documentation (Chaincode Functions)
The Smart Contract (\`iot_hash.js\`) exposes the following functions via the Fabric Gateway:

* **createSensor(ID, Hash, Owner):** Commits a new SHA-256 sensor batch hash to the ledger.
* **querySensor(ID):** Returns the world-state data and transaction history for a specific sensor ID.
* **getAllSensors(start, end, limit):** Range query to retrieve historical batches for AI analysis.
* **transferOwnership(ID, newOwner):** Updates the permissioned MSP owner of a specific data asset.

## 🛠️ Troubleshooting
| Problem | Solution |
| :--- | :--- |
| **Docker containers not found** | Run \`docker ps -a\`. If stopped, restart with \`docker-compose up -d\`. |
| **Chaincode broken/missing** | Restore from \`chaincode/backup/\` and run your redeploy script. |
| **RAG returns no data** | Ensure the vector DB is synced: \`python ingest_to_vector.py\`. |
