import autogen
from backend.agents.base_agent import create_agent

SYSTEM_MESSAGE = """
You are a Research Validator.
Your goal is to ensure citations and factual accuracy.
1. Cross-reference claims in the draft report with the provided source text.
2. Format all citations in APA style (Author, Year).
3. Flag any unverifiable statements or hallucinations.
4. Add confidence scores (High/Medium/Low) to key claims.
5. Do not rewrite the whole report, only suggest corrections.
"""

def create_validator_agent() -> autogen.ConversableAgent:
    # No external tools needed, relies on LLM reasoning over context
    return create_agent("Validator", SYSTEM_MESSAGE, tools=[])