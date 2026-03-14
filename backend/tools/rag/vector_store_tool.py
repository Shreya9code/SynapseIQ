# backend/tools/rag/vector_store_tool.py
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class VectorStore:
    """Qdrant-backed vector store for document chunks."""
    
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            prefer_grpc=True  # Faster than HTTP
        )
        self.collection_name = "document_chunks"
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        
    def create_collection(self, recreate: bool = False) -> bool:
        """Create collection if it doesn't exist."""
        try:
            # Check if exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name in collection_names:
                if recreate:
                    self.client.delete_collection(self.collection_name)
                    logger.info(f"Deleted existing collection: {self.collection_name}")
                else:
                    logger.info(f"Collection already exists: {self.collection_name}")
                    return True
            
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE  # for text embeddings
                ),
                optimizers_config=models.OptimizersConfigDiff(
                    default_segment_number=2,
                    indexing_threshold=20000
                ),
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100
                )
            )
            
            logger.info(f"✓ Created collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Collection creation failed: {e}")
            return False
    
    def add_documents(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
        metadata: Dict
    ) -> bool:
        """
        Add document chunks to vector store.
        
        Args:
            chunks: List of chunk dicts with 'text', 'chunk_id', 'page', etc.
            embeddings: List of embedding vectors (same length as chunks)
            metadata: Document-level metadata (filename, title, author, etc.)
        
        Returns:
            bool: Success status
        """
        try:
            if len(chunks) != len(embeddings):
                raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) length mismatch")
            
            points = []
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                # Build payload with chunk + document metadata
                payload = {
                    "text": chunk["text"],
                    "chunk_id": chunk.get("chunk_id", i),
                    "page": chunk.get("page", 0),
                    "start_char": chunk.get("start_char", 0),
                    "end_char": chunk.get("end_char", 0),
                    # Document metadata
                    "filename": metadata.get("filename", ""),
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "file_path": metadata.get("file_path", ""),
                }
                
                # Generate unique point ID
                point_id = f"{metadata.get('filename', 'unknown')}_{chunk.get('chunk_id', i)}"
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=emb,
                        payload=payload
                    )
                )
            
            # Upsert in batches (Qdrant handles this efficiently)
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
            )
            logger.info(f"✓ Added {len(points)} chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.0,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query vector
            limit: Max results
            score_threshold: Minimum cosine similarity (0.0 to 1.0)
            filter_metadata: Optional filters like {"filename": "paper.pdf", "page": 5}
        
        Returns:
            List of results with text, score, and metadata
        """
        try:
            # Build filter if provided
            search_filter = None
            if filter_metadata:
                must_conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filter_metadata.items()
                ]
                search_filter = Filter(must=must_conditions)
            
            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold if score_threshold > 0 else None,
                with_payload=True,
                with_vectors=False  # Don't return full vectors (saves bandwidth)
            )
            
            # Format results
            formatted = [
                {
                    "text": r.payload.get("text", ""),
                    "score": float(r.score),  # Cosine similarity
                    "page": r.payload.get("page", 0),
                    "chunk_id": r.payload.get("chunk_id", 0),
                    "filename": r.payload.get("filename", ""),
                    "title": r.payload.get("title", ""),
                    "start_char": r.payload.get("start_char", 0),
                    "end_char": r.payload.get("end_char", 0),
                }
                for r in results
            ]
            
            return formatted
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_by_filename(self, filename: str) -> bool:
        """Delete all chunks from a specific document."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="filename",
                                match=models.MatchValue(value=filename)
                            )
                        ]
                    )
                )
            )
            logger.info(f"✓ Deleted chunks for: {filename}")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def get_document_stats(self, filename: Optional[str] = None) -> Dict:
        """Get stats about stored documents."""
        try:
            if filename:
                # Count chunks for specific document
                points, _ = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="filename",
                                match=models.MatchValue(value=filename)
                            )
                        ]
                    ),
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                count = len(points)
                return {"filename": filename, "chunks": count}
            else:
                # Get collection info
                info = self.client.get_collection(self.collection_name)
                return {
                    "total_points": info.points_count,
                    "vectors_count": info.vectors_count,
                    "embedding_dim": self.embedding_dim
                }
        except Exception as e:
            logger.error(f"Stats query failed: {e}")
            return {"error": str(e)}
    
    def clear_all(self) -> bool:
        """Delete all data (use with caution!)."""
        try:
            self.client.delete_collection(self.collection_name)
            self.create_collection()
            logger.warning("⚠️ Cleared all vector store data")
            return True
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            return False


# Singleton instance
vector_store = VectorStore()