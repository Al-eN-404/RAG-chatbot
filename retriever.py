import os
from vectorstore import get_weaviate_client, get_huggingface_embeddings

def retrieve(query, k=3):
    """
    Search the Weaviate database using hybrid search (BM25 + Semantic).
    """
    # Compute query vector via Hugging Face API
    embeddings = get_huggingface_embeddings([query])
    if not isinstance(embeddings, list) or len(embeddings) != 1:
        raise ValueError("Failed to retrieve embedding vector for query.")
    query_vector = embeddings[0]
    
    retrieved_chunks = []
    
    with get_weaviate_client() as client:
        collection_name = "WebsiteData"
        
        # Check if collection exists before querying
        if not client.collections.exists(collection_name):
            print(f"Collection '{collection_name}' does not exist.")
            return retrieved_chunks
            
        collection = client.collections.get(collection_name)
        
        # Perform hybrid search
        response = collection.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=0.5,  # Balanced hybrid search weighting
            limit=k
        )
        
        for obj in response.objects:
            retrieved_chunks.append({
                "url": obj.properties.get("url", ""),
                "text": obj.properties.get("text", "")
            })
            
    return retrieved_chunks

if __name__ == "__main__":
    # Test retriever
    query = "What is transport?"
    results = retrieve(query)
    for i, chunk in enumerate(results):
        print(f"\nResult {i+1}")
        print(chunk["url"])
        print(chunk["text"][:300])
import os
from vectorstore import get_weaviate_client, get_huggingface_embeddings

def retrieve(query, k=3):
    """
    Search the Weaviate database using hybrid search (BM25 + Semantic).
    """
    # Compute query vector via Hugging Face API
    embeddings = get_huggingface_embeddings([query])
    if not isinstance(embeddings, list) or len(embeddings) != 1:
        raise ValueError("Failed to retrieve embedding vector for query.")
    query_vector = embeddings[0]
    
    retrieved_chunks = []
    
    with get_weaviate_client() as client:
        collection_name = "WebsiteData"
        
        # Check if collection exists before querying
        if not client.collections.exists(collection_name):
            print(f"Collection '{collection_name}' does not exist.")
            return retrieved_chunks
            
        collection = client.collections.get(collection_name)
        
        # Perform hybrid search
        response = collection.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=0.5,  # Balanced hybrid search weighting
            limit=k
        )
        
        for obj in response.objects:
            retrieved_chunks.append({
                "url": obj.properties.get("url", ""),
                "text": obj.properties.get("text", "")
            })
            
    return retrieved_chunks

if __name__ == "__main__":
    # Test retriever
    query = "What is transport?"
    results = retrieve(query)
    for i, chunk in enumerate(results):
        print(f"\nResult {i+1}")
        print(chunk["url"])
        print(chunk["text"][:300])
import os
from sentence_transformers import SentenceTransformer
from vectorstore import get_weaviate_client

# Keep model cached in memory globally to speed up subsequent queries
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model

def retrieve(query, k=3):
    """
    Search the Weaviate database using hybrid search (BM25 + Semantic).
    """
    model = get_embedding_model()
    # Compute query vector locally
    query_vector = model.encode([query])[0].tolist()
    
    retrieved_chunks = []
    
    with get_weaviate_client() as client:
        collection_name = "WebsiteData"
        
        # Check if collection exists before querying
        if not client.collections.exists(collection_name):
            print(f"Collection '{collection_name}' does not exist.")
            return retrieved_chunks
            
        collection = client.collections.get(collection_name)
        
        # Perform hybrid search
        response = collection.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=0.5,  # Balanced hybrid search weighting
            limit=k
        )
        
        for obj in response.objects:
            retrieved_chunks.append({
                "url": obj.properties.get("url", ""),
                "text": obj.properties.get("text", "")
            })
            
    return retrieved_chunks

if __name__ == "__main__":
    # Test retriever
    query = "What is transport?"
    results = retrieve(query)
    for i, chunk in enumerate(results):
        print(f"\nResult {i+1}")
        print(chunk["url"])
        print(chunk["text"][:300])

        
# updated final version 
