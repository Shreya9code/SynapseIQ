import fitz  # PyMuPDF
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def save_pdf(file, filename: str) -> str:
    """
    Save uploaded PDF file to upload directory.
    Args:
        file: UploadFile object from FastAPI
        filename: Original filename
    Returns:
        str: Path to saved file
    """
    try:
        upload_dir = Path(settings.DATA_DIR) / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved PDF to {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to save PDF: {e}")
        raise e

def parse_pdf(file_path: str) -> Dict:
    """
    Extract text and metadata from PDF.
    Args:
        file_path: Path to PDF file
    Returns:
        Dict with text, pages, and metadata
    """
    try:
        doc = fitz.open(file_path)
        
        text = ""
        pages = []
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            text += page_text + "\n"
            
            pages.append({
                "page": page_num + 1,
                "text": page_text,
                "blocks": len(page.get_text("blocks"))
            })
        
        metadata = doc.metadata
        doc.close()
        
        logger.info(f"Extracted {len(text)} chars from {len(pages)} pages")
        
        return {
            "success": True,
            "text": text,
            "pages": pages,
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "pages": len(pages),
                "file_path": file_path,
                "filename": Path(file_path).name
            }
        }
    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        return {"success": False, "error": str(e)}

def process_pdf(file, filename: str) -> Dict:
    """
    Complete PDF processing: save + parse.
    Args:
        file: UploadFile object from FastAPI
        filename: Original filename
    Returns:
        Dict with file path, text, pages, and metadata
    """
    try:
        # Step 1: Save file
        file_path = save_pdf(file, filename)
        
        # Step 2: Parse PDF
        result = parse_pdf(file_path)
        
        if result["success"]:
            result["file_path"] = file_path
            logger.info(f"Successfully processed PDF: {filename}")
        else:
            logger.error(f"PDF processing failed: {result.get('error')}")
        
        return result
    except Exception as e:
        logger.error(f"PDF processing failed: {e}")
        return {"success": False, "error": str(e)}

def extract_text_from_pdf(file_path: str, pages: Optional[List[int]] = None) -> str:
    """
    Extract text from specific pages of a PDF.
    Args:
        file_path: Path to PDF file
        pages: List of page numbers to extract (1-indexed). If None, extract all.
    Returns:
        str: Extracted text
    """
    try:
        doc = fitz.open(file_path)
        text = ""
        
        for page_num in range(len(doc)):
            if pages is None or (page_num + 1) in pages:
                page = doc[page_num]
                text += page.get_text() + "\n"
        
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return ""