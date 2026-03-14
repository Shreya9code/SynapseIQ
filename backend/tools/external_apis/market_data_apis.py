from typing import Dict, Any, List, Optional
from .base_api import BaseAPI
from datetime import datetime
class MarketDataAPIs(BaseAPI):
    """
    Combined wrapper for all market research APIs
    Single class, multiple methods for different data sources
    """
    
    def __init__(self, config: dict):
        super().__init__(cache_ttl=config.get("cache_ttl", 86400))
        self.config = config
        
        # API-specific keys
        self.statista_key = config.get("statista_api_key")
        self.crunchbase_key = config.get("crunchbase_api_key")
        self.news_api_key = config.get("news_api_key")
        
        # Base URLs
        self.statista_url = "https://api.statista.com/v1"
        self.crunchbase_url = "https://api.crunchbase.com/api/v4"
        self.news_url = "https://newsapi.org/v2"
        self.sec_url = "https://data.sec.gov"
    
    def get_market_size(self, industry: str, region: str) -> Dict[str, Any]:
        """Get market size from Statista"""
        if not self.statista_key:
            return self._fallback_market_size(industry, region)
        
        headers = {"Authorization": f"Bearer {self.statista_key}"}
        endpoint = f"{self.statista_url}/markets/{industry.lower().replace(' ', '-')}"
        params = {"region": region.lower()}
        
        result = self._make_request("GET", endpoint, headers, params)
        
        if "error" in result:
            return self._fallback_market_size(industry, region)
        
        data = result["data"]
        return {
            "source": "Statista",
            "market_size_usd": data.get("revenue", 0),
            "cagr": data.get("cagr", 0),
            "forecast_years": data.get("forecast", []),
            "cached": result["from_cache"]
        }
    
    def _fallback_market_size(self, industry: str, region: str) -> Dict[str, Any]:
        """Fallback when Statista fails"""
        return {
            "source": "Fallback (Estimated)",
            "market_size_usd": 0,
            "cagr": 0,
            "warning": "Statista API unavailable - using estimates",
            "cached": False
        }
    
    def get_company_profile(self, company_name: str) -> Dict[str, Any]:
        """Get company info from Crunchbase"""
        if not self.crunchbase_key:
            return self._fallback_company_profile(company_name)
        
        headers = {"Authorization": f"Bearer {self.crunchbase_key}"}
        endpoint = f"{self.crunchbase_url}/entities/organizations/{company_name.lower().replace(' ', '-')}"
        
        result = self._make_request("GET", endpoint, headers)
        
        if "error" in result:
            return self._fallback_company_profile(company_name)
        
        data = result["data"]
        return {
            "source": "Crunchbase",
            "name": data.get("properties", {}).get("identifier", {}).get("value"),
            "founded_year": data.get("properties", {}).get("founded_on", {}).get("year"),
            "total_funding_usd": data.get("properties", {}).get("total_funding_usd", 0),
            "categories": [cat.get("value") for cat in data.get("categories", [])],
            "cached": result["from_cache"]
        }
    
    def _fallback_company_profile(self, company_name: str) -> Dict[str, Any]:
        """Fallback when Crunchbase fails"""
        return {
            "source": "Fallback (Web Search)",
            "name": company_name,
            "warning": "Crunchbase API unavailable",
            "cached": False
        }
    
    def get_trend_data(self, keywords: List[str], geo: str = "", timeframe: str = "today 12-m") -> Dict[str, Any]:
        """Get Google Trends data"""
        try:
            from pytrends.request import TrendReq
            import pandas as pd
            
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload(keywords, cat=0, geo=geo, timeframe=timeframe)
            
            interest_over_time = pytrends.interest_over_time()
            if not interest_over_time.empty:
                interest_over_time = interest_over_time.drop(columns=['isPartial'], errors='ignore')
            
            return {
                "source": "Google Trends",
                "interest_over_time": interest_over_time.to_dict() if not interest_over_time.empty else {},
                "average_interest": interest_over_time.mean().to_dict() if not interest_over_time.empty else {},
                "cached": False  # Google Trends not cached (real-time)
            }
        except Exception as e:
            return {
                "source": "Google Trends",
                "error": str(e),
                "cached": False
            }
    
    def get_company_filings(self, cik: str, form_type: str = "10-K") -> Dict[str, Any]:
        """Get SEC filings"""
        headers = {
            "User-Agent": "YourCompany/1.0 (your@email.com)",
            "Accept-Encoding": "gzip, deflate"
        }
        endpoint = f"{self.sec_url}/filings/CIK{cik}.json"
        
        result = self._make_request("GET", endpoint, headers)
        
        if "error" in result:
            return {"source": "SEC EDGAR", "error": result["error"], "cached": False}
        
        data = result["data"]
        filings = []
        for filing in data.get('filings', {}).get('recent', {})[:10]:
            if filing.get('form') == form_type:
                filings.append({
                    "filing_date": filing.get('filingDate'),
                    "form_type": filing.get('form'),
                    "accession_number": filing.get('accessionNumber')
                })
        
        return {
            "source": "SEC EDGAR",
            "company_name": data.get('name'),
            "filings": filings,
            "cached": result["from_cache"]
        }
    
    def get_industry_news(self, industry: str, days: int = 7) -> Dict[str, Any]:
        """Get recent news about industry"""
        if not self.news_api_key:
            return {"source": "NewsAPI", "error": "API key not configured", "cached": False}
        
        from datetime import datetime, timedelta
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        headers = {"X-Api-Key": self.news_api_key}
        endpoint = f"{self.news_url}/everything"
        params = {
            "q": industry,
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en"
        }
        
        result = self._make_request("GET", endpoint, headers, params)
        
        if "error" in result:
            return {"source": "NewsAPI", "error": result["error"], "cached": False}
        
        data = result["data"]
        return {
            "source": "NewsAPI",
            "articles": [
                {
                    "title": article.get("title"),
                    "source": article.get("source", {}).get("name"),
                    "published_at": article.get("publishedAt"),
                    "url": article.get("url")
                }
                for article in data.get("articles", [])[:10]
            ],
            "total_results": data.get("totalResults"),
            "cached": result["from_cache"]
        }
    
    def get_comprehensive_market_data(self, industry: str, region: str, companies: List[str] = None) -> Dict[str, Any]:
        """
        One-stop method to get ALL market data
        Perfect for your BI agents
        """
        results = {
            "industry": industry,
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # 1. Market Size (Statista)
        results["data"]["market_size"] = self.get_market_size(industry, region)
        
        # 2. Trends (Google Trends)
        results["data"]["trends"] = self.get_trend_data([industry, f"{industry} market"])
        
        # 3. Company Profiles (Crunchbase)
        if companies:
            results["data"]["companies"] = [
                self.get_company_profile(company) for company in companies
            ]
        
        # 4. Recent News
        results["data"]["news"] = self.get_industry_news(industry)
        
        return results