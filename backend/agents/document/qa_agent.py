# backend/agents/document/qa_agent.py
import autogen
from backend.agents.base_agent import create_agent
from backend.utils.prompt_templates import AGENT_PROMPTS

SYSTEM_MESSAGE = """
You are a Document Q&A Specialist.
Your role is to answer questions about uploaded documents using retrieved context.

Rules:
1. Answer ONLY based on the provided context - do not use outside knowledge
2. Cite page numbers like [p.5] when referencing specific information
3. If the answer isn't in the context, clearly state: "I couldn't find this in the uploaded documents"
4. Be concise but complete - prefer bullet points for lists
5. Flag any ambiguous or conflicting information in the source

Tone: Professional, helpful, precise
"""

def create_qa_agent() -> autogen.ConversableAgent:
    """Create the Q&A agent for document queries."""
    return create_agent(
        name="DocumentQA",
        system_message=SYSTEM_MESSAGE,
        tools=[]  # No external tools - works with retrieved context only
    )