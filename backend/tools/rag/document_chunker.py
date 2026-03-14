from typing import List, Dict
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def chunk_document(text: str,page:int, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """Split document into overlapping chunks."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind(".", start, end)
            last_newline = text.rfind("\n", start, end)
            
            if last_period > start + chunk_size // 2:
                end = last_period + 1
            elif last_newline > start + chunk_size // 2:
                end = last_newline + 1
        
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunks.append({
                "chunk_id": len(chunks),
                "text": chunk_text,
                "page": page, 
                "start_char": start,
                "end_char": end,
                "length": len(chunk_text)
            })
        
        start = end - overlap
    
    logger.info(f"Created {len(chunks)} chunks from {len(text)} chars")
    return chunks