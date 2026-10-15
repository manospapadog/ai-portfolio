import os
import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("my_docs")

docs_folder = "docs"
for filename in os.listdir(docs_folder):
    if filename.endswith(".txt"):
        with open(os.path.join(docs_folder, filename), "r") as f:
            text = f.read()
        embedding = model.encode(text).tolist()
        collection.add(
            documents=[text],
            embeddings=[embedding],
            ids=[filename]
        )
        print(f"Added: {filename}")

print("Index built.")