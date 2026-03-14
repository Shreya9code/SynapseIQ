from backend.agents.base_agent import BaseAgent
from backend.tools.external_apis.market_data_apis import MarketDataAPIs
from typing import Dict, Any
import asyncio

class IndustryAgent(BaseAgent):
    """Research market size, growth, drivers, regulations"""
    
    def __init__(self, api_config: dict):
        super().__init__(name="industry_agent")
        self.api = MarketDataAPIs(config=api_config)
    
    async def research(self, industry: str, region: str) -> Dict[str, Any]:
        """Gather industry intelligence"""
        try:
            # Get market size data
            market_data = self.api.get_market_size(industry, region)
            
            # Get trend data
            trend_data = self.api.get_trend_data(
                keywords=[industry, f"{industry} market"],
                geo=self._region_to_geo_code(region)
            )
            
            # Get news
            news_data = self.api.get_industry_news(industry, days=30)
            
            # Generate insights using LLM
            insights = await self._generate_insights({
                "market": market_data,
                "trends": trend_data,
                "news": news_data
            })
            
            return {
                "agent": "industry_agent",
                "industry": industry,
                "region": region,
                "market_size": market_data,
                "trends": trend_data,
                "news_summary": news_data,
                "insights": insights,
                "confidence": self._calculate_confidence(market_data, trend_data),
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            return {
                "agent": "industry_agent",
                "error": str(e),
                "confidence": 0.0
            }
    
    def _region_to_geo_code(self, region: str) -> str:
        """Convert region name to Google Trends geo code"""
        mapping = {
            "europe": "GB",
            "north america": "US",
            "asia": "JP",
            "asia pacific": "AU",
            "global": ""
        }
        return mapping.get(region.lower(), "")
    
    async def _generate_insights(self, data: dict) -> str:
        """Use LLM to generate natural language insights"""
        prompt = f"""
        Analyze this market data and provide 3-5 key insights:
        
        Market Data: {self._truncate(data['market'])}
        Trends: {self._truncate(data['trends'])}
        Recent News: {self._truncate(data['news'])}
        
        Focus on:
        1. Market growth trajectory
        2. Key drivers and headwinds
        3. Strategic implications
        
        Keep it concise and actionable.
        """
        response = await self.llm_call(prompt)
        return response
    
    def _calculate_confidence(self, market_data: dict, trend_data: dict) -> float:
        """Calculate confidence score based on data quality"""
        score = 0.5  # Base score
        
        if market_data.get("source") == "Statista":
            score += 0.2
        if not market_data.get("warning"):
            score += 0.1
        if trend_data.get("average_interest"):
            score += 0.1
        if market_data.get("cached") == False:  # Fresh data
            score += 0.1
        
        return min(score, 1.0)