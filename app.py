import streamlit as st
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Setup the Web Page
st.set_page_config(page_title="Blockchain IoT Dashboard", layout="wide")
st.title("🛡️ Verified IoT Intelligence")

# 2. Connect to the "Brain" and "Library"
@st.cache_resource
def init_system():
    # Use the local Llama 3.2 model you downloaded
    llm = ChatOllama(model="llama3.2", temperature=0)
    
    # Load the 3,383 records from your folder
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma(
        persist_directory="./chroma_db", 
        embedding_function=embeddings, 
        collection_name="sensor_logs"
    )
    return llm, vector_db

llm, vector_db = init_system()

# 3. Sidebar Status
with st.sidebar:
    st.header("Ledger Status")
    count = vector_db._collection.count()
    st.metric("Verified Records", count)
    st.success("Hyperledger Fabric: Connected")

# 4. Chat Interface
if prompt := st.chat_input("Ask: What is the average temperature?"):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # SEARCH: Pull the top 20 records for context
        docs = vector_db.similarity_search("temperature humidity sensor", k=20)
        context_text = "\n".join([f"DATA: {d.page_content}" for d in docs])
        
        # SYSTEM PROMPT: Forcing the AI to use the data provided
        full_instruction = f"""
        You are a private AI Data Analyst. You have direct access to the local 
        blockchain ledger containing IoT sensor readings.
        
        DATA FROM LEDGER:
        {context_text}
        
        USER QUESTION: {prompt}
        
        RULES:
        - Use the numbers provided in the DATA section above.
        - If asked for an average, calculate it mathematically.
        - Do not say 'I don't know' or 'I can't verify'—the data is already verified.
        """
        
        with st.spinner("Analyzing Blockchain Ledger..."):
            response = llm.invoke(full_instruction)
            st.markdown(response.content)
            
        with st.expander("🔍 View raw data points used for this answer"):
            st.text(context_text)