"""
BioLens Chunking Module

Chunking strategies supported:
1. Fixed-size chunking
2. Sentence-based chunking
3. Paragraph-based chunking
4. Semantic chunking (embedding-based)
5. Agentic chunking (LLM-guided)

Guidelines:
- Chunk size: 200–500 characters
- Overlap: 50–100 characters
- Boundary rules:
  * Split at sentence boundaries
  * Avoid mid-word breaks
- Quality checks:
  * Test with real queries
  * Verify context preservation
  * Monitor retrieval relevance
"""

import re
from typing import List
from sentence_transformers import SentenceTransformer, util

def clean_text(text:str) -> str:
    text= re.sub(r'\s+', ' ', text)
    return text.strip()

def split_into_sentence(text: str) -> List[str]:
    sentence_endings= r'(?<={.!?]) +'
    sentences= re.split(sentence_endings, text)
    return [s.strip() for s in sentences if len(s.strip()) > 0]

def  fixed_size_chunking(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80
) -> List[str]:
    text= clean_text(text)
    chunks= []
    start=0
    text_lenght = len(text)
    while start < text_lenght:
        end = start + chunk_size
        chunks.append(text[start:end])
        if end < text_length and not text[end].isspace():
            last_space = chunck.rfind(" ")
            if last_space != -1:
                chunk = chunk[:last_space]
                end =start + last_space
        chunks.append(chunk.strip())
        start = end - overlap
    return chunks

def sentence_based_chunking(
    text: str,
    min_size: int = 200,
    max_size: int = 400
) -> List[str]:
    text = clean_text(text)
    sentences = split_into_sentences(text)
    chunks=[]
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_size:
            current_chunk += " " + sentence
        else :
            if len(current_chunk) >= min_size:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    if len(current_chunk) >= min_size:
        chunks.append(current_chunk.strip())
    return chunks


def paragraph_based_chunking(
    text: str,
    max_size: int = 500
) -> List[str]:
    paragraph =text.split("\n")
    chunks = []
    for para in paragraph:
        para= clean_text(para)
        if not para:
            continue
        if len(para) <= max_size:
            chunks.append(para)
        else:
            chunks.extend(sentence_based_chunking(para, max_size))
    return chunks


def semantic_chunking(
    text: str,
    model_name: str = "all-MiniLM-L6-v2",
    similarity_threshold: float = 0.75
) -> List[str]:
    """
    Uses embeddings to group semantically similar sentences
    """
    text = clean_text(text)
    sentences = split_into_sentences(text)

    model = SentenceTransformer(model_name)
    embeddings = model.encode(sentences, convert_to_tensor=True)

    chunks = []
    current_chunk = sentences[0]
    current_embedding = embeddings[0]

    for i in range(1, len(sentences)):
        similarity = util.cos_sim(current_embedding, embeddings[i]).item()

        if similarity >= similarity_threshold:
            current_chunk += " " + sentences[i]
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentences[i]
            current_embedding = embeddings[i]

    chunks.append(current_chunk.strip())
    return chunks

def agentic_chunking(
    text: str,
    llm_splitter
) -> List[str]:
    text = clean_text(text)
    chunks = llm_splitter(text)
    final_chunks = []
    for chunk in chunks:
        if 200 <= len(chunk) <= 500:
            final_chunks.append(chunk.strip())

    return final_chunks
#quality

if __name__ == "__main__":
    with open("sample.txt", "r", encoding="utf-8") as f:
        text = f.read()
    chunks = paragraph_based_chunking(text)
    print(chunks)