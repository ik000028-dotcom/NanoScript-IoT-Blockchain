import psycopg2
import chromadb
from sentence_transformers import SentenceTransformer
import time
from datetime import datetime

CHROMA_PATH = "/Users/ikramsmac/Documents/PlatformIO/Projects/MKRZeroTest/chroma_db"
INGEST_INTERVAL = 300

def run_ingest(model, collection):
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running ingestion...")
    try:
        conn = psycopg2.connect(dbname="iot_data", user="ikramsmac", host="/tmp")
        cur = conn.cursor()

        # Use count-based offset — no ID fetching needed
        existing_count = collection.count()
        print(f"Already indexed: {existing_count}")

        cur.execute("""
            SELECT 
                t.time, t.temperature, h.humidity,
                t.latitude, t.longitude, t.data_hash
            FROM sensor_data t
            JOIN sensor_data h 
                ON ABS(EXTRACT(EPOCH FROM (t.time - h.time))) < 5
                AND t.temperature IS NOT NULL
                AND h.humidity IS NOT NULL
                AND t.humidity IS NULL
                AND h.temperature IS NULL
            ORDER BY t.time ASC
            LIMIT 100000
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        print(f"Total paired rows in DB: {len(rows)}")

        # Skip already indexed rows using offset
        new_rows = rows[existing_count:]
        print(f"New records to add: {len(new_rows)}")

        if not new_rows:
            print("✅ ChromaDB is up to date")
            return

        documents, ids, metadatas = [], [], []
        added = 0

        for i, (ts, temp, hum, lat, lon, dhash) in enumerate(new_rows):
            rec_id = f"rec_{existing_count + i}"
            gps = f", Lat: {lat}, Lon: {lon}" if lat and lon else ", GPS: indoor"
            text = f"Time: {ts}, Temp: {temp}C, Hum: {hum}%{gps}. Hash: {dhash}"
            documents.append(text)
            ids.append(rec_id)
            metadatas.append({
                "hash": str(dhash),
                "temp": str(temp),
                "hum": str(hum),
                "gps": "outdoor" if (lat and lon) else "indoor"
            })
            added += 1

            if len(documents) >= 100:
                collection.add(documents=documents, ids=ids, metadatas=metadatas)
                print(f"  Uploaded {added} records...")
                documents, ids, metadatas = [], [], []

        if documents:
            collection.add(documents=documents, ids=ids, metadatas=metadatas)

        print(f"✅ Added {added} new records. Total in ChromaDB: {collection.count()}")

    except Exception as e:
        print(f"Ingestion error: {e}")

def main():
    print("--- Initializing embedding model ---")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("--- Connecting to ChromaDB ---")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name="sensor_logs")
    print(f"Existing documents: {collection.count()}")
    print(f"--- Auto-ingestion loop started (every {INGEST_INTERVAL}s) ---")
    while True:
        run_ingest(model, collection)
        print(f"Next ingestion in {INGEST_INTERVAL} seconds...")
        time.sleep(INGEST_INTERVAL)

if __name__ == "__main__":
    main()
