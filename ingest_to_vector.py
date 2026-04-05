import psycopg2
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime

def run():
    print("--- STEP 1: Initializing AI Models ---")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("--- STEP 2: Connecting to ChromaDB ---")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Delete old collection and recreate fresh
    try:
        client.delete_collection("sensor_logs")
        print("Old collection deleted")
    except:
        pass
    collection = client.create_collection(name="sensor_logs")
    
    print("--- STEP 3: Connecting to PostgreSQL ---")
    conn = psycopg2.connect(dbname="iot_data", user="ikramsmac", host="/tmp")
    cur = conn.cursor()
    
    print("--- STEP 4: Fetching Paired Data ---")
    cur.execute("""
        SELECT 
            t.time,
            t.temperature,
            h.humidity,
            t.latitude,
            t.longitude,
            t.data_hash
        FROM sensor_data t
        JOIN sensor_data h 
            ON ABS(EXTRACT(EPOCH FROM (t.time - h.time))) < 5
            AND t.temperature IS NOT NULL
            AND h.humidity IS NOT NULL
            AND t.humidity IS NULL
            AND h.temperature IS NULL
        ORDER BY t.time DESC
        LIMIT 1000
    """)
    rows = cur.fetchall()
    print(f"Total paired rows found: {len(rows)}")

    documents, ids, metadatas = [], [], []

    print("--- STEP 5: Processing Records ---")
    for i, (ts, temp, hum, lat, lon, dhash) in enumerate(rows):

        # Include GPS in document text if available, gracefully skip if indoors
        gps = f", Lat: {lat}, Lon: {lon}" if lat and lon else ", GPS: indoor"
        text = f"Time: {ts}, Temp: {temp}C, Hum: {hum}%{gps}. Hash: {dhash}"

        documents.append(text)
        ids.append(f"rec_{i}")
        metadatas.append({
            "hash": str(dhash),
            "temp": str(temp),
            "hum": str(hum),
            "gps": "outdoor" if (lat and lon) else "indoor"
        })

        # Upload in batches of 100
        if len(documents) >= 100:
            collection.add(documents=documents, ids=ids, metadatas=metadatas)
            print(f"  Uploaded batch up to record {i+1}...")
            documents, ids, metadatas = [], [], []

    # Final batch
    if documents:
        collection.add(documents=documents, ids=ids, metadatas=metadatas)

    print(f"--- ✅ FINISHED: Indexed {collection.count()} documents ---")
    conn.close()

if __name__ == "__main__":
    run()
