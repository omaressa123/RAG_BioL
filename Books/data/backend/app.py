
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import sys
from pathlib import Path

# Add the rag module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag'))

from rag.chroma_store import get_store
from rag.chunking import intelligent_chunking, create_metadata_for_chunk
from ocr.pdf_ocr import extract_text_from_pdf

# Get absolute paths
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / 'frontend'
STATIC_DIR = FRONTEND_DIR / 'static'

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='/static')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    """Serve the frontend"""
    return send_from_directory(str(FRONTEND_DIR), 'index.html')

@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files"""
    return send_from_directory(str(STATIC_DIR), filename)

@app.route("/upload", methods=["POST"])
def upload_pdf():
    """
    Upload and process a PDF file
    
    Expected: multipart/form-data with file field named 'pdf'
    Returns: JSON with processing status and statistics
    """
    try:
        # Check if file is in request
        if 'pdf' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['pdf']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF files are allowed"}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process PDF through the pipeline
        result = process_pdf_pipeline(filepath)
        
        if result["success"]:
            return jsonify({
                "message": "PDF processed successfully",
                "stats": result["stats"],
                "chunks_created": result["chunks_created"]
            }), 200
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    """
    Ask a question and get semantic search results
    
    Expected: JSON with 'question' field
    Optional: 'chunk_type' filter ('concept', 'question', 'application')
    Returns: JSON with answers, sources, and confidence scores
    """
    try:
        data = request.get_json()
        
        if not data or "question" not in data:
            return jsonify({"error": "Question is required"}), 400
        
        question = data["question"]
        chunk_type = data.get("chunk_type", None)
        n_results = data.get("n_results", 5)
        
        # Perform semantic search
        store = get_store()
        results = store.semantic_search(
            query=question,
            n_results=n_results,
            chunk_type_filter=chunk_type
        )
        
        # Format response
        response = {
            "question": question,
            "answers": results["documents"][0] if results["documents"] else [],
            "sources": results["metadatas"][0] if results["metadatas"] else [],
            "confidence_scores": results["confidence"][0] if results["confidence"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

@app.route("/stats", methods=["GET"])
def get_stats():
    """
    Get collection statistics
    
    Returns: JSON with collection stats
    """
    try:
        store = get_store()
        stats = store.get_collection_stats()
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get stats: {str(e)}"}), 500

@app.route("/clear", methods=["DELETE"])
def clear_collection():
    """
    Clear the entire collection
    
    Returns: JSON with operation status
    """
    try:
        store = get_store()
        success = store.delete_collection()
        
        if success:
            # Recreate empty collection
            store.__init__()
            return jsonify({"message": "Collection cleared successfully"}), 200
        else:
            return jsonify({"error": "Failed to clear collection"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Clear operation failed: {str(e)}"}), 500

def process_pdf_pipeline(filepath: str) -> dict:
    """
    Process a PDF through the complete pipeline:
    OCR -> Chunking -> Vector DB Storage
    
    Args:
        filepath: Path to PDF file
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Step 1: OCR - Extract text from PDF
        print(f"Extracting text from {filepath}...")
        pdf_data = extract_text_from_pdf(filepath)
        
        if not pdf_data["text"].strip():
            return {"success": False, "error": "No text could be extracted from PDF"}
        
        # Step 2: Chunking - Classify and chunk the text
        print("Chunking and classifying text...")
        chunks_data = intelligent_chunking(pdf_data["text"])
        
        if not chunks_data:
            return {"success": False, "error": "No chunks were created"}
        
        # Step 3: Create metadata for each chunk
        source_info = {
            "title": pdf_data["metadata"]["title"],
            "author": pdf_data["metadata"]["author"],
            "file_path": filepath,
            "total_chunks": len(chunks_data)
        }
        
        chunks_text = []
        chunks_metadata = []
        
        for chunk_data in chunks_data:
            chunks_text.append(chunk_data["text"])
            chunks_metadata.append(create_metadata_for_chunk(chunk_data, source_info))
        
        # Step 4: Store in Chroma Vector DB
        print("Storing chunks in vector database...")
        store = get_store()
        success = store.store_chunks(chunks_text, chunks_metadata)
        
        if not success:
            return {"success": False, "error": "Failed to store chunks in database"}
        
        # Return success with statistics
        return {
            "success": True,
            "stats": pdf_data["stats"],
            "chunks_created": len(chunks_data),
            "chunk_types": {
                chunk_type: sum(1 for c in chunks_data if c["type"] == chunk_type)
                for chunk_type in ["concept", "question", "application"]
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Pipeline processing failed: {str(e)}"}

if __name__ == "__main__":
    print("Starting BioLens RAG System...")
    print("Available endpoints:")
    print("  GET  /           - Frontend")
    print("  POST /upload    - Upload PDF")
    print("  POST /ask       - Ask question")
    print("  GET  /stats     - Collection stats")
    print("  DELETE /clear   - Clear collection")
    app.run(debug=True, port=5000)
