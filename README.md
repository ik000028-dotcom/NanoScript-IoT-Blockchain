# ⛓️ Hyperledger Fabric Installation Guide

This guide details the step-by-step process for installing a permissioned blockchain environment to support the **NanoScript-IoT-Blockchain** framework.

### **1. System Prerequisites**
Hyperledger Fabric requires several underlying technologies. Run the following commands to ensure your environment is ready:

* **Docker & Docker Compose:** To host the blockchain nodes (Peers, Orderers, CAs).
* **Node.js (v18.x):** Required for the JavaScript chaincode execution.
* **Python (3.10+):** Required for the FastAPI backend and RAG gateway.

\`\`\`bash
# For macOS (Using Homebrew)
brew install git curl node@18 python@3.10 docker docker-compose
\`\`\`

### **2. Install Fabric Binaries and Docker Images**
This project is optimized for **Hyperledger Fabric v2.5.4** (LTS). Execute the official bootstrap script to download the Fabric samples, the required binaries (peer, orderer, configtxgen), and the official Docker images:

\`\`\`bash
# Downloads binaries and Docker images for version 2.5.4
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.4 1.5.7
\`\`\`

### **3. Environment Configuration**
Add the downloaded binaries to your system's PATH and define the configuration path so the system can locate the peer CLI:

\`\`\`bash
# Add these lines to your ~/.zshrc or ~/.bashrc
export PATH=\$PWD/bin:\$PATH
export FABRIC_CFG_PATH=\$PWD/config/
\`\`\`

### **4. Smart Contract (Chaincode) Dependencies**
Since the project uses **Node.js** for the Smart Contract (iot_hash.js), you must install the Fabric Contract SDK dependencies before deployment:

\`\`\`bash
cd chaincode/src
npm install
cd ../..
\`\`\`
