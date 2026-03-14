import asyncio
from typing import Dict, Any, List
from backend.agents.bi.industry_agent import IndustryAgent
from backend.agents.bi.competitor_agent import CompetitorAgent
from backend.agents.bi.trend_agent import TrendAgent
from backend.agents.bi.internal_analyst_agent import InternalAnalystAgent
from backend.agents.bi.synthesis_agent import SynthesisAgent
from backend.agents.bi.strategy_agent import StrategyAgent
from backend.agents.bi.validator_agent import ValidatorAgent

class Bipipeline:
    """Main BI orchestration pipeline"""
    
    def __init__(self, api_config: dict):
        self.api_config = api_config
        
        # Initialize agents
        self.industry_agent = IndustryAgent(api_config)
        self.competitor_agent = CompetitorAgent(api_config)
        self.trend_agent = TrendAgent(api_config)
        self.internal_analyst = InternalAnalystAgent()
        self.synthesis_agent = SynthesisAgent()
        self.strategy_agent = StrategyAgent()
        self.validator_agent = ValidatorAgent()
    
    async def run(self, query: str, industry: str, region: str,
                  file_paths: List[str] = None, 
                  competitors: List[str] = None) -> Dict[str, Any]:
        """
        Run complete BI analysis pipeline
        
        Args:
            query: User's natural language query
            industry: Industry to analyze
            region: Geographic region
            file_paths: Optional list of uploaded file paths
            competitors: Optional list of competitor names
        
        Returns:
            Complete BI report with all sections
        """
        print(f"🚀 Starting BI analysis for: {industry} in {region}")
        
        # PHASE 1: Parallel Research (External + Internal)
        print("📊 Phase 1: Parallel data collection...")
        
        tasks = [
            self.industry_agent.research(industry, region),
            self.competitor_agent.research(industry, competitors),
            self.trend_agent.research(industry),
        ]
        
        if file_paths:
            tasks.append(self.internal_analyst.analyze(file_paths, query))
        
        agent_outputs = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        results = {}
        for i, task in enumerate(["industry", "competitor", "trend", "internal"]):
            if i < len(agent_outputs):
                output = agent_outputs[i]
                if isinstance(output, Exception):
                    results[f"{task}_agent"] = {"error": str(output), "confidence": 0.0}
                else:
                    results[f"{task}_agent"] = output
        
        # PHASE 2: Synthesis
        print("🔗 Phase 2: Synthesizing insights...")
        synthesis = await self.synthesis_agent.combine(results)
        
        # PHASE 3: Strategy Generation
        print("💡 Phase 3: Generating strategy...")
        strategy = await self.strategy_agent.recommend(synthesis)
        
        # PHASE 4: Validation
        print("✅ Phase 4: Validating report...")
        validation = await self.validator_agent.validate({
            **synthesis,
            **strategy
        })
        
        # PHASE 5: Final Report Assembly
        print("📄 Phase 5: Assembling final report...")
        final_report = {
            "status": "complete",
            "query": query,
            "industry": industry,
            "region": region,
            "executive_summary": await self._generate_executive_summary(synthesis, strategy),
            "market_overview": synthesis.get("market_overview", {}),
            "competitive_landscape": synthesis.get("competitive_landscape", {}),
            "trend_analysis": synthesis.get("trend_analysis", {}),
            "internal_performance": synthesis.get("internal_performance", {}),
            "strategy": strategy,
            "validation": validation,
            "visualizations": synthesis.get("visualizations", []),
            "metadata": {
                "generated_at": synthesis.get("timestamp"),
                "agents_executed": list(results.keys()),
                "overall_confidence": validation.get("final_confidence", 0),
                "requires_human_review": validation.get("requires_human_review", False)
            }
        }
        
        print("✅ BI analysis complete!")
        return final_report
    
    async def _generate_executive_summary(self, synthesis: dict, 
                                           strategy: dict) -> str:
        """Generate executive summary"""
        prompt = f"""
        Create a 1-paragraph executive summary:
        
        Market Overview: {synthesis.get('market_overview', {})}
        Key Recommendations: {strategy.get('recommendations', [])[:3]}
        
        Focus on:
        1. Market opportunity
        2. Key challenge
        3. Top recommendation
        
        Keep it under 150 words.
        """
        response = await self.synthesis_agent.llm_call(prompt)
        return response