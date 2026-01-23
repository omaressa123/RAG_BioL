
import re
from typing import Dict, List, Tuple
from pypdf import PdfReader

def extract_text_from_pdf(path: str) -> Dict[str, any]:
    """
    Extract text from PDF with preprocessing and metadata
    
    Args:
        path: Path to PDF file
        
    Returns:
        Dict containing extracted text, metadata, and statistics
    """
    try:
        reader = PdfReader(path)
        
        # Extract metadata
        metadata = {
            'title': reader.metadata.get('/Title', 'Unknown') if reader.metadata else 'Unknown',
            'author': reader.metadata.get('/Author', 'Unknown') if reader.metadata else 'Unknown',
            'pages': len(reader.pages),
            'file_path': path
        }
        
        # Extract and clean text from each page
        pages_text = []
        full_text = ""
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                # Clean the text
                cleaned_text = clean_text(page_text)
                pages_text.append({
                    'page_num': i + 1,
                    'text': cleaned_text,
                    'char_count': len(cleaned_text)
                })
                full_text += cleaned_text + "\n\n"
        
        return {
            'text': full_text.strip(),
            'pages': pages_text,
            'metadata': metadata,
            'stats': {
                'total_chars': len(full_text),
                'total_pages': len(reader.pages),
                'pages_with_text': len(pages_text)
            }
        }
        
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def clean_text(text: str) -> str:
    """
    Clean and preprocess extracted text
    
    Args:
        text: Raw text from PDF
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common OCR errors
    text = text.replace('|', 'I')  # Common OCR confusion
    
    # Remove page numbers and headers/footers patterns
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    
    # Clean up punctuation spacing
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    
    # Remove multiple consecutive newlines
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()

def extract_biology_keywords(text: str) -> List[str]:
    """
    Extract biology-related keywords from text
    
    Args:
        text: Input text
        
    Returns:
        List of biology keywords found
    """
    # Common biology terms patterns
    biology_patterns = [
        r'\b(cell|tissue|organ|organism|DNA|RNA|protein|enzyme|metabolism)\b',
        r'\b(photosynthesis|respiration|mitosis|meiosis|evolution|ecosystem)\b',
        r'\b(membrane|nucleus|mitochondria|chloroplast|ribosome)\b',
        r'\b(genetics|heredity|mutation|adaptation|classification|taxonomy)\b'
    ]
    
    keywords = set()
    for pattern in biology_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        keywords.update([match.lower() for match in matches])
    
    return list(keywords)
