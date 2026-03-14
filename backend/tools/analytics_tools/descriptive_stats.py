import pandas as pd
import numpy as np
from typing import Dict, Any

class DescriptiveStats:
    """Generate descriptive statistics for datasets"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def compute_all(self) -> Dict[str, Any]:
        """Compute all descriptive statistics"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns
        
        return {
            "numeric_stats": self._numeric_stats(numeric_cols),
            "categorical_stats": self._categorical_stats(categorical_cols),
            "correlation_matrix": self._correlation_matrix(numeric_cols),
            "data_quality": self._data_quality()
        }
    
    def _numeric_stats(self, columns) -> Dict[str, Any]:
        """Statistics for numeric columns"""
        stats = {}
        for col in columns:
            stats[col] = {
                "mean": float(self.df[col].mean()),
                "median": float(self.df[col].median()),
                "std": float(self.df[col].std()),
                "min": float(self.df[col].min()),
                "max": float(self.df[col].max()),
                "q25": float(self.df[col].quantile(0.25)),
                "q75": float(self.df[col].quantile(0.75)),
                "skewness": float(self.df[col].skew()),
                "kurtosis": float(self.df[col].kurtosis())
            }
        return stats
    
    def _categorical_stats(self, columns) -> Dict[str, Any]:
        """Statistics for categorical columns"""
        stats = {}
        for col in columns:
            value_counts = self.df[col].value_counts().head(10)
            stats[col] = {
                "unique_count": int(self.df[col].nunique()),
                "top_values": value_counts.to_dict(),
                "mode": str(self.df[col].mode()[0]) if len(self.df[col].mode()) > 0 else None
            }
        return stats
    
    def _correlation_matrix(self, columns) -> Dict[str, Any]:
        """Correlation between numeric columns"""
        if len(columns) < 2:
            return {}
        
        corr = self.df[columns].corr()
        return {
            "columns": corr.columns.tolist(),
            "matrix": corr.values.tolist()
        }
    
    def _data_quality(self) -> Dict[str, Any]:
        """Data quality metrics"""
        total_cells = self.df.shape[0] * self.df.shape[1]
        null_cells = self.df.isnull().sum().sum()

        return {
            "completeness": float(1 - (null_cells / total_cells)),
            "duplicate_rows": int(self.df.duplicated().sum()),
            "duplicate_percentage": float(self.df.duplicated().sum() / len(self.df) * 100)
        }