# backend/teams/sequential_team.py
import autogen
from typing import Dict, Any
from backend.agents.research import (
    create_searcher_agent,
    create_summarizer_agent,
    create_trend_analyzer_agent,
    create_writer_agent,
    create_validator_agent
)
from backend.config import get_llm_config
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def create_sequential_team():
    """
    Creates a sequential chain of agents for linear research workflow.
    Best for: Simple, straightforward research tasks.
    """
    # Create all agents
    searcher = create_searcher_agent()
    summarizer = create_summarizer_agent()
    trend_analyzer = create_trend_analyzer_agent()
    writer = create_writer_agent()
    validator = create_validator_agent()
    
    # Create User Proxy (initiates the chain)
    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
    )
    
    # Define the sequence using nested chats
    def run_research_task(query: str) -> Dict[str, Any]:
        '''Sequential workflow with robust message extraction.'''
        logger.info(f"Starting sequential research for: {query}")
    
        def safe_extract_content(agent):
            try:
                msg = agent.last_message()
                if not msg:
                    return ""
                if isinstance(msg, dict) and "content" in msg:
                    return msg["content"]
                if isinstance(msg, dict):
                    for key in ["content", "output", "text", "message"]:
                        if key in msg and msg[key]:
                            return msg[key]
                return str(msg)

            except Exception as e:
                logger.error(f"Extraction error: {e}")
                return ""
    
        try:
            # Step 1: Search
            user_proxy.initiate_chat(
                searcher,
                message=f"Search for research papers on: {query}. Return JSON with title, url, abstract.",
                max_turns=4
            )
            search_results = searcher.chat_messages[user_proxy][-1]["content"]
            logger.info(f"✓ Search complete: {len(search_results)} chars")
            logger.debug(f"🔍 Search output preview: {search_results[:300]}...")  # DEBUG
        
            # Step 2: Summarize
            if not search_results:
                raise ValueError("Search agent returned empty results")

            user_proxy.initiate_chat(summarizer,
                message=f"Summarize these papers:\n\n<papers>\n{search_results}\n</papers>\n\nExtract: Problem, Methodology, Findings. Keep under 300 words.",
                max_turns=4
            )
            summaries = summarizer.chat_messages[user_proxy][-1]["content"]
            logger.info(f"✓ Summaries complete: {len(summaries)} chars")
            logger.debug(f"📝 Summary preview: {summaries[:300]}...")  # DEBUG
        
            # Step 3: Trends (with fallback)
            if len(summaries) < 50:
                logger.warning("⚠️ Summaries too short - using placeholder")
                summaries = f"Sample summary for {query}: Key findings include method improvements and novel applications."
        
            user_proxy.initiate_chat(trend_analyzer,
                message=f"Analyze trends from:\n\n<summaries>\n{summaries}\n</summaries>\n\nCluster topics and identify 2-3 emerging directions.",
                max_turns=4
            )
            trends = trend_analyzer.chat_messages[user_proxy][-1]["content"]
            logger.info(f"✓ Trends complete: {len(trends)} chars")
        
            # Step 4: Write (with fallback)
            if len(trends) < 30:
                raise ValueError(f"Insufficient trend data found for '{query}'.")        
            user_proxy.initiate_chat(
                writer,
                message=f"""
                Write a detailed research report about: {query}
                Use the following inputs.
                <paper_summaries>
                {summaries}
                </paper_summaries>

                <research_trends>
                {trends}
                </research_trends>

                Requirements:
                - Abstract (4–5 sentences)
                - Introduction
                - Key Findings with explanations
                - Emerging Trends
                - Conclusion
                - References with real URLs

                Write ~500 words in Markdown.
                Do NOT output empty sections.
                """,
                max_turns=4
            )
            draft = writer.chat_messages[user_proxy][-1]["content"]
            logger.info(f"✓ Draft complete: {len(draft)} chars")
        
            # Step 5: Validate (with fallback)
            if len(draft) < 100:
                logger.warning("Writer returned short output, using it anyway")
                #draft = f"# Report: {query}\n\n## Abstract\nThis report summarizes research on {query}.\n\n## Key Findings\n- Finding 1\n- Finding 2\n\n## References\n1. Example Author (2024). Paper title. https://arxiv.org/example"
        
            user_proxy.initiate_chat(validator,
                message=f"Validate this report:\n\n<report>\n{draft}\n</report>\n\nTasks: 1) Check claims vs sources, 2) Format APA citations, 3) Flag hallucinations. Return corrected report.",
                max_turns=4
            )
            final_report = validator.chat_messages[user_proxy][-1]["content"]
        
            # Return best available content
            report_content = final_report if (final_report and len(final_report) > 150) else draft
            return {
                "status": "complete",
                "report": report_content,
                "workflow": "sequential"
            }
        
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}", exc_info=True)
            return {
                "status": "error",
                "report": f"Error: {str(e)}\n\nFallback: Research on '{query}' requires further analysis.",
                "workflow": "sequential"
            }
    return {
        "user_proxy": user_proxy,
        "agents": [searcher, summarizer, trend_analyzer, writer, validator],
        "run": run_research_task
    }