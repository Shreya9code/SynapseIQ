# tools/external_apis/base_api.py
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from hashlib import md5

class BaseAPI:
    """
    Base class for all external APIs
    Handles: authentication, rate limiting, error handling
    """
    
    def __init__(self, api_key: str = None, cache_ttl: int = 86400):
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self.session = requests.Session()
        
        # Disable caching (no Redis)
        self.cache_enabled = False
        
        # Rate limiting
        self.request_count = 0
        self.request_limit = 60
        self.window_start = datetime.now()
    
    def _check_rate_limit(self) -> bool:
        now = datetime.now()
        if (now - self.window_start).seconds >= 60:
            self.request_count = 0
            self.window_start = now
        
        if self.request_count >= self.request_limit:
            raise Exception("Rate limit exceeded. Try again in 60 seconds.")
        
        self.request_count += 1
        return True
    
    def _get_cache_key(self, endpoint: str, params: dict) -> str:
        # Keep this method even if not used
        key_string = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return f"api_cache:{md5(key_string.encode()).hexdigest()}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        # No caching
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        # No caching
        pass
    
    def _make_request(self, method: str, url: str, headers: dict = None, 
                      params: dict = None, timeout: int = 30) -> Dict:
        self._check_rate_limit()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            
            return {"data": data, "from_cache": False}
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "from_cache": False}