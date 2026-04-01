import requests
import time
import random

API_URL = "http://fastapi:8000/data"

def simulate_sensor():
    time.sleep(10)  # Wait for FastAPI to start
    while True:
        data = {
            "temperature": round(random.uniform(18, 30), 1),
            "humidity": round(random.uniform(10, 25), 1)
        }
        try:
            response = requests.post(API_URL, json=data, timeout=5)
            print(f"Sent: {data}, Status: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    simulate_sensor()
