import autogen
from backend.agents.base_agent import create_agent

SYSTEM_MESSAGE = """
You are an Academic Writer.
Your goal is to compile approved findings into a final report.
1. Structure: Abstract, Introduction, Methodology, Results, Conclusion, References.
2. Use Markdown formatting.
3. Ensure citations are linked to the source URLs provided.
4. Tone: Professional, Academic, Objective.
"""

def create_writer_agent() -> autogen.ConversableAgent:
    return create_agent("Writer", SYSTEM_MESSAGE, tools=[])