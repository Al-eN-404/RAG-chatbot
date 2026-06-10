import os
import weaviate
import weaviate.classes as wvc
import requests
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

def get_huggingface_embeddings(texts):
    """
    Generate embeddings using Hugging Face's serverless Inference API.
    Does not require local PyTorch/SentenceTransformer installation,
    significantly reducing memory footprint to fit in Render Free tier (512MB).
    Batches requests to prevent API limits or timeouts.
    """
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
    
    hf_token = get_secret("HF_TOKEN")
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    # If a single string is passed, wrap it in a list
    is_single = isinstance(texts, str)
    if is_single:
        texts = [texts]
        
    batch_size = 32
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        payload = {
            "inputs": batch,
            "options": {"wait_for_model": True}
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 503:
            import time
            for _ in range(5):
                time.sleep(3)
                response = requests.post(api_url, headers=headers, json=payload)
                if response.status_code != 503:
                    break
                    
        if response.status_code != 200:
            raise Exception(
                f"Hugging Face API error ({response.status_code}): {response.text}\n"
                f"Please ensure HF_TOKEN is configured correctly in Render secrets or .env file."
            )
            
        batch_embeddings = response.json()
        if not isinstance(batch_embeddings, list):
            raise ValueError(f"Unexpected embeddings format from Hugging Face API: {type(batch_embeddings)}")
            
        all_embeddings.extend(batch_embeddings)
        
    return all_embeddings[0] if is_single else all_embeddings

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
    Encode chunks using Hugging Face Inference API and upload them to Weaviate in batch.
    """
    # Extract texts and compute embeddings using Hugging Face API
    texts = [chunk["text"] for chunk in chunks]
    embeddings = get_huggingface_embeddings(texts)
    
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
                vector = embeddings[i].tolist()  # Convert numpy array to list of floats
                batch.add_object(
                    properties={
                        "text": chunk["text"],
                        "url": chunk["url"]
                    },
                    vector=vector
                )
        print(f"Ingested {len(chunks)} chunks into Weaviate.")import os
import weaviate
import weaviate.classes as wvc
import requests
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

def get_huggingface_embeddings(texts):
    """
    Generate embeddings using Hugging Face's serverless Inference API.
    Does not require local PyTorch/SentenceTransformer installation,
    significantly reducing memory footprint to fit in Render Free tier (512MB).
    Batches requests to prevent API limits or timeouts.
    """
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
    
    hf_token = get_secret("HF_TOKEN")
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    # If a single string is passed, wrap it in a list
    is_single = isinstance(texts, str)
    if is_single:
        texts = [texts]
        
    batch_size = 32
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        payload = {
            "inputs": batch,
            "options": {"wait_for_model": True}
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 503:
            import time
            for _ in range(5):
                time.sleep(3)
                response = requests.post(api_url, headers=headers, json=payload)
                if response.status_code != 503:
                    break
                    
        if response.status_code != 200:
            raise Exception(
                f"Hugging Face API error ({response.status_code}): {response.text}\n"
                f"Please ensure HF_TOKEN is configured correctly in Render secrets or .env file."
            )
            
        batch_embeddings = response.json()
        if not isinstance(batch_embeddings, list):
            raise ValueError(f"Unexpected embeddings format from Hugging Face API: {type(batch_embeddings)}")
            
        all_embeddings.extend(batch_embeddings)
        
    return all_embeddings[0] if is_single else all_embeddings

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
    Encode chunks using Hugging Face Inference API and upload them to Weaviate in batch.
    """
    # Extract texts and compute embeddings using Hugging Face API
    texts = [chunk["text"] for chunk in chunks]
    embeddings = get_huggingface_embeddings(texts)
    
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
                vector = embeddings[i].tolist()  # Convert numpy array to list of floats
                batch.add_object(
                    properties={
                        "text": chunk["text"],
                        "url": chunk["url"]
                    },
                    vector=vector
                )
        print(f"Ingested {len(chunks)} chunks into Weaviate.")import os
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
