from langchain_ollama import ChatOllama

print("Testing connection to Llama 3.2...")
try:
    llm = ChatOllama(model="llama3.2")
    # A simple prompt to see if the engine is running
    response = llm.invoke("Hello! Are you running on my Mac?")
    print(f"\n✅ SUCCESS! LLM says: {response.content}")
except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")
    print("Make sure the Ollama app is open in your menu bar!")