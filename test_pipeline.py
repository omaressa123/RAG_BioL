"""
Test pipeline for chunking and storing data without external dependencies
"""

import os
import glob
import json
from test_chunking_basic import paragraph_based_chunking

def load_text_files(data_folder="data"):
    """Load all text files from the data folder"""
    all_text = ""
    processed_files = []
    
    # Get all text files in the data folder
    text_files = glob.glob(os.path.join(data_folder, "*.txt"))
    
    if not text_files:
        print(f"❌ No text files found in {data_folder} folder")
        return None, []
    
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
        return None, []
    
    print(f"\n📄 Total combined text length: {len(all_text)} characters")
    return all_text, processed_files

def store_chunks_locally(chunks, processed_files, output_file="chunks.json"):
    """Store chunks in a JSON file for testing"""
    chunk_data = {
        "metadata": {
            "total_chunks": len(chunks),
            "processed_files": processed_files,
            "total_files": len(processed_files)
        },
        "chunks": []
    }
    
    for i, chunk in enumerate(chunks):
        chunk_data["chunks"].append({
            "id": f"chunk_{i}",
            "content": chunk,
            "metadata": {
                "source": "biology_books",
                "chunk_id": i,
                "length": len(chunk)
            }
        })
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunk_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Chunks stored in {output_file}")
    return chunk_data

def simulate_query(chunks, query, top_k=3):
    """Simple keyword-based query simulation"""
    query_words = query.lower().split()
    scored_chunks = []
    
    for i, chunk in enumerate(chunks):
        chunk_lower = chunk.lower()
        score = 0
        
        # Simple scoring: count query word matches
        for word in query_words:
            score += chunk_lower.count(word) * len(word)
        
        if score > 0:
            scored_chunks.append((i, chunk, score))
    
    # Sort by score and return top_k
    scored_chunks.sort(key=lambda x: x[2], reverse=True)
    return scored_chunks[:top_k]

if __name__ == "__main__":
    print("🚀 Testing complete chunking and storage pipeline...")
    
    # Load text files
    all_text, processed_files = load_text_files()
    
    if all_text:
        # Chunk the text
        print("\n🔪 Chunking text...")
        chunks = paragraph_based_chunking(all_text)
        print(f"✅ Created {len(chunks)} chunks")
        
        # Store chunks
        print("\n💾 Storing chunks...")
        chunk_data = store_chunks_locally(chunks, processed_files)
        
        # Test queries
        print("\n🔍 Testing queries...")
        test_queries = [
            "What is the function of mitochondria?",
            "How does photosynthesis work?",
            "What are the types of cells?",
            "Explain DNA structure"
        ]
        
        for query in test_queries:
            print(f"\n❓ Query: {query}")
            results = simulate_query(chunks, query)
            
            if results:
                for i, (chunk_idx, chunk, score) in enumerate(results):
                    print(f"  Result {i+1} (Score: {score}): {chunk[:100]}...")
            else:
                print("  No relevant chunks found")
        
        print(f"\n🎉 Pipeline test completed successfully!")
        print(f"📊 Summary: {len(chunks)} chunks from {len(processed_files)} files")
    else:
        print("❌ Pipeline test failed - no text content")
