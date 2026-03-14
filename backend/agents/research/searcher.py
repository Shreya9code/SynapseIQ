import autogen
from backend.agents.base_agent import create_agent
from backend.tools import search_arxiv, search_web

SYSTEM_MESSAGE = """
You are an Academic Search Specialist.
Your goal is to find high-quality research papers and web sources.
1. Use search_arxiv for academic papers.
2. Use search_web for news, blogs, or recent developments.
3. Return ONLY a JSON-like list of findings with Title, URL, and Relevance.
4. Do not summarize content yet. Just find sources.
"""

def create_searcher_agent() -> autogen.ConversableAgent:
    tools = [search_arxiv, search_web]
    return create_agent("Searcher", SYSTEM_MESSAGE, tools=tools)