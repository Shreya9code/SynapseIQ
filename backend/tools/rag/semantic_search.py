# backend/tools/rag/semantic_search.py
from typing import List, Dict, Optional
from backend.tools.rag.embedding_generator import generate_embeddings
from backend.database.vector_store import vector_store
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def search_similar(
    query: str,
    limit: int = 5,
    score_threshold: float = 0.0,
    filter_metadata: Optional[Dict] = None
) -> List[Dict]:
    """
    Search for semantically similar document chunks.
    Args:
        query: Search query text
        limit: Max number of results to return
        score_threshold: Minimum similarity score (0.0 to 1.0)
        filter_metadata: Optional filters (e.g., {"page": 5}, {"filename": "paper.pdf"})
    Returns:
        List of results with text, score, page, and metadata
    """
    try:
        # Step 1: Generate embedding for query
        query_embedding = generate_embeddings([query])[0]
        
        # Step 2: Search vector store
        results = vector_store.search(
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            filter_metadata=filter_metadata
        )
        
        logger.info(f"Found {len(results)} results for query: '{query[:50]}...'")
        
        return results
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []

def search_by_page(
    query: str,
    filename: str,
    page: int,
    limit: int = 3
) -> List[Dict]:
    """
    Search within a specific page of a specific document.
    Args:
        query: Search query
        filename: Document filename to filter by
        page: Page number (1-indexed)
        limit: Max results
    Returns:
        Filtered search results
    """
    try:
        return search_similar(
            query=query,
            limit=limit,
            filter_metadata={
                "filename": filename,
                "page": page
            }
        )
    except Exception as e:
        logger.error(f"Page-specific search failed: {e}")
        return []

def search_by_document(
    query: str,
    filename: str,
    limit: int = 5
) -> List[Dict]:
    """
    Search within a specific document only.
    Args:
        query: Search query
        filename: Document filename to filter by
        limit: Max results
    Returns:
        Document-filtered search results
    """
    try:
        return search_similar(
            query=query,
            limit=limit,
            filter_metadata={"filename": filename}
        )
    except Exception as e:
        logger.error(f"Document-specific search failed: {e}")
        return []

def hybrid_search(
    query: str,
    keyword_boost: float = 0.3,
    limit: int = 5
) -> List[Dict]:
    """
    Hybrid search: combine semantic + keyword matching.
    Args:
        query: Search query
        keyword_boost: Weight for keyword matching (0.0 to 1.0)
        limit: Max results
    Returns:
        Re-ranked results combining both signals
    """
    try:
        # Get semantic results
        semantic_results = search_similar(query, limit=limit * 2)
        
        # Simple keyword scoring (u can enhance with BM25)
        query_terms = query.lower().split()
        
        for result in semantic_results:
            text_lower = result["text"].lower()
            matches = sum(text_lower.count(term) for term in query_terms)
            keyword_score = matches / max(len(text_lower.split()), 1)
            result["hybrid_score"] = (
                (1 - keyword_boost) * result["score"] + 
                keyword_boost * keyword_score
            )
        
        # Re-rank by hybrid score
        ranked = sorted(semantic_results, key=lambda x: x.get("hybrid_score", x["score"]), reverse=True)
        
        logger.info(f"Hybrid search returned {len(ranked[:limit])} results")
        return ranked[:limit]
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return search_similar(query, limit=limit)  # Fallback to semantic only