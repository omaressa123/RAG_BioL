"""
Basic test without external dependencies to verify chunking logic
"""

import re
from typing import List

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_into_sentence(text: str) -> List[str]:
    sentence_endings = r'(?<=[.!?]) +'
    sentences = re.split(sentence_endings, text)
    return [s.strip() for s in sentences if len(s.strip()) > 0]

def paragraph_based_chunking(text: str, max_size: int = 500) -> List[str]:
    paragraphs = text.split("\n")
    chunks = []
    for para in paragraphs:
        para = clean_text(para)
        if not para:
            continue
        if len(para) <= max_size:
            chunks.append(para)
        else:
            # For long paragraphs, split by sentences
            sentences = split_into_sentence(para)
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= max_size:
                    current_chunk += " " + sentence if current_chunk else sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
            if current_chunk:
                chunks.append(current_chunk.strip())
    return chunks

# Test with sample biology text
sample_text = """Biology: The Study of Life

Biology is the scientific study of life and living organisms. It encompasses a vast range of topics, from the molecular mechanisms within cells to the complex interactions of ecosystems.

The Cell: Basic Unit of Life

All living organisms are composed of cells, which are the basic structural and functional units of life. There are two main types of cells: prokaryotic cells and eukaryotic cells.

Cellular Organelles and Their Functions

Within eukaryotic cells, various organelles perform specific functions. The nucleus contains the genetic material (DNA) and controls cellular activities. Mitochondria are often called the "powerhouses" of the cell because they generate most of the cell's supply of ATP."""

if __name__ == "__main__":
    print("🧪 Testing basic chunking functionality...")
    
    chunks = paragraph_based_chunking(sample_text)
    
    print(f"\n📦 Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ({len(chunk)} chars) ---")
        print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
    
    print(f"\n✅ Basic chunking test completed successfully!")
