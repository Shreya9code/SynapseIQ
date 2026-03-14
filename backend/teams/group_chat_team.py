import autogen
from typing import Dict, Any
from backend.agents.research import (
    create_searcher_agent,
    create_summarizer_agent,
    create_critic_agent,
    create_writer_agent,
    create_validator_agent,
    create_trend_analyzer_agent
)
from backend.config import get_llm_config
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def create_group_chat_team():
    """
    Creates a GroupChat where all agents collaborate and debate.
    Best for: Complex research requiring multiple perspectives.
    """
    # Create all agents
    searcher = create_searcher_agent()
    summarizer = create_summarizer_agent()
    trend_analyzer = create_trend_analyzer_agent()
    critic = create_critic_agent()
    writer = create_writer_agent()
    validator = create_validator_agent()
    
    # Create Group Chat Manager (Orchestrator)
    manager = autogen.GroupChatManager(
        name="ResearchManager",
        system_message="""You are the Research Manager.
        Coordinate the team to complete research tasks efficiently.
        1. Start with Searcher to find papers.
        2. Pass to Summarizer for content extraction.
        3. Use TrendAnalyzer for pattern discovery.
        4. Let Writer draft the report.
        5. Have Critic and Validator review.
        6. End when report is finalized.
        Say TERMINATE when the task is complete.""",
        llm_config={"config_list": get_llm_config()},
        human_input_mode="NEVER",
    )
    
    # Create Group Chat
    group_chat = autogen.GroupChat(
        agents=[searcher, summarizer, trend_analyzer, critic, writer, validator],
        messages=[],
        max_round=20,
        speaker_selection_method="round_robin",  # Or "auto" for LLM-based selection
    )
    
    # Attach group chat to manager
    manager.group_chat = group_chat
    
    # Create User Proxy
    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
    )
    
    def run_research_task(query: str) -> Dict[str, Any]:
        logger.info(f"Starting group chat research for: {query}")
        
        # Initiate group chat
        user_proxy.initiate_chat(
            manager,
            message=f"""Research Task: {query}
            
            Please coordinate the team to:
            1. Find relevant papers
            2. Summarize key findings
            3. Identify trends
            4. Write a comprehensive report
            5. Validate all claims
            
            End with TERMINATE when complete.""",
            max_turns=25
        )
        
        # Extract final report from chat history
        messages = manager.group_chat.messages
        final_report = ""
        for msg in reversed(messages):
            if msg.get("name") == "Writer" or msg.get("name") == "Validator":
                final_report = msg.get("content", "")
                break
        
        return {
            "status": "complete",
            "report": final_report,
            "workflow": "group_chat",
            "chat_history": messages
        }
    
    return {
        "user_proxy": user_proxy,
        "manager": manager,
        "group_chat": group_chat,
        "agents": [searcher, summarizer, trend_analyzer, critic, writer, validator],
        "run": run_research_task
    }