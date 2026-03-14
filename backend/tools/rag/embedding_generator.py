from sentence_transformers import SentenceTransformer
from typing import List
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Load model once at startup
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for text chunks."""
    try:
        model = get_embedding_model()
        embeddings = model.encode(texts,batch_size=32, show_progress_bar=True)
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return []