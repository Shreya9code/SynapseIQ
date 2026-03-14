from backend.agents.base_agent import BaseAgent
from typing import Dict, Any, List
import json, re

class StrategyAgent(BaseAgent):
    """Generate strategic recommendations and action items"""
    
    def __init__(self):
        super().__init__(name="strategy_agent")
    
    async def recommend(self, synthesis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic recommendations"""
        
        # Generate SWOT matrix
        swot_matrix = await self._generate_swot_matrix(synthesis)
        
        # Generate strategic recommendations
        recommendations = await self._generate_recommendations(synthesis)
        
        # Generate action items
        action_items = await self._generate_action_items(recommendations)
        
        # Generate go-to-market suggestions
        gtm = await self._generate_gtm_suggestions(synthesis)
        
        return {
            "agent": "strategy_agent",
            "swot_matrix": swot_matrix,
            "recommendations": recommendations,
            "action_items": action_items,
            "go_to_market": gtm,
            "priority_framework": self._prioritize(recommendations),
            "timestamp": self._get_timestamp()
        }
    
    async def _generate_swot_matrix(self, synthesis: dict) -> Dict[str, List[str]]:
        """Generate SWOT matrix"""
        prompt = f"""
        Create a SWOT matrix based on this analysis:
        
        Market Overview: {self._truncate(synthesis.get('market_overview', {}))}
        Competitive Landscape: {self._truncate(synthesis.get('competitive_landscape', {}))}
        Trend Analysis: {self._truncate(synthesis.get('trend_analysis', {}))}
        Internal Performance: {self._truncate(synthesis.get('internal_performance', {}))}
        
        Return as JSON with keys: strengths, weaknesses, opportunities, threats
        Each should be a list of 3-5 short items.
        """
        return await self.llm_call(prompt)
    
    async def _generate_recommendations(self, synthesis: dict) -> str:
        """Generate strategic recommendations"""
        prompt = f"""
        Based on this market analysis, provide 5 strategic recommendations:
        
        {self._truncate(synthesis)}
        
        For each recommendation include:
        - title
        - description
        - expected_impact (high/medium/low)
        - effort_required (high/medium/low)
        - timeline (weeks/months)
        
        Return as JSON array.
        """
        return await self.llm_call(prompt)
    
    async def _generate_action_items(self, recommendations) -> str:
        """Convert recommendations to action items"""
        prompt = f"""
        Convert these recommendations into specific action items:
        
        {self._truncate(recommendations)}
        
        For each action item include:
        - action
        - owner (role)
        - deadline
        - success_metric
        
        Return as JSON array.
        """
        return await self.llm_call(prompt)
    
    async def _generate_gtm_suggestions(self, synthesis: dict) -> str:
        """Generate go-to-market suggestions"""
        prompt = f"""
        Based on this market analysis, suggest go-to-market strategies:
        
        {self._truncate(synthesis)}
        
        Include:
        - Target segments
        - Positioning recommendations
        - Pricing strategy
        - Channel recommendations
        
        Return as JSON.
        """
        return await self.llm_call(prompt)
    
    def _prioritize(self, recommendations) -> Dict[str, List[dict]]:
        """Prioritize recommendations by impact/effort.
        Safely handles cases where LLM returned a string instead of a parsed list."""
        # If LLM returned a string, try to parse JSON out of it
        if isinstance(recommendations, str):
            try:
                clean = re.sub(r"```json|```", "", recommendations).strip()
                recommendations = json.loads(clean)
            except (json.JSONDecodeError, ValueError):
                return {"quick_wins": [], "strategic_bets": [], "fill_ins": []}

        if not isinstance(recommendations, list):
            return {"quick_wins": [], "strategic_bets": [], "fill_ins": []}

        quick_wins, strategic_bets, fill_ins = [], [], []
        for rec in recommendations:
            if not isinstance(rec, dict):
                continue
            impact = rec.get("expected_impact", "medium")
            effort = rec.get("effort_required", "medium")
            if impact == "high" and effort == "low":
                quick_wins.append(rec)
            elif impact == "high" and effort == "high":
                strategic_bets.append(rec)
            else:
                fill_ins.append(rec)
        
        return {
            "quick_wins": quick_wins,
            "strategic_bets": strategic_bets,
            "fill_ins": fill_ins
        }