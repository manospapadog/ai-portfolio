from dotenv import load_dotenv
import os
import chromadb
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic

load_dotenv()
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("my_docs")
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

question = input("Ask a question about your docs: ")
question_embedding = model.encode(question).tolist()

results = collection.query(query_embeddings=[question_embedding], n_results=4)
retrieved_docs = results["documents"][0]
retrieved_ids = results["ids"][0]

context_with_sources = "\n\n".join(
    f"[Source: {retrieved_ids[i]}]\n{retrieved_docs[i]}"
    for i in range(len(retrieved_docs))
)

response = anthropic_client.messages.create(
    model="claude-sonnet-5",
    max_tokens=300,
    messages=[{
        "role": "user",
        "content": f"Answer the question using ONLY the context below. Cite which source file(s) you used in your answer. If the answer is not contained in the context, respond exactly with: 'I don't have enough information to answer that.' Do not guess.\n\n{context_with_sources}\n\nQuestion: {question}"
    }]
)

for block in response.content:
    if block.type == "text":
        print("\nAnswer:", block.text)