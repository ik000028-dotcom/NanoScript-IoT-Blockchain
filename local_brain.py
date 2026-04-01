import os
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# CHANGE THIS LINE:
from langchain_classic.chains import RetrievalQA

print("🏔️ Initializing Local RAG Framework (Llama 3.2)...")

# (The rest of your code remains exactly the same!)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings, 
    collection_name="sensor_logs"
)
llm = ChatOllama(model="llama3.2", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=db.as_retriever(search_kwargs={"k": 3})
)

def run_ai():
    print("\n✅ READY. I can see 3,383 blockchain records.")
    while True:
        query = input("\nUser: ")
        if query.lower() in ['exit', 'quit']:
            break
        print("AI is thinking...")
        try:
            response = qa_chain.invoke({"query": query})
            print(f"\n🤖 AI: {response['result']}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_ai()