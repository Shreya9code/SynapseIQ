from backend.agents.base_agent import BaseAgent
from typing import Dict, Any, List

class SynthesisAgent(BaseAgent):
    """Combine all agent outputs into unified report"""
    
    def __init__(self):
        super().__init__(name="synthesis_agent")
    
    async def combine(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all research into cohesive report"""
        
        # Extract outputs from each agent
        industry = agent_outputs.get("industry_agent", {})
        competitor = agent_outputs.get("competitor_agent", {})
        trend = agent_outputs.get("trend_agent", {})
        internal = agent_outputs.get("internal_analyst_agent", {})
        
        # Generate unified analysis
        market_overview = await self._generate_market_overview(industry, internal)
        competitive_landscape = await self._generate_competitive_landscape(competitor)
        trend_analysis = await self._generate_trend_analysis(trend)
        
        # Calculate overall confidence
        confidence = self._calculate_overall_confidence(agent_outputs)
        
        return {
            "agent": "synthesis_agent",
            "market_overview": market_overview,
            "competitive_landscape": competitive_landscape,
            "trend_analysis": trend_analysis,
            "internal_performance": internal.get("data_summary", {}),
            "visualizations": internal.get("visualizations", []),
            "overall_confidence": confidence,
            "data_sources": self._extract_sources(agent_outputs),
            "timestamp": self._get_timestamp()
        }
    
    async def _generate_market_overview(self, industry: dict, 
                                         internal: dict) -> Dict[str, Any]:
        """Generate market overview section"""
        prompt = f"""
        Create a market overview combining:
        
        Industry Data: {self._truncate(industry.get('market_size', {}))}
        Industry Insights: {self._truncate(industry.get('insights', ''))}
        Internal Performance: {self._truncate(internal.get('insights', ''))}
        
        Structure:
        1. Market size and growth
        2. Key drivers
        3. How internal performance compares to market
        """
        response = await self.llm_call(prompt)
        return {"content": response}
    
    async def _generate_competitive_landscape(self, competitor: dict) -> Dict[str, Any]:
        """Generate competitive landscape section"""
        return {
            "swot": competitor.get("swot_analysis", {}),
            "comparison_matrix": competitor.get("comparison_matrix", {}),
            "top_players": competitor.get("company_profiles", [])
        }
    
    async def _generate_trend_analysis(self, trend: dict) -> Dict[str, Any]:
        """Generate trend analysis section"""
        return {
            "emerging_trends": trend.get("emerging_trends", []),
            "technology_shifts": trend.get("technology_shifts", []),
            "trend_data": trend.get("trend_data", {})
        }
    
    def _calculate_overall_confidence(self, outputs: dict) -> float:
        """Calculate weighted average confidence"""
        confidences = [
            v.get("confidence", 0.5) 
            for v in outputs.values() 
            if isinstance(v, dict) and "confidence" in v
        ]
        return sum(confidences) / len(confidences) if confidences else 0.5
    
    def _extract_sources(self, outputs: dict) -> List[str]:
        """Extract all data sources"""
        sources = set()
        for output in outputs.values():
            if isinstance(output, dict):
                if "market_size" in output:
                    sources.add(output["market_size"].get("source", "Unknown"))
                if "company_profiles" in output:
                    for profile in output["company_profiles"]:
                        sources.add(profile.get("source", "Unknown"))
        return list(sources)