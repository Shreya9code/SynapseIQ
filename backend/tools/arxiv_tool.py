import arxiv
from typing import List, Dict
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def search_arxiv(query: str, max_results: int = 5) -> List[Dict]:
    """Search arXiv for papers based on a query."""
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        results = []
        for result in client.results(search):
            results.append({
                "title": result.title,
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "abstract": result.summary[:500] # Truncate for context
            })
        logger.info(f"Found {len(results)} papers on arXiv for '{query}'")
        return results
    except Exception as e:
        logger.error(f"arXiv search failed: {e}")
        return []