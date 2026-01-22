import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
client = chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False
    )
)

collection = client.get_collection("biolens_biology")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

query = "What is the function of the mitochondria?"
query_embedding = embedder.encode(query).tolist()
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

print("\n🔍 Query:", query)
print("\n📚 Retrieved Chunks:\n")

for i, doc in enumerate(results["documents"][0]):
    print(f"--- Chunk {i+1} ---")
    print(doc)
    print()