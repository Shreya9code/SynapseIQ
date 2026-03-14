from duckduckgo_search import DDGS
from typing import List, Dict
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def search_web(query: str, max_results: int = 5) -> List[Dict]:
    """Search the general web for news, blogs, or non-arxiv sources."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
        formatted = [
            {"title": r['title'], "url": r['href'], "snippet": r['body']} 
            for r in results
        ]
        logger.info(f"Found {len(formatted)} web results for '{query}'")
        return formatted
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []