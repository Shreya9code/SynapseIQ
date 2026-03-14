import autogen
from backend.agents.base_agent import create_agent
from backend.tools import download_and_parse_pdf

SYSTEM_MESSAGE = """
You are a Research Summarizer.
You receive text content or PDF URLs.
1. If given a URL, use download_and_parse_pdf to get text.
2. Extract: Core Problem, Methodology, Key Findings.
3. Keep summaries concise (max 150 words per paper).
4. Ignore irrelevant marketing fluff.
"""

def create_summarizer_agent() -> autogen.ConversableAgent:
    tools = [download_and_parse_pdf]
    return create_agent("Summarizer", SYSTEM_MESSAGE, tools=tools)