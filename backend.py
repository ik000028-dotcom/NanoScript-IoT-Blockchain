from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import hashlib
import json
from datetime import datetime

app = FastAPI()

# 🔹 Temporary buffer to merge readings
buffer = {
    "temperature": None,
    "humidity": None,
    "gps_fix": None
}

# 🔹 PostgreSQL connection
conn = psycopg2.connect(
    dbname="iot_data",
    user="ikramsmac",
    password="",
    host="localhost"
)
cursor = conn.cursor()

# 🔹 Data model
class SensorData(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    gps_fix: bool | None = None

# 🔹 Insert function
def insert_into_db(reading, data_hash):
    cursor.execute("""
        INSERT INTO sensor_readings
        (temperature, humidity, latitude, longitude, gps_fix, data_hash)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        reading["temperature"],
        reading["humidity"],
        None,  # latitude (not used now)
        None,  # longitude (not used now)
        reading["gps_fix"],
        data_hash
    ))
    conn.commit()

# 🔹 Main endpoint (MERGING LOGIC)
@app.post("/data")
def receive_data(data: SensorData):
    global buffer

    data_dict = data.dict()

    # ✅ Update buffer with incoming values
    for key in buffer:
        if data_dict.get(key) is not None:
            buffer[key] = data_dict[key]

    # 🔍 Check if all values are collected
    if all(v is not None for v in buffer.values()):

        # ✅ Create full reading object
        full_reading = {
            "temperature": buffer["temperature"],
            "humidity": buffer["humidity"],
            "gps_fix": buffer["gps_fix"],
            "timestamp": datetime.utcnow().isoformat()
        }

        # ✅ Compute hash
        data_string = json.dumps(full_reading, sort_keys=True)
        data_hash = hashlib.sha256(data_string.encode()).hexdigest()

        # ✅ Insert into DB
        insert_into_db(full_reading, data_hash)

        # 🔄 Reset buffer
        buffer = {k: None for k in buffer}

        print("✅ STORED FULL READING:", full_reading)

        return {"status": "stored", "hash": data_hash}

    print("⏳ WAITING FOR FULL DATA:", buffer)

    return {"status": "waiting"}
