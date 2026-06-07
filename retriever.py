import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)
index = faiss.read_index("website.index")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2")

def retrieve(query, k=3):
    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding).astype("float32"), k)
    results = []
    for idx in indices[0]:
        results.append(chunks[idx])
    return results

query = "What is transport?"

results = retrieve(query)

for i, chunk in enumerate(results):

    print(f"\nResult {i+1}")
    
    print(chunk["url"])

    print(chunk["text"][:300])
