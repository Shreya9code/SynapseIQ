from backend.agents.base_agent import BaseAgent
from backend.tools.external_apis.market_data_apis import MarketDataAPIs
from typing import Dict, Any

class TrendAgent(BaseAgent):
    """Identify emerging trends, tech shifts, regulatory changes"""
    
    def __init__(self, api_config: dict):
        super().__init__(name="trend_agent")
        self.api = MarketDataAPIs(config=api_config)
    
    async def research(self, industry: str, timeframe: str = "12 months") -> Dict[str, Any]:
        """Gather trend intelligence"""
        
        # Get Google Trends data
        trend_data = self.api.get_trend_data(
            keywords=[industry, f"{industry} trends", f"{industry} innovation"],
            timeframe="today 12-m"
        )
        
        # Get news for trend detection
        news_data = self.api.get_industry_news(industry, days=90)
        
        # Analyze trends
        emerging_trends = await self._detect_emerging_trends(trend_data, news_data)
        
        # Detect technology shifts
        tech_shifts = await self._detect_tech_shifts(news_data)
        
        return {
            "agent": "trend_agent",
            "industry": industry,
            "timeframe": timeframe,
            "trend_data": trend_data,
            "emerging_trends": emerging_trends,
            "technology_shifts": tech_shifts,
            "confidence": self._calculate_confidence(trend_data),
            "timestamp": self._get_timestamp()
        }
    
    async def _detect_emerging_trends(self, trend_data: dict, 
                                       news_data: dict) -> list:
        """Detect emerging trends from data"""
        prompt = f"""
        Analyze this trend and news data to identify emerging trends:
        
        Trend Data: {self._truncate(trend_data)}
        News Headlines: {self._truncate([a.get('title') for a in news_data.get('articles', [])])}
        
        Return top 5 emerging trends as a JSON array.
        Each item must have: name (string), evidence (string), growth_trajectory (accelerating/stable/declining)
        Return ONLY the JSON array, no other text.
        """
        result = await self.llm_json_call(prompt)
        # llm_json_call returns {} on failure; normalise to list
        return result if isinstance(result, list) else []
    
    async def _detect_tech_shifts(self, news_data: dict) -> list:
        """Detect technology shifts"""
        prompt = f"""
        From these news articles, identify technology shifts:
        
        {self._truncate(news_data)}
        
        Look for: new technologies being adopted, legacy tech being replaced, regulatory changes.
        Return as a JSON array of objects with: technology, direction, impact.
        Return ONLY the JSON array, no other text.
        """
        result = await self.llm_json_call(prompt)
        return result if isinstance(result, list) else []
    
    def _calculate_confidence(self, trend_data: dict) -> float:
        score = 0.5
        if trend_data.get("average_interest"):
            score += 0.3
        if not trend_data.get("error"):
            score += 0.2
        return min(score, 1.0)