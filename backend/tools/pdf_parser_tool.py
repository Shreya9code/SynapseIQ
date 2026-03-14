from pypdf import PdfReader
import requests
import io
from typing import Optional
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def download_and_parse_pdf(url: str) -> Optional[str]:
    """Download a PDF from URL and extract text."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        pdf_file = io.BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        logger.info(f"Successfully parsed PDF from {url}")
        return text[:10000] # Limit tokens for context window safety
    except Exception as e:
        logger.error(f"PDF parsing failed for {url}: {e}")
        return None