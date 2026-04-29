import serial
import json
import requests
import time
import subprocess
import psycopg2

def check_and_seal_batch():
    """Auto-seal when 200+ unconfirmed complete records exist"""
    try:
        conn = psycopg2.connect(dbname="iot_data", user="ikramsmac", host="/tmp")
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM sensor_data 
            WHERE blockchain_tx IS NULL 
            AND data_hash IS NOT NULL
            AND (temperature IS NOT NULL OR humidity IS NOT NULL)
        """)
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        if count >= 200:
            print(f"🔗 {count} unconfirmed records — auto-sealing batch...")
            result = subprocess.run(
                ["python3", "batch_to_fabric.py"],
                cwd="/Users/ikramsmac/Documents/PlatformIO/Projects/MKRZeroTest/NanoScript-IoT-Blockchain",
                capture_output=True, text=True, timeout=60
            )
            print(result.stdout)
            if result.returncode != 0:
                print("Batch error:", result.stderr[:200])
    except Exception as e:
        print(f"Auto-batch error: {e}")

# SERIAL SETTINGS
SERIAL_PORT = "/dev/tty.usbmodem101"  # ← this goes here, not in terminal
BAUD_RATE = 9600

# FASTAPI ENDPOINT
API_URL = "http://127.0.0.1:8000/data"

# Connect to Arduino
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # wait for Arduino to reset

print("Gateway started. Reading data from Arduino...")

while True:
    try:
        line = ser.readline().decode().strip()
        if not line or line.startswith('---'):
            continue

        data = {}
        if "Temperature" in line:
            data['temperature'] = float(line.split(":")[1].strip())
        elif "Humidity" in line:
            data['humidity'] = float(line.split(":")[1].strip())
        elif "Latitude" in line:
            data['latitude'] = float(line.split(":")[1].strip())
        elif "Longitude" in line:
            data['longitude'] = float(line.split(":")[1].strip())
        elif "Waiting for GPS" in line:
            data['gps_fix'] = False

        if data:
            print("Read data:", data)
            try:
                response = requests.post(API_URL, json=data)
                print("Sent to API, status:", response.status_code)
                if response.status_code == 200:
                    check_and_seal_batch()
            except requests.exceptions.RequestException as e:
                print("Failed to send to API:", e)

    except Exception as e:
        print("Error reading line:", e)