
import re
from typing import List, Dict, Tuple
from enum import Enum

class ChunkType(Enum):
    CONCEPT = "concept"
    QUESTION = "question"
    APPLICATION = "application"

def fixed_chunk(text, size=300, overlap=80):
    chunks=[]
    start=0
    while start < len(text):
        end = start+size
        chunks.append(text[start:end])
        start = end-overlap
    return chunks

def paragraph_chunk(text):
    return [p.strip() for p in text.split("\n\n") if len(p)>100]

def sentence_chunk(text):
    s = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for sentence in s:
        if len(current)+len(sentence) < 400:
            current += " "+sentence
        else:
            chunks.append(current.strip())
            current = sentence
    chunks.append(current.strip())
    return chunks

def classify_chunk_type(chunk: str) -> ChunkType:
    """
    Classify a text chunk as Concept, Question, or Application
    
    Args:
        chunk: Text chunk to classify
        
    Returns:
        ChunkType enum value
    """
    chunk_lower = chunk.lower()
    
    # Question indicators
    question_patterns = [
        r'\b(what|how|why|when|where|which|who)\b',
        r'\?\s*$',
        r'\b(explain|describe|define|compare|contrast|analyze)\b',
        r'\b(can you|could you|would you)\b'
    ]
    
    # Application indicators
    application_patterns = [
        r'\b(solve|calculate|determine|find|show|demonstrate)\b',
        r'\b(example|problem|exercise|activity|experiment)\b',
        r'\b(approach|method|technique|procedure)\b',
        r'\b(practical|real world|clinical|laboratory)\b'
    ]
    
    # Check for question patterns
    for pattern in question_patterns:
        if re.search(pattern, chunk_lower):
            return ChunkType.QUESTION
    
    # Check for application patterns
    for pattern in application_patterns:
        if re.search(pattern, chunk_lower):
            return ChunkType.APPLICATION
    
    # Default to concept
    return ChunkType.CONCEPT

def intelligent_chunking(text: str, chunk_size: int = 400) -> List[Dict[str, any]]:
    """
    Intelligent chunking that classifies chunks by type
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk
        
    Returns:
        List of chunks with metadata including type classification
    """
    # Start with sentence-based chunking for better semantic boundaries
    sentence_chunks = sentence_chunk(text)
    
    enhanced_chunks = []
    
    for i, chunk in enumerate(sentence_chunks):
        if len(chunk.strip()) < 50:  # Skip very short chunks
            continue
            
        chunk_type = classify_chunk_type(chunk)
        
        # Extract biology keywords for better context
        keywords = extract_biology_keywords(chunk)
        
        enhanced_chunks.append({
            'text': chunk.strip(),
            'type': chunk_type.value,
            'chunk_id': f"chunk_{i}",
            'char_count': len(chunk),
            'keywords': keywords,
            'position': i
        })
    
    return enhanced_chunks

def extract_biology_keywords(text: str) -> List[str]:
    """
    Extract biology-related keywords from text chunk
    
    Args:
        text: Text chunk
        
    Returns:
        List of biology keywords
    """
    biology_terms = [
        'cell', 'tissue', 'organ', 'organism', 'dna', 'rna', 'protein', 'enzyme',
        'metabolism', 'photosynthesis', 'respiration', 'mitosis', 'meiosis',
        'evolution', 'ecosystem', 'membrane', 'nucleus', 'mitochondria',
        'chloroplast', 'ribosome', 'genetics', 'heredity', 'mutation',
        'adaptation', 'classification', 'taxonomy', 'species', 'genus',
        'kingdom', 'phylum', 'class', 'order', 'family', 'bacteria',
        'virus', 'fungi', 'plant', 'animal', 'human', 'physiology',
        'anatomy', 'biochemistry', 'molecular', 'cellular', 'ecological'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for term in biology_terms:
        if term in text_lower:
            found_keywords.append(term)
    
    return found_keywords

def create_metadata_for_chunk(chunk_data: Dict[str, any], source_info: Dict[str, any]) -> Dict[str, any]:
    """
    Create comprehensive metadata for a chunk
    
    Args:
        chunk_data: Chunk information including text and classification
        source_info: Source document information
        
    Returns:
        Metadata dictionary for ChromaDB
    """
    return {
        'source': source_info.get('title', 'Unknown'),
        'author': source_info.get('author', 'Unknown'),
        'file_path': source_info.get('file_path', ''),
        'chunk_type': chunk_data['type'],
        'chunk_id': chunk_data['chunk_id'],
        'char_count': chunk_data['char_count'],
        'keywords': ', '.join(chunk_data['keywords']) if chunk_data['keywords'] else '',
        'position': chunk_data['position'],
        'total_chunks': source_info.get('total_chunks', 0)
    }
