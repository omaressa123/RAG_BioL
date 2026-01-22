import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from chunking import semantic_chunking  # أو أي method

# -----------------------
# Setup
# -----------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

client = chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False
    )
)

collection = client.get_or_create_collection(
    name="biolens_biology"
)

embedder = SentenceTransformer(EMBEDDING_MODEL)

# -----------------------
# Load Text
# -----------------------
with open("data/biology_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

# -----------------------
# Chunking
# -----------------------
chunks = semantic_chunking(text)

print(f"Total chunks created: {len(chunks)}")

# -----------------------
# Embedding + Store
# -----------------------
embeddings = embedder.encode(chunks).tolist()

ids = [f"chunk_{i}" for i in range(len(chunks))]

metadatas = [
    {"source": "biology_book", "chunk_id": i}
    for i in range(len(chunks))
]

collection.add(
    documents=chunks,
    embeddings=embeddings,
    ids=ids,
    metadatas=metadatas
)

client.persist()

print("✅ Chunks stored successfully in ChromaDB")
