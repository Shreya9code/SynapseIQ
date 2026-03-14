# bi/internal_analyst_agent.py
from backend.agents.base_agent import BaseAgent
from backend.tools.data_tools.csv_parser import CSVParser
from backend.tools.analytics_tools.descriptive_stats import DescriptiveStats
from backend.tools.visualization_tools.plotly_charts import PlotlyCharts
from typing import Dict, Any, List
import pandas as pd

class InternalAnalystAgent(BaseAgent):
    """Analyze uploaded internal data (CSV, Excel, JSON)"""
    
    def __init__(self):
        super().__init__(name="internal_analyst_agent")
        self.parser_class = CSVParser  # Store class, not instance
        self.stats_class = DescriptiveStats
        self.charts_class = PlotlyCharts
    
    async def analyze(self, file_paths: List[str], 
                      user_query: str = "") -> Dict[str, Any]:
        """Analyze uploaded data files"""
        all_data = {}
        all_charts = []
        
        for file_path in file_paths:
            # Create instance here
            parser = self.parser_class(file_path)
            df = parser.parse()
            schema = parser.get_schema()
            
            # Generate statistics
            stats = self.stats_class(df).compute_all()
            
            # Generate charts
            charts = self._generate_charts(df, schema)
            all_charts.extend(charts)
            
            # Generate insights
            insights = await self._generate_insights(df, stats, user_query)
            
            all_data[file_path] = {
                "schema": schema,
                "sample": parser.get_sample(5),
                "statistics": stats,
                "insights": insights
            }
        
        # Detect anomalies
        anomalies = await self._detect_anomalies(all_data)
        
        return {
            "agent": "internal_analyst_agent",
            "files_analyzed": len(file_paths),
            "data_summary": all_data,
            "visualizations": all_charts,
            "anomalies": anomalies,
            "confidence": 0.9,
            "timestamp": self._get_timestamp()
        }
    
    # Rest of the methods remain the same...
    def _generate_charts(self, df: pd.DataFrame, schema: dict) -> List[Dict[str, Any]]:
        """Auto-generate relevant charts"""
        charts = []
        columns = schema["columns"]
        
        # Fix: Use charts_class
        chart_type = self.charts_class.auto_recommend(df, columns)
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if chart_type == "line" and len(numeric_cols) >= 1:
            charts.append({
                "type": "line",
                "title": "Trend Over Time",
                "data": self.charts_class.line_chart(df, x=columns[0], y=numeric_cols[0])
            })
        
        if chart_type == "bar" and len(numeric_cols) >= 1:
            charts.append({
                "type": "bar",
                "title": "Comparison",
                "data": self.charts_class.bar_chart(df, x=columns[0], y=numeric_cols[0])
            })
        
        if len(numeric_cols) >= 2:
            charts.append({
                "type": "scatter",
                "title": "Correlation",
                "data": self.charts_class.scatter_chart(df, x=numeric_cols[0], y=numeric_cols[1])
            })
        
        return charts
    
    async def _generate_insights(self, df: pd.DataFrame, stats: dict, 
                                  query: str) -> str:
        """Generate natural language insights"""
        prompt = f"""
        Analyze this data and provide key insights:
        
        Data Summary:
        - Rows: {stats['data_quality'].get('completeness', 0) * 100:.1f}% complete
        - Numeric columns: {len(stats.get('numeric_stats', {}))}
        - Categorical columns: {len(stats.get('categorical_stats', {}))}
        
        Statistics: {stats['numeric_stats']}
        
        User Query: {query}
        
        Provide 3-5 actionable insights.
        """
        response = await self.llm_call(prompt)
        return response
    
    async def _detect_anomalies(self, all_data: dict) -> List[Dict[str, Any]]:
        """Detect anomalies across datasets"""
        anomalies = []
        
        for file_path, data in all_data.items():
            stats = data.get("statistics", {})
            quality = stats.get("data_quality", {})
            
            if quality.get("completeness", 1) < 0.8:
                anomalies.append({
                    "file": file_path,
                    "type": "data_quality",
                    "severity": "high",
                    "description": f"Data completeness is {quality.get('completeness', 0)*100:.1f}%"
                })
            if quality.get("duplicate_percentage", 0) > 5:
                anomalies.append({
                    "file": file_path,
                    "type": "duplicates",
                    "severity": "medium",
                    "description": f"{quality.get('duplicate_percentage', 0):.1f}% duplicate rows"
                })        
        return anomalies