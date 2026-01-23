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

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="biolens_biology"
)

embedder = SentenceTransformer(EMBEDDING_MODEL)

# -----------------------
# Load PDF Files from ChromaDB Folder
# -----------------------
data_folder = "chromadb"
all_text = ""
processed_files = []

# Get all PDF files in the data folder
pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))

if not pdf_files:
    print(f"❌ No PDF files found in {data_folder} folder")
    exit(1)

print(f"📂 Found {len(pdf_files)} PDF files:")
for file_path in pdf_files:
    print(f"  - {os.path.basename(file_path)}")

# Read and extract text from all PDF files
import fitz  # PyMuPDF

for file_path in pdf_files:
    try:
        with fitz.open(file_path) as doc:
            text_content = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += page.get_text()
            
            if text_content.strip():
                all_text += "\n\n" + text_content
                processed_files.append(os.path.basename(file_path))
                print(f" Loaded: {os.path.basename(file_path)} ({len(text_content)} characters, {len(doc)} pages)")
            else:
                print(f"  Empty PDF: {os.path.basename(file_path)}")
    except Exception as e:
        print(f" Error reading {file_path}: {e}")

if not all_text.strip():
    print(" No content found in any PDF files")
    exit(1)

print(f"\n Total extracted text length: {len(all_text)} characters")

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
        "files": ",".join(processed_files),
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

print(" Chunks stored successfully in ChromaDB")
