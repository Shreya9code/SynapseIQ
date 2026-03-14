from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class MarketSizeData(BaseModel):
    source: str
    market_size_usd: float
    cagr: float
    forecast_years: List[int]
    cached: bool
    timestamp: str

class CompanyProfile(BaseModel):
    name: str
    founded_year: Optional[int] = None
    total_funding_usd: float = 0
    categories: List[str] = []
    source: str

class TrendData(BaseModel):
    source: str
    interest_over_time: Dict[str, Any] = {}
    average_interest: Dict[str, Any] = {}
    cached: bool

class BIReport(BaseModel):
    status: str
    query: str
    industry: str
    region: str
    executive_summary: str
    market_overview: Dict[str, Any]
    competitive_landscape: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    strategy: Dict[str, Any]
    validation: Dict[str, Any]
    visualizations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "complete",
                "query": "Analyze EV market in Europe",
                "industry": "Electric Vehicles",
                "region": "Europe"
            }
        }