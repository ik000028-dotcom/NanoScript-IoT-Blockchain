from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import psycopg2
import hashlib
import json
from datetime import datetime
import subprocess
import threading

app = FastAPI()

# 🔹 Buffer
buffer = {"temperature": None, "humidity": None, "gps_fix": None}

# 🔹 Database Connection
def get_db_conn():
    return psycopg2.connect(
        dbname="iot_data", user="ikramsmac", password="", host="localhost"
    )

# 🔹 Background Sync Task
def run_sync_pipeline():
    try:
        print("🚀 Starting Auto-Sync...")
        subprocess.run(["python", "batch_hash_generator.py"], check=True)
        subprocess.run(["python", "batch_to_fabric_fixed.py"], check=True)
        subprocess.run(["python", "ingest_to_vector.py"], check=True)
        print("✅ Auto-Sync Complete.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

# 🔹 Data model
class SensorData(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    gps_fix: bool | None = None

@app.post("/data")
async def receive_data(data: SensorData, background_tasks: BackgroundTasks):
    global buffer
    data_dict = data.dict()
    for key in buffer:
        if data_dict.get(key) is not None:
            buffer[key] = data_dict[key]

    if all(v is not None for v in buffer.values()):
        full_reading = {
            "temperature": buffer["temperature"],
            "humidity": buffer["humidity"],
            "gps_fix": buffer["gps_fix"],
            "timestamp": datetime.utcnow().isoformat()
        }
        data_string = json.dumps(full_reading, sort_keys=True)
        data_hash = hashlib.sha256(data_string.encode()).hexdigest()

        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sensor_data 
                (temperature, humidity, gps_fix, data_hash)
                VALUES (%s, %s, %s, %s)
            """, (full_reading["temperature"], full_reading["humidity"], 
                  full_reading["gps_fix"], data_hash))
            conn.commit()
            cur.close()
            conn.close()
            
            print("✅ STORED TO POSTGRES:", full_reading)
            background_tasks.add_task(run_sync_pipeline)
            buffer = {k: None for k in buffer}
            return {"status": "stored", "hash": data_hash}
        except Exception as e:
            print(f"❌ DB Error: {e}")
            return {"status": "error", "detail": str(e)}

    return {"status": "waiting"}
