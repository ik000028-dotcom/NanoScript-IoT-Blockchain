# Windows Setup Guide for Supervisor

## Prerequisites (Install First)

1. **Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop
   - During install: Enable WSL2 when prompted
   - Restart computer after installation

2. **Git for Windows**
   - Download: https://git-scm.com/download/win
   - Use default settings during install

## Quick Start (5 Minutes)

Open PowerShell or Command Prompt, then run:

```bash
# 1. Clone the repository
git clone https://github.com/ik000028-dotcom/NanoScript-IoT-Blockchain.git
cd NanoScript-IoT-Blockchain

# 2. Start all services
docker-compose up -d

# 3. Verify everything is running
docker-compose ps
