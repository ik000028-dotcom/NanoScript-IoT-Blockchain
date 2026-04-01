import serial
import json
import requests
import time

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
            except requests.exceptions.RequestException as e:
                print("Failed to send to API:", e)

    except Exception as e:
        print("Error reading line:", e)