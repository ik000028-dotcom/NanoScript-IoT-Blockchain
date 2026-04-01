import psycopg2
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime

def run():
    print("--- STEP 1: Initializing AI Models ---")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("--- STEP 2: Connecting to ChromaDB ---")
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="sensor_logs")
    
    print("--- STEP 3: Connecting to PostgreSQL ---")
    conn = psycopg2.connect(dbname="iot_data", user="ikramsmac", host="/tmp")
    cur = conn.cursor()
    
    print("--- STEP 4: Fetching Data ---")
    cur.execute("SELECT time, temperature, humidity, latitude, longitude, data_hash FROM sensor_data")
    rows = cur.fetchall()
    print(f"Total rows found: {len(rows)}")

    documents, ids, metadatas = [], [], []
    
    print("--- STEP 5: Processing Records (Ignoring missing GPS for Indoor Test) ---")
    for i, row in enumerate(rows):
        timestamp, temp, hum, lat, lon, d_hash = row
        
        # We only need Temp and Hum to be valid. Lat/Lon can be None/0.0.
        if temp is None or hum is None:
            continue

        text = f"Time: {timestamp}, Temp: {temp}C, Hum: {hum}%. Verified: {d_hash}"
        documents.append(text)
        ids.append(f"id_{i}_{timestamp.strftime('%s')}")
        metadatas.append({"hash": d_hash})

        # Add to DB in batches of 100
        if len(documents) >= 100:
            collection.add(documents=documents, ids=ids, metadatas=metadatas)
            print(f"Uploaded {i+1} records...")
            documents, ids, metadatas = [], [], []

    # Final batch
    if documents:
        collection.add(documents=documents, ids=ids, metadatas=metadatas)

    print(f"--- ✅ FINISHED: Indexed {len(rows)} records ---")
    conn.close()

if __name__ == "__main__":
    run()