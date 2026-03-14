import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List

class PlotlyCharts:
    """Generate interactive Plotly charts"""
    
    @staticmethod
    def line_chart(df: pd.DataFrame, x: str, y: str, title: str = "") -> Dict[str, Any]:
        """Time series line chart"""
        fig = px.line(df, x=x, y=y, title=title, markers=True)
        fig.update_layout(hovermode='x unified')
        return fig.to_dict()
    
    @staticmethod
    def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", 
                  color: str = None) -> Dict[str, Any]:
        """Bar chart for comparisons"""
        fig = px.bar(df, x=x, y=y, color=color, title=title)
        fig.update_layout(barmode='group')
        return fig.to_dict()
    
    @staticmethod
    def pie_chart(df: pd.DataFrame, names: str, values: str, 
                  title: str = "") -> Dict[str, Any]:
        """Pie chart for composition"""
        fig = px.pie(df, names=names, values=values, title=title)
        return fig.to_dict()
    
    @staticmethod
    def scatter_chart(df: pd.DataFrame, x: str, y: str, 
                      title: str = "", color: str = None) -> Dict[str, Any]:
        """Scatter plot for relationships"""
        fig = px.scatter(df, x=x, y=y, color=color, title=title, 
                        trendline="ols" if color is None else None)
        return fig.to_dict()
    
    @staticmethod
    def histogram(df: pd.DataFrame, x: str, title: str = "", 
                  nbins: int = 20) -> Dict[str, Any]:
        """Histogram for distributions"""
        fig = px.histogram(df, x=x, nbins=nbins, title=title)
        return fig.to_dict()
    
    @staticmethod
    def heatmap(correlation_matrix: List[List[float]], 
                columns: List[str], title: str = "") -> Dict[str, Any]:
        """Heatmap for correlation matrix"""
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            x=columns,
            y=columns,
            colorscale='RdBu',
            zmid=0
        ))
        fig.update_layout(title=title)
        return fig.to_dict()
    
    @staticmethod
    def auto_recommend(df: pd.DataFrame, columns: List[str]) -> str:
        """Recommend best chart type based on data"""
        if len(df) == 0:
            return "empty"
        
        # Check for time column
        time_keywords = ['date', 'time', 'year', 'month', 'quarter']
        has_time = any(any(kw in col.lower() for kw in time_keywords) for col in columns)
        
        if has_time:
            return "line"
        
        # Check data types
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        if len(numeric_cols) >= 2:
            return "scatter"
        elif len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            return "bar"
        elif len(numeric_cols) == 1:
            return "histogram"
        else:
            return "bar"