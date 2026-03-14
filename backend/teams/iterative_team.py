import autogen
from typing import Dict, Any
from backend.agents.research import (
    create_searcher_agent,
    create_summarizer_agent,
    create_critic_agent,
    create_writer_agent,
    create_validator_agent
)
from backend.config import get_llm_config
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def create_iterative_team():
    """
    Creates an iterative workflow with feedback loops.
    Writer drafts → Critic reviews → Writer revises → Validator approves.
    Best for: High-quality reports requiring multiple refinement cycles.
    """
    # Create agents
    searcher = create_searcher_agent()
    summarizer = create_summarizer_agent()
    critic = create_critic_agent()
    writer = create_writer_agent()
    validator = create_validator_agent()
    
    # User Proxy
    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=15,
        code_execution_config=False,
    )
    
    def run_research_task(query: str, max_iterations: int = 3) -> Dict[str, Any]:
        logger.info(f"Starting iterative research for: {query}")
        
        # Phase 1: Gather & Summarize (one-time)
        user_proxy.initiate_chat(
            searcher,
            message=f"Search for research papers on: {query}",
            max_turns=2
        )
        search_results = searcher.last_message()["content"]
        
        user_proxy.initiate_chat(
            summarizer,
            message=f"Summarize these findings: {search_results}",
            max_turns=2
        )
        summaries = summarizer.last_message()["content"]
        
        # Phase 2: Iterative Write → Critic → Revise loop
        current_draft = summaries
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}/{max_iterations}")
            
            # Write/Revise
            user_proxy.initiate_chat(
                writer,
                message=f"""Write/Revise the research report.
                Current content: {current_draft}
                Improve based on any previous feedback.""",
                max_turns=2
            )
            draft = writer.last_message()["content"]
            
            # Critic Review
            user_proxy.initiate_chat(
                critic,
                message=f"Review this draft for quality and novelty: {draft}",
                max_turns=2
            )
            critique = critic.last_message()["content"]
            
            # Check if critic is satisfied (simple keyword check)
            if "approved" in critique.lower() or "good" in critique.lower():
                logger.info("Critic approved the draft")
                current_draft = draft
                break
            else:
                logger.info("Critic requested revisions")
                current_draft = f"{draft}\n\nCritique to address: {critique}"
        
        # Phase 3: Final Validation
        user_proxy.initiate_chat(
            validator,
            message=f"Final validation of report (citations, facts): {current_draft}",
            max_turns=2
        )
        final_report = validator.last_message()["content"]
        
        return {
            "status": "complete",
            "report": final_report,
            "workflow": "iterative",
            "iterations": iteration
        }
    
    return {
        "user_proxy": user_proxy,
        "agents": [searcher, summarizer, critic, writer, validator],
        "run": run_research_task
    }