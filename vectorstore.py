import os
import weaviate
import weaviate.classes as wvc
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

def get_secret(key_name, default=None):
    try:
        import streamlit as st
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, default)

def get_weaviate_client():
    """
    Establish a connection to the Weaviate v4 instance.
    Supports local Docker setup or Weaviate Cloud (WCD) cluster configuration.
    """
    url = get_secret("WEAVIATE_URL", "http://localhost:8080").strip()
    api_key = get_secret("WEAVIATE_API_KEY")
    
    # Auto-prepend scheme if missing
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
            
    auth = wvc.init.Auth.api_key(api_key) if api_key else None
    
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=url,
        auth_credentials=auth
    )

def build_vectorstore(chunks):
    """
    Encode chunks locally using SentenceTransformer and upload them to Weaviate in batch.
    """
    # Initialize the local embedding model
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    # Extract texts and compute embeddings locally
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    with get_weaviate_client() as client:
        collection_name = "WebsiteData"
        
        # Delete if exists to rebuild fresh
        if client.collections.exists(collection_name):
            client.collections.delete(collection_name)
            
        # Create collection without server-side vectorizer (we supply vectors)
        collection = client.collections.create(
            name=collection_name,
            properties=[
                wvc.config.Property(name="text", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="url", data_type=wvc.config.DataType.TEXT),
            ],
            vectorizer_config=None
        )
        
        # Batch upload to Weaviate
        with collection.batch.dynamic() as batch:
            for i, chunk in enumerate(chunks):
                vector = embeddings[i].tolist() 
                batch.add_object(
                    properties={
                        "text": chunk["text"],
                        "url": chunk["url"]
                    },
                    vector=vector
                )
        print(f"Ingested {len(chunks)} chunks into Weaviate.")

#  updated final version
