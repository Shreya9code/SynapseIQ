import pandas as pd
from typing import Dict, Any, Optional
import os

class CSVParser:
    """Parse and validate CSV/Excel files"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.schema = {}
    
    def parse(self) -> pd.DataFrame:
        """Auto-detect file type and load"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.file_path.endswith('.csv'):
            self.df = pd.read_csv(self.file_path, infer_datetime_format=True)
        elif self.file_path.endswith(('.xlsx', '.xls')):
            self.df = pd.read_excel(self.file_path)
        elif self.file_path.endswith('.json'):
            self.df = pd.read_json(self.file_path)
        else:
            raise ValueError(f"Unsupported file format: {self.file_path}")
        
        self.schema = self.get_schema()
        return self.df
    
    def get_schema(self) -> Dict[str, Any]:
        """Detect column types and statistics"""
        if self.df is None:
            return {}
        
        return {
            "columns": self.df.columns.tolist(),
            "row_count": len(self.df),
            "column_count": len(self.df.columns),
            "dtypes": self.df.dtypes.astype(str).to_dict(),
            "null_counts": self.df.isnull().sum().to_dict(),
            "null_percentage": (self.df.isnull().sum() / len(self.df) * 100).to_dict(),
            "memory_usage_mb": self.df.memory_usage(deep=True).sum() / 1024**2
        }
    
    def get_sample(self, n: int = 5) -> Dict[str, Any]:
        """Get sample rows for preview"""
        if self.df is None:
            return {}
        
        return {
            "headers": self.df.columns.tolist(),
            "rows": self.df.head(n).to_dict('records')
        }