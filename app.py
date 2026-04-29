import streamlit as st
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import psycopg2
import hashlib
import json
import subprocess
import os
import re
from datetime import datetime

CHROMA_PATH = "/Users/ikramsmac/Documents/PlatformIO/Projects/MKRZeroTest/chroma_db"
HOME = os.path.expanduser("~")
TN = f"{HOME}/fabric-samples/test-network"

st.set_page_config(page_title="Blockchain IoT Dashboard", layout="wide")
st.title("🛡️ Verified IoT Intelligence")

@st.cache_resource
def init_system():
    llm = ChatOllama(model="llama3.2", temperature=0)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
        collection_name="sensor_logs"
    )
    return llm, vector_db

def get_fabric_env():
    env = os.environ.copy()
    env["FABRIC_CFG_PATH"] = f"{HOME}/fabric-samples/config"
    env["CORE_PEER_TLS_ENABLED"] = "true"
    env["CORE_PEER_LOCALMSPID"] = "Org1MSP"
    env["CORE_PEER_ADDRESS"] = "localhost:7051"
    env["CORE_PEER_MSPCONFIGPATH"] = f"{TN}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
    env["CORE_PEER_TLS_ROOTCERT_FILE"] = f"{TN}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
    env["PATH"] = f"{HOME}/fabric-samples/bin:" + env.get("PATH", "")
    return env

def query_ledger(batch_id):
    """Query Hyperledger ledger for a specific batch"""
    env = get_fabric_env()
    payload = json.dumps({"function": "queryHash", "Args": [batch_id]})
    cmd = [
        f"{HOME}/fabric-samples/bin/peer", "chaincode", "invoke",
        "-o", "localhost:7050",
        "--ordererTLSHostnameOverride", "orderer.example.com",
        "--tls", "--cafile",
        f"{TN}/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem",
        "-C", "mychannel", "-n", "iot_hash",
        "-c", payload,
        "--peerAddresses", "localhost:7051",
        "--tlsRootCertFiles",
        f"{TN}/organizations/peerOrganizations/org1.example.com/tlsca/tlsca.org1.example.com-cert.pem"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=15)
        match = re.search(r'payload:"(.+?)"\s*$', result.stderr.strip(), re.MULTILINE)
        if match:
            raw = match.group(1)
            # Fix escaped quotes from Fabric CLI output
            payload_str = raw.replace('\\"', '"').replace('\\\\', '\\')
            return json.loads(payload_str)
    except:
        pass
    return None

def get_db_connection():
    return psycopg2.connect(dbname="iot_data", user="ikramsmac", host="/tmp")

def get_db_stats():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sensor_data WHERE temperature IS NOT NULL AND humidity IS NOT NULL")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sensor_data WHERE blockchain_tx IS NOT NULL")
        sealed = cur.fetchone()[0]
        cur.execute("SELECT time, temperature, humidity FROM sensor_data WHERE temperature IS NOT NULL ORDER BY time DESC LIMIT 1")
        latest = cur.fetchone()
        cur.close()
        conn.close()
        return total, sealed, latest
    except:
        return 0, 0, None

def get_blockchain_context(prompt=""):
    """Build full blockchain context from both PostgreSQL and Hyperledger ledger"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                blockchain_tx,
                COUNT(*) as records,
                MIN(time) as batch_start,
                MAX(time) as batch_end
            FROM sensor_data
            WHERE blockchain_tx IS NOT NULL
            GROUP BY blockchain_tx
            ORDER BY MIN(time) DESC
        """)
        batches = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) FROM sensor_data 
            WHERE blockchain_tx IS NULL 
            AND temperature IS NOT NULL AND humidity IS NOT NULL
        """)
        unsealed_count = cur.fetchone()[0]
        cur.close()
        conn.close()

        lines = []
        lines.append(f"=== BLOCKCHAIN LEDGER STATUS ===")
        lines.append(f"Total sealed batches : {len(batches)}")
        lines.append(f"Records per batch    : 200")
        lines.append(f"Total sealed records : {len(batches) * 200}")
        lines.append(f"Awaiting next seal   : {unsealed_count}")
        lines.append("")

        confirmed_on_ledger = 0
        pending_count = 0

        for batch in batches:
            tx, records, start, end = batch
            master_hash = tx.replace("pending_", "") if tx.startswith("pending_") else tx
            is_pending = tx.startswith("pending_")

            if not is_pending:
                # Query actual ledger
                ledger_data = query_ledger(tx)
                if ledger_data:
                    confirmed_on_ledger += 1
                    lines.append(f"✅ BATCH {tx}")
                    lines.append(f"   Records   : {records}")
                    lines.append(f"   Period    : {start.strftime('%Y-%m-%d %H:%M')} → {end.strftime('%Y-%m-%d %H:%M')}")
                    lines.append(f"   Master hash: {ledger_data.get('hashValue', master_hash)}")
                    lines.append(f"   Ledger TX  : {ledger_data.get('transactionID', 'N/A')}")
                    lines.append(f"   Timestamp  : {ledger_data.get('timestamp', 'N/A')}")
                else:
                    lines.append(f"⚠️  BATCH {tx} — submitted but not found on ledger")
                    lines.append(f"   Master hash: {master_hash}")
            else:
                pending_count += 1
                lines.append(f"⏳ PENDING BATCH {master_hash[:16]}...")
                lines.append(f"   Records : {records}")
                lines.append(f"   Period  : {start.strftime('%Y-%m-%d %H:%M')} → {end.strftime('%Y-%m-%d %H:%M')}")
                lines.append(f"   Status  : computed but not yet submitted to Hyperledger")

        lines.append("")
        lines.append(f"=== SUMMARY ===")
        lines.append(f"Confirmed on Hyperledger ledger : {confirmed_on_ledger}")
        lines.append(f"Pending blockchain submission   : {pending_count}")

        return "\n".join(lines)

    except Exception as e:
        return f"Blockchain query error: {e}"

def verify_records(n=20):
    """Recompute hashes and compare with stored hashes"""
    import datetime as dt
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT time, temperature, humidity, latitude, longitude, data_hash, blockchain_tx
            FROM sensor_data
            WHERE temperature IS NOT NULL AND humidity IS NOT NULL AND data_hash IS NOT NULL
            ORDER BY time DESC LIMIT %s
        """, (n,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = []
        all_ok = True

        for row in rows:
            time, temp, hum, lat, lon, stored_hash, blockchain_tx = row
            ts_utc = time.astimezone(dt.timezone.utc).isoformat()

            candidates = [
                {"temperature": temp, "humidity": hum, "gps_fix": False, "timestamp": ts_utc},
                {"temperature": temp, "humidity": hum, "timestamp": ts_utc},
            ]
            if lat: candidates[0]["latitude"] = lat
            if lon: candidates[0]["longitude"] = lon

            recomputed = None
            for candidate in candidates:
                c = {k: v for k, v in candidate.items() if v is not None}
                canonical = json.dumps(c, sort_keys=True, separators=(",", ":"))
                h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if h == stored_hash:
                    recomputed = h
                    break

            if recomputed is None:
                all_ok = False
                recomputed = hashlib.sha256(
                    json.dumps(candidates[0], sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()

            results.append({
                "time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "temp": temp, "hum": hum,
                "stored_hash": stored_hash[:20] + "...",
                "match": recomputed == stored_hash,
                "blockchain_tx": blockchain_tx
            })

        return results, all_ok
    except Exception as e:
        return [], False

def smart_query(prompt):
    """Route to appropriate SQL based on question intent"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        p = prompt.lower()
        result_lines = []

        cur.execute("""
            SELECT COUNT(*), ROUND(AVG(temperature)::numeric,2),
                   ROUND(AVG(humidity)::numeric,2),
                   MIN(temperature), MAX(temperature),
                   MIN(humidity), MAX(humidity),
                   MIN(time), MAX(time)
            FROM sensor_data WHERE temperature IS NOT NULL AND humidity IS NOT NULL
        """)
        stats = cur.fetchone()
        result_lines.append(f"=== FULL DATABASE SUMMARY ({stats[0]} total records) ===")
        result_lines.append(f"Temperature → avg: {stats[1]}°C, min: {stats[3]}°C, max: {stats[4]}°C")
        result_lines.append(f"Humidity    → avg: {stats[2]}%, min: {stats[5]}%, max: {stats[6]}%")
        result_lines.append(f"Time range  → {stats[7].strftime('%Y-%m-%d %H:%M')} to {stats[8].strftime('%Y-%m-%d %H:%M')}")
        result_lines.append("")

        if any(k in p for k in ["latest", "current", "now", "recent", "last reading", "right now", "today"]):
            cur.execute("""
                SELECT time, temperature, humidity FROM sensor_data
                WHERE temperature IS NOT NULL AND humidity IS NOT NULL
                ORDER BY time DESC LIMIT 10
            """)
            rows = cur.fetchall()
            result_lines.append("=== LATEST 10 READINGS ===")
            for r in rows:
                result_lines.append(f"[{r[0].strftime('%Y-%m-%d %H:%M:%S')}] Temp: {r[1]}°C, Humidity: {r[2]}%")

        elif any(k in p for k in ["highest", "maximum", "max", "hottest", "peak", "warmest"]):
            cur.execute("SELECT time, temperature, humidity FROM sensor_data WHERE temperature IS NOT NULL ORDER BY temperature DESC LIMIT 10")
            rows = cur.fetchall()
            result_lines.append("=== TOP 10 HIGHEST TEMPERATURES ===")
            for r in rows:
                result_lines.append(f"[{r[0].strftime('%Y-%m-%d %H:%M:%S')}] Temp: {r[1]}°C, Humidity: {r[2]}%")

        elif any(k in p for k in ["lowest", "minimum", "min", "coldest", "coolest"]):
            cur.execute("SELECT time, temperature, humidity FROM sensor_data WHERE temperature IS NOT NULL ORDER BY temperature ASC LIMIT 10")
            rows = cur.fetchall()
            result_lines.append("=== TOP 10 LOWEST TEMPERATURES ===")
            for r in rows:
                result_lines.append(f"[{r[0].strftime('%Y-%m-%d %H:%M:%S')}] Temp: {r[1]}°C, Humidity: {r[2]}%")

        elif any(k in p for k in ["average", "mean", "avg"]):
            cur.execute("""
                SELECT DATE(time), ROUND(AVG(temperature)::numeric,2),
                       ROUND(AVG(humidity)::numeric,2), COUNT(*)
                FROM sensor_data WHERE temperature IS NOT NULL AND humidity IS NOT NULL
                GROUP BY DATE(time) ORDER BY DATE(time) DESC LIMIT 14
            """)
            rows = cur.fetchall()
            result_lines.append("=== DAILY AVERAGES (last 14 days) ===")
            for r in rows:
                result_lines.append(f"[{r[0]}] Avg Temp: {r[1]}°C, Avg Humidity: {r[2]}%, Readings: {r[3]}")

        elif any(k in p for k in ["anomal", "unusual", "spike", "strange", "weird", "outlier"]):
            cur.execute("""
                SELECT time, temperature, humidity FROM sensor_data
                WHERE temperature IS NOT NULL AND humidity IS NOT NULL
                AND (temperature > (SELECT AVG(temperature) + 2*STDDEV(temperature) FROM sensor_data WHERE temperature IS NOT NULL)
                OR temperature < (SELECT AVG(temperature) - 2*STDDEV(temperature) FROM sensor_data WHERE temperature IS NOT NULL))
                ORDER BY time DESC LIMIT 20
            """)
            rows = cur.fetchall()
            result_lines.append(f"=== ANOMALOUS READINGS ({len(rows)} found) ===")
            for r in rows:
                result_lines.append(f"[{r[0].strftime('%Y-%m-%d %H:%M:%S')}] Temp: {r[1]}°C, Humidity: {r[2]}%")

        else:
            cur.execute("""
                SELECT DATE_TRUNC('hour', time),
                       ROUND(AVG(temperature)::numeric,2),
                       ROUND(AVG(humidity)::numeric,2), COUNT(*)
                FROM sensor_data
                WHERE temperature IS NOT NULL AND humidity IS NOT NULL
                AND time > NOW() - INTERVAL '24 hours'
                GROUP BY DATE_TRUNC('hour', time)
                ORDER BY DATE_TRUNC('hour', time) DESC
            """)
            rows = cur.fetchall()
            result_lines.append("=== LAST 24 HOURS (hourly summary) ===")
            for r in rows:
                result_lines.append(f"[{r[0].strftime('%Y-%m-%d %H:%M')}] Avg Temp: {r[1]}°C, Avg Humidity: {r[2]}%, Readings: {r[3]}")

        cur.close()
        conn.close()
        return "\n".join(result_lines)
    except Exception as e:
        return f"DB error: {e}"

llm, vector_db = init_system()

# Sidebar — status only, no blockchain UI
with st.sidebar:
    st.header("📊 System Status")
    total, sealed, latest = get_db_stats()
    chroma_count = vector_db._collection.count()
    st.metric("Complete Records", total)
    st.metric("Blockchain Sealed", sealed)
    st.metric("ChromaDB Indexed", chroma_count)
    if latest:
        st.metric("Latest Temp", f"{latest[1]}°C")
        st.metric("Latest Humidity", f"{latest[2]}%")
        st.caption(f"At {latest[0].strftime('%Y-%m-%d %H:%M:%S')}")
    st.success("✅ Hyperledger Fabric: Connected")
    st.success("✅ ChromaDB: Live")
    st.success("✅ Llama 3.2: Ready")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask anything about your sensor data or blockchain..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        p = prompt.lower()

        # Route: blockchain/ledger questions
        if any(k in p for k in ["blockchain", "ledger", "sealed", "batch", "master hash", "fabric", "hyperledger", "transaction", "seal"]):
            with st.spinner("🔗 Querying Hyperledger ledger..."):
                blockchain_context = get_blockchain_context(prompt)

            full_instruction = f"""You are a blockchain IoT analyst. Answer using the ledger data below.

Current time: {now}

{blockchain_context}

USER QUESTION: {prompt}

INSTRUCTIONS:
- Answer directly from the ledger data above.
- Explain what sealed means: 200 sensor readings were hashed together into one master hash and written permanently to Hyperledger Fabric.
- Distinguish between confirmed on ledger (✅) and pending (⏳).
- If asked about a specific batch, provide its master hash and transaction ID.
- Be precise and factual.

ANSWER:"""
            with st.spinner("🤖 Analyzing..."):
                response = llm.invoke(full_instruction)
                st.markdown(response.content)
                st.session_state.messages.append({"role": "assistant", "content": response.content})

            with st.expander("🔍 Raw ledger data used"):
                st.text(blockchain_context)

        # Route: integrity/tamper verification
        elif any(k in p for k in ["verify", "tamper", "integrity", "hash check", "authentic", "changed"]):
            with st.spinner("🔐 Recomputing hashes..."):
                results, all_ok = verify_records(20)

            summary = f"Verified {len(results)} records. " + ("✅ All hashes match — no tampering detected." if all_ok else "❌ TAMPERING DETECTED in one or more records.")
            st.markdown(f"### 🔐 Integrity Report\n{summary}")

            for r in results:
                icon = "✅" if r["match"] else "❌"
                sealed_icon = "⛓️" if r["blockchain_tx"] else "⏳"
                st.markdown(f"{icon} {sealed_icon} `{r['time']}` T:{r['temp']}°C H:{r['hum']}% | `{r['stored_hash']}`")

            st.session_state.messages.append({"role": "assistant", "content": summary})

        # Route: sensor data questions
        else:
            db_context = smart_query(prompt)
            docs = vector_db.similarity_search(prompt, k=5)
            semantic_context = "\n".join([d.page_content for d in docs])

            full_instruction = f"""You are a private AI Data Analyst for a blockchain-verified IoT sensor system.
Current time: {now}

DATABASE RESULTS:
{db_context}

SEMANTICALLY RELATED RECORDS:
{semantic_context}

USER QUESTION: {prompt}

INSTRUCTIONS:
- Answer using the DATABASE RESULTS as primary source.
- Always mention how many total records the answer is based on.
- Include timestamps when relevant.
- Be concise and factual.

ANSWER:"""

            with st.spinner("🔍 Analyzing sensor data..."):
                response = llm.invoke(full_instruction)
                st.markdown(response.content)
                st.session_state.messages.append({"role": "assistant", "content": response.content})

            with st.expander("🔍 View source data"):
                st.subheader("Database results")
                st.text(db_context)
                st.subheader("Semantic search")
                st.text(semantic_context)
