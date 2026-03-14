import autogen
from backend.agents.base_agent import create_agent

SYSTEM_MESSAGE = """
You are a Peer Reviewer Critic.
Your goal is to evaluate the quality of summarized research.
1. Check for logical consistency.
2. Score novelty and methodology (1-10).
3. Flag any hallucinations or unsupported claims.
4. Be strict but constructive.
"""

def create_critic_agent() -> autogen.ConversableAgent:
    # No external tools needed, just LLM reasoning
    return create_agent("Critic", SYSTEM_MESSAGE, tools=[])