import os
from pydantic_settings import BaseSettings
from typing import List, Dict, Any,Optional

class Settings(BaseSettings):

    GROQ_API_KEY: str
    LLM_MODEL: str = "llama-3.1-8b-instant"
    # 🆕 RAG Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # sentence-transformers
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.7EBXZ_9cpFw9Go2lALSWKciGPozDhPSO4bqgX7-ltBQ"  # Optional for local
    # External API Keys
    STATISTA_API_KEY: str = ""
    CRUNCHBASE_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    # BI Configuration
    BI_CACHE_TTL_HOURS: int = 24
    BI_RATE_LIMIT_PER_MINUTE: int = 60
    BI_MAX_FILE_SIZE_MB: int = 50
    # Database
    DATABASE_URL: str = "postgresql://localhost:5432/bi_db"
    REDIS_URL: str = "redis://localhost:6379"
    DATA_DIR: str = "./data"
    UPLOAD_DIR: str = "./data/uploads"
    DB_PATH: str = "./data/research.db"
    VECTOR_DB_PATH: str = "./data/vector_store"
    
    ALPHA_VANTAGE_KEY: str = ""
    class Config:
        env_file = ".env"

settings = Settings()

def get_llm_config() -> List[Dict[str, Any]]:
    return [
        {
            "model": settings.LLM_MODEL,
            "api_key": settings.GROQ_API_KEY,
            "base_url": "https://api.groq.com/openai/v1",
            "temperature": 0.7,
            "cache_seed": None,
            "price": [0, 0],
        }
    ]