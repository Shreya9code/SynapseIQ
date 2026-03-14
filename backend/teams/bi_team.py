from typing import Dict, Any, List, Optional
import asyncio

class BipipelineTeam:
    """BI Agent Team Coordinator (AutoGen-style group chat)"""
    
    def __init__(self, agents: dict, config: dict):
        self.agents = agents
        self.config = config
        self.conversation_history = []
        self.max_turns = config.get("max_turns", 10)
    
    async def run(self, task: str, context: dict = None) -> Dict[str, Any]:
        """Run team collaboration"""
        
        self.conversation_history = [{
            "role": "user",
            "content": task,
            "context": context or {}
        }]
        
        turn = 0
        while turn < self.max_turns:
            # Select next agent based on task
            next_agent = self._select_next_agent(task, self.conversation_history)
            
            if not next_agent:
                break
            
            # Get agent response
            response = await self.agents[next_agent].process(
                task=task,
                history=self.conversation_history
            )
            
            self.conversation_history.append({
                "role": next_agent,
                "content": response
            })
            
            # Check if task is complete
            if self._is_task_complete(response):
                break
            
            turn += 1
        
        return {
            "conversation": self.conversation_history,
            "turns_taken": turn,
            "final_output": self._extract_final_output()
        }
    
    def _select_next_agent(self, task: str, history: list) -> Optional[str]:
        """Select which agent should speak next"""
        # can do LLM-based too
        task_lower = task.lower()
        
        if "market" in task_lower or "size" in task_lower:
            return "industry_agent"
        elif "competitor" in task_lower or "swot" in task_lower:
            return "competitor_agent"
        elif "trend" in task_lower or "emerging" in task_lower:
            return "trend_agent"
        elif "upload" in task_lower or "csv" in task_lower:
            return "internal_analyst_agent"
        elif "recommend" in task_lower or "strategy" in task_lower:
            return "strategy_agent"
        else:
            return "synthesis_agent"
    
    def _is_task_complete(self, response: str) -> bool:
        """Check if task is complete"""
        completion_keywords = ["TERMINATE", "COMPLETE", "FINAL REPORT"]
        return any(keyword in response.upper() for keyword in completion_keywords)
    
    def _extract_final_output(self) -> Dict[str, Any]:
        """Extract final output from conversation"""
        for msg in reversed(self.conversation_history):
            if msg["role"] in ["synthesis_agent", "strategy_agent"]:
                return msg["content"]
        return {}