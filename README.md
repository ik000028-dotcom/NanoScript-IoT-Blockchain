# NanoScript IoT Blockchain System

## 🎯 Project Overview

A complete end-to-end IoT data integrity system that combines:
- **Arduino MKR Zero** with sensors (DHT11, GPS)
- **FastAPI Backend** for data validation and hashing
- **PostgreSQL + TimescaleDB** for time-series storage
- **Hyperledger Fabric Blockchain** for immutable audit trails
- **RAG Pipeline** with LLM for intelligent data querying


---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Hardware Requirements](#hardware-requirements)
3. [Software Stack](#software-stack)
4. [Installation Guide](#installation-guide)
5. [Layer-by-Layer Validation](#layer-by-layer-validation)
6. [API Documentation](#api-documentation)
7. [Blockchain Integration](#blockchain-integration)
8. [Troubleshooting](#troubleshooting)


---

## 🏗️ System Architecture
┌─────────────────┐
│  Arduino MKR    │  L1: IoT Device
│  Zero + Sensors │     (Temperature, Humidity, GPS)
└────────┬────────┘
│ Serial USB
▼
┌─────────────────┐
│  Python Gateway │  L2: Data Aggregation
│  (gateway.py)   │     (Serial → HTTP)
└────────┬────────┘
│ HTTP POST
▼
┌─────────────────┐
│  FastAPI        │  L3: Validation & Hashing
│  Backend        │     (SHA-256 computation)
└────────┬────────┘
│ SQL + Hash
▼
┌─────────────────┐
│  PostgreSQL +   │  L4: Trusted Registry
│  TimescaleDB    │     (Time-series storage)
└────────┬────────┘
│ Batch Read
▼
┌─────────────────┐
│  Batch Hash     │  L5: Batch Generator
│  Generator      │     (Pre-computed hashes)
└────────┬────────┘
│ gRPC/HTTP
▼
┌─────────────────┐
│  Hyperledger    │  L6: Smart Contract
│  Fabric         │     (iot_hash chaincode)
└────────┬────────┘
│ Consensus
▼
┌─────────────────┐
│  Blockchain     │  L7: Immutable Ledger
│  Ledger         │     (Org1 + Org2 endorsement)
└────────┬────────┘
│ Verified Data
▼
┌─────────────────┐
│  RAG Pipeline   │  L8-L11: AI Integration
│  (LangChain +   │     (Vector DB + LLM)
│   LLM)          │
└─────────────────┘

---

## 💻 Hardware Requirements

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

## 🛠️ Software Stack

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

## 📥 Installation Guide

### Prerequisites

```bash
brew install postgresql@17
brew install timescaledb
brew install docker
brew install git

python3.10 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn psycopg2-binary pydantic
