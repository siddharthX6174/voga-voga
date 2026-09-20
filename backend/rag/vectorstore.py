import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

def get_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    # Ensure the directory exists
    os.makedirs("./data/chroma_db", exist_ok=True)
    
    vectorstore = Chroma(
        persist_directory="./data/chroma_db",
        embedding_function=embeddings,
        collection_name="enterprise_policies"
    )
    return vectorstore
