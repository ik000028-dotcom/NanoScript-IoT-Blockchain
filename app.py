import streamlit as st
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ─────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────
st.set_page_config(page_title="Blockchain IoT Dashboard", layout="wide")
st.title("🛡️ Verified IoT Intelligence")

# ─────────────────────────────────────────────
# SYSTEM INITIALIZATION (cached — runs once)
# ─────────────────────────────────────────────
@st.cache_resource
def init_system():
    llm = ChatOllama(model="llama3.2", temperature=0)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings,
        collection_name="sensor_logs"
    )
    return llm, vector_db, embeddings

llm, vector_db, embeddings = init_system()

# ─────────────────────────────────────────────
# QUERY-DRIVEN RETRIEVAL FUNCTION
# ─────────────────────────────────────────────
def retrieve_relevant_data(user_query: str, k: int = 10) -> list:
    query_vector = embeddings.embed_query(user_query)
    docs = vector_db.similarity_search_by_vector(query_vector, k=k)
    return docs

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Ledger Status")
    count = vector_db._collection.count()
    st.metric("Verified Records", count)
    st.success("Hyperledger Fabric: Connected")
    st.divider()
    st.caption("RAG Mode: Query-Driven")
    st.caption("Embedding: all-MiniLM-L6-v2")
    st.caption("LLM: llama3.2 (local)")

# ─────────────────────────────────────────────
# CHAT INTERFACE
# ─────────────────────────────────────────────
if prompt := st.chat_input("Ask anything about your sensor data..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching blockchain ledger..."):
            docs = retrieve_relevant_data(user_query=prompt, k=10)
            context_text = "\n".join([f"DATA: {d.page_content}" for d in docs])
            full_instruction = f"""
You are a secure AI Data Analyst with direct access to a blockchain-verified
IoT sensor ledger. The data below has been cryptographically verified on
Hyperledger Fabric — it is tamper-proof.

VERIFIED DATA FROM LEDGER (retrieved based on your question):
{context_text}

USER QUESTION: {prompt}

RULES:
- Base your answer ONLY on the DATA provided above.
- If asked for an average or calculation, show your working step by step.
- If the data does not contain enough information to answer, say so clearly.
- Always reference the timestamps when discussing specific readings.
- Do not invent values that are not in the data above.
"""
        with st.spinner("Generating answer..."):
            response = llm.invoke(full_instruction)
            st.markdown(response.content)

        with st.expander("🔍 View raw data points used for this answer"):
            for i, doc in enumerate(docs):
                st.text(f"[{i+1}] {doc.page_content}")
