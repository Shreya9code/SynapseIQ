from backend.agents.base_agent import BaseAgent
from typing import Dict, Any, List

class ValidatorAgent(BaseAgent):
    """Fact-check and validate all insights"""
    
    def __init__(self):
        super().__init__(name="validator_agent")
    
    async def validate(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Validate entire report"""
        
        # Check for hallucinations
        hallucination_check = await self._check_hallucinations(report)
        
        # Verify citations
        citation_check = await self._verify_citations(report)
        
        # Check logical consistency
        consistency_check = await self._check_consistency(report)
        
        # Calculate final confidence
        final_confidence = self._calculate_final_confidence(
            hallucination_check, citation_check, consistency_check
        )
        
        # Generate validation summary
        summary = await self._generate_validation_summary(
            hallucination_check, citation_check, consistency_check
        )
        
        return {
            "agent": "validator_agent",
            "hallucination_check": hallucination_check,
            "citation_check": citation_check,
            "consistency_check": consistency_check,
            "final_confidence": final_confidence,
            "validation_summary": summary,
            "requires_human_review": final_confidence < 0.7,
            "timestamp": self._get_timestamp()
        }
    
    async def _check_hallucinations(self, report: dict) -> Dict[str, Any]:
        """Check for potential hallucinations"""
        prompt = f"""
        Review this report summary for potential hallucinations or unsupported claims:
        
        {self._truncate(report)}
        
        Flag any:
        - Statistics without sources
        - Contradictory statements
        - Overly specific claims without evidence
        
        Return as JSON with: flagged_items (list), risk_level (low/medium/high)
        """
        response = await self.llm_call(prompt)
        return response
    
    async def _verify_citations(self, report: dict) -> Dict[str, Any]:
        """Verify all citations are valid"""
        citations = self._extract_citations(report)
        
        valid_count = 0
        for citation in citations:
            if citation.get("source") and citation.get("source") != "Unknown":
                valid_count += 1
        
        return {
            "total_citations": len(citations),
            "valid_citations": valid_count,
            "citation_rate": valid_count / len(citations) if citations else 0
        }
    
    async def _check_consistency(self, report: dict) -> Dict[str, Any]:
        """Check for logical consistency"""
        prompt = f"""
        Check this report summary for logical inconsistencies:
        
        {self._truncate(report)}
        
        Look for:
        - Contradictory recommendations
        - Numbers that don't add up
        - Inconsistent timeframes
        
        Return as JSON with: inconsistencies (list), severity (low/medium/high)
        """
        response = await self.llm_call(prompt)
        return response
    
    def _extract_citations(self, report: dict) -> List[dict]:
        """Extract all citations from report"""
        citations = []
        if "data_sources" in report:
            for source in report.get("data_sources", []):
                citations.append({"source": source})
        return citations
    
    def _calculate_final_confidence(self, hallucination, 
                                     citation: dict, consistency) -> float:
        """Calculate final confidence score"""
        score = 1.0
        
        # hallucination/consistency may be raw strings if LLM returned unparsed text
        if isinstance(hallucination, dict):
            risk_map = {"low": 0, "medium": 0.1, "high": 0.3}
            score -= risk_map.get(hallucination.get("risk_level", "low"), 0)
        else:
            score -= 0.1  # small penalty if we couldn't parse the check

        score -= (1 - citation.get("citation_rate", 1)) * 0.3

        if isinstance(consistency, dict):
            severity_map = {"low": 0.05, "medium": 0.15, "high": 0.3}
            score -= severity_map.get(consistency.get("severity", "low"), 0)
        else:
            score -= 0.05
        
        return max(score, 0.0)
    
    async def _generate_validation_summary(self, hallucination, 
                                            citation: dict, consistency) -> str:
        """Generate human-readable validation summary"""
        prompt = f"""
        Create a validation summary:
        Hallucination Check: {hallucination}
        Citation Check: {citation}
        Consistency Check: {consistency}
        Provide:
        1. Overall assessment
        2. Key concerns (if any)
        3. Recommendations for improvement
        
        Keep it concise (3-5 sentences).
        """
        response = await self.llm_call(prompt)
        return response