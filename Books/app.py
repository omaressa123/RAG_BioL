"""
BioLens RAG Flask Application
Connects frontend with ChromaDB backend
"""

from flask import Flask, render_template, request, jsonify
import chromadb
from sentence_transformers import SentenceTransformer
import os
import glob
import fitz
from chunking import semantic_chunking
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Global variables for processing status
processing_status = {
    "is_processing": False,
    "progress": 0,
    "current_step": "",
    "pages_processed": 0,
    "total_pages": 0,
    "error": None
}

# Initialize ChromaDB and models
try:
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("biolens_biology")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ ChromaDB and models loaded successfully")
except Exception as e:
    print(f"❌ Error initializing database: {e}")
    collection = None
    embedder = None

def process_pdf_background(pdf_path):
    """Background processing for PDF files"""
    global processing_status
    
    try:
        processing_status.update({
            "is_processing": True,
            "progress": 0,
            "current_step": "Reading PDF",
            "pages_processed": 0,
            "total_pages": 0,
            "error": None
        })
        
        # Extract text from PDF
        with fitz.open(pdf_path) as doc:
            processing_status["total_pages"] = len(doc)
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += page.get_text()
                processing_status["pages_processed"] = page_num + 1
                processing_status["progress"] = int((page_num + 1) / len(doc) * 30)
                time.sleep(0.1)  # Small delay for UI updates
        
        processing_status.update({
            "current_step": "Chunking text",
            "progress": 40
        })
        
        # Chunk the text
        chunks = semantic_chunking(text_content)
        
        processing_status.update({
            "current_step": "Creating embeddings",
            "progress": 60
        })
        
        # Create embeddings
        embeddings = embedder.encode(chunks).tolist()
        
        processing_status.update({
            "current_step": "Storing in database",
            "progress": 80
        })
        
        # Store in ChromaDB
        ids = [f"chunk_{int(time.time())}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": os.path.basename(pdf_path),
                "chunk_id": i,
                "timestamp": datetime.now().isoformat()
            }
            for i in range(len(chunks))
        ]
        
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        processing_status.update({
            "is_processing": False,
            "progress": 100,
            "current_step": "Complete"
        })
        
    except Exception as e:
        processing_status.update({
            "is_processing": False,
            "error": str(e),
            "progress": 0
        })

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and processing"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    pdf_path = os.path.join(upload_dir, file.filename)
    file.save(pdf_path)
    
    # Start background processing
    thread = threading.Thread(target=process_pdf_background, args=(pdf_path,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "File uploaded successfully", "filename": file.filename})

@app.route('/api/status')
def get_status():
    """Get processing status"""
    return jsonify(processing_status)

@app.route('/api/query', methods=['POST'])
def query_books():
    """Query ChromaDB"""
    if not collection or not embedder:
        return jsonify({"error": "Database not available"}), 500
    
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Create embedding for query
        query_embedding = embedder.encode(query).tolist()
        
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        # Format results
        response = {
            "query": query,
            "answer": generate_answer(query, results["documents"][0]),
            "references": [],
            "confidence": calculate_confidence(results)
        }
        
        # Add references
        for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            response["references"].append({
                "source": metadata.get("source", "Unknown"),
                "snippet": doc[:200] + "..." if len(doc) > 200 else doc,
                "chunk_id": metadata.get("chunk_id", i)
            })
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_answer(query, documents):
    """Generate a simple answer from retrieved documents"""
    if not documents:
        return "I couldn't find relevant information in books."
    
    # Simple answer generation - in production, use an LLM here
    best_doc = documents[0]
    return f"Based on biology books: {best_doc[:300]}..." if len(best_doc) > 300 else best_doc

def calculate_confidence(results):
    """Calculate confidence score based on similarity scores"""
    # This is a simplified confidence calculation
    # In production, use actual similarity scores from ChromaDB
    num_results = len(results["documents"][0]) if results["documents"] else 0
    
    if num_results >= 3:
        return 92
    elif num_results >= 2:
        return 78
    elif num_results >= 1:
        return 65
    else:
        return 20

@app.route('/api/books')
def get_books():
    """Get list of processed books"""
    if not collection:
        return jsonify({"books": []})
    
    try:
        # Get unique sources from metadata
        results = collection.get(include=["metadatas"])
        sources = set()
        
        for metadata in results["metadatas"]:
            if metadata and "source" in metadata:
                sources.add(metadata["source"])
        
        return jsonify({"books": list(sources)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
