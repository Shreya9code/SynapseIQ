from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None
        )
        self.collection_name = "documents"
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        
    def create_collection(self):
        """Create collection if not exists."""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            if "already exists" not in str(e):
                logger.error(f"Collection creation failed: {e}")
    
    def add_documents(self, chunks: List[Dict], embeddings: List[List[float]], meta Dict):
        """Add chunks to vector store."""
        points = []
        
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            points.append(
                PointStruct(
                    id=i,
                    vector=emb,
                    payload={
                        "text": chunk["text"],
                        "chunk_id": chunk["chunk_id"],
                        "document_id": metadata.get("file_path", ""),
                        "page": chunk.get("page", 0),
                        **metadata
                    }
                )
            )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"Added {len(points)} documents to vector store")
    
    def search(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Search for similar documents."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        return [
            {
                "text": r.payload["text"],
                "score": r.score,
                "page": r.payload.get("page", 0),
                "document_id": r.payload.get("document_id", "")
            }
            for r in results
        ]

vector_store = VectorStore()