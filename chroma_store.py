import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from chunking import semantic_chunking
import os
import glob

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
# Load Text Files from Data Folder
# -----------------------
data_folder = "data"
all_text = ""
processed_files = []

# Get all text files in the data folder
text_files = glob.glob(os.path.join(data_folder, "*.txt"))

if not text_files:
    print(f"❌ No text files found in {data_folder} folder")
    exit(1)

print(f"📂 Found {len(text_files)} text files:")
for file_path in text_files:
    print(f"  - {os.path.basename(file_path)}")

# Read and combine all text files
for file_path in text_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if content.strip():
                all_text += "\n\n" + content
                processed_files.append(os.path.basename(file_path))
                print(f"✅ Loaded: {os.path.basename(file_path)} ({len(content)} characters)")
            else:
                print(f"⚠️  Empty file: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")

if not all_text.strip():
    print("❌ No content found in any files")
    exit(1)

print(f"\n📄 Total combined text length: {len(all_text)} characters")

# -----------------------
# Chunking
# -----------------------
chunks = semantic_chunking(all_text)

print(f"Total chunks created: {len(chunks)}")

# -----------------------
# Embedding + Store
# -----------------------
embeddings = embedder.encode(chunks).tolist()

ids = [f"chunk_{i}" for i in range(len(chunks))]

metadatas = [
    {
        "source": "biology_books", 
        "chunk_id": i,
        "processed_files": processed_files,
        "total_files": len(processed_files)
    }
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
