from backend.agents.base_agent import BaseAgent
from backend.tools.external_apis.market_data_apis import MarketDataAPIs
from typing import Dict, Any, List

class CompetitorAgent(BaseAgent):
    """Analyze competitors: market share, SWOT, pricing"""
    
    def __init__(self, api_config: dict):
        super().__init__(name="competitor_agent")
        self.api = MarketDataAPIs(config=api_config)
    
    async def research(self, industry: str, 
                       competitors: List[str] = None) -> Dict[str, Any]:
        """Gather competitor intelligence"""
        
        if not competitors:
            competitors = await self._discover_competitors(industry)
        
        company_profiles = []
        for company in competitors[:5]:  # Limit to top 5
            profile = self.api.get_company_profile(company)
            company_profiles.append(profile)
        
        # Generate SWOT analysis
        swot = await self._generate_swot(company_profiles, industry)
        
        # Generate competitive matrix
        matrix = await self._generate_comparison_matrix(company_profiles)
        
        return {
            "agent": "competitor_agent",
            "industry": industry,
            "competitors_analyzed": len(company_profiles),
            "company_profiles": company_profiles,
            "swot_analysis": swot,
            "comparison_matrix": matrix,
            "confidence": self._calculate_confidence(company_profiles),
            "timestamp": self._get_timestamp()
        }
    
    async def _discover_competitors(self, industry: str) -> List[str]:
        """Auto-discover top competitors"""
        prompt = f"""
        List the top 5 companies in the {industry} industry.
        Return only company names, one per line.
        """
        response = await self.llm_call(prompt)
        return [line.strip() for line in response.split('\n') if line.strip()]
    
    async def _generate_swot(self, profiles: List[dict], 
                             industry: str) -> Dict[str, Any]:
        """Generate SWOT analysis"""
        prompt = f"""
        Based on these company profiles, create a SWOT analysis for the {industry} industry:
        
        {profiles}
        
        Return as JSON with keys: strengths, weaknesses, opportunities, threats
        """
        response = await self.llm_call(prompt)
        return response
    
    async def _generate_comparison_matrix(self, profiles: List[dict]) -> Dict[str, Any]:
        """Generate comparison matrix"""
        return {
            "columns": ["Company", "Founded", "Funding", "Categories"],
            "rows": [
                [
                    p.get("name", "Unknown"),
                    p.get("founded_year", "N/A"),
                    p.get("total_funding_usd", 0),
                    ", ".join(p.get("categories", [])[:3])
                ]
                for p in profiles
            ]
        }
    
    def _calculate_confidence(self, profiles: List[dict]) -> float:
        score = 0.5
        valid_profiles = sum(1 for p in profiles if p.get("source") == "Crunchbase")
        score += (valid_profiles / len(profiles)) * 0.5 if profiles else 0
        return min(score, 1.0)