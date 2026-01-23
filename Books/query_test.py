import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection("biolens_biology")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Test multiple queries
test_queries = [
    "What is the function of the mitochondria?",
    "How does photosynthesis work?",
    "What are the stages of cell division?",
    "Explain the structure of DNA",
    "What is the difference between prokaryotic and eukaryotic cells?"
]

for query in test_queries:
    query_embedding = embedder.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    print("\n🔍 Query:", query)
    print("\n📚 Retrieved Chunks:\n")

    for i, doc in enumerate(results["documents"][0]):
        print(f"--- Chunk {i+1} ---")
        print(doc[:200] + "..." if len(doc) > 200 else doc)
        print()
    
    print("=" * 80)