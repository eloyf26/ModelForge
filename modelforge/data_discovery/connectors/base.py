from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import logging
import aiohttp
import asyncio
from cachetools import TTLCache
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """Base class for API connectors with rate limiting and caching"""
    
    def __init__(self, base_url: str, rate_limit: int = 60):
        self.base_url = base_url.rstrip('/')
        self.rate_limit = rate_limit
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour cache TTL
        logger.info("Initialized %s connector with base URL: %s", self.__class__.__name__, base_url)
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        logger.debug("Created new aiohttp session for %s", self.__class__.__name__)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            logger.debug("Closed aiohttp session for %s", self.__class__.__name__)
            
    @sleep_and_retry
    @limits(calls=1, period=1)  # Basic rate limiting
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a rate-limited API request with caching"""
        if not self.session:
            logger.error("Connector must be used as async context manager")
            raise RuntimeError("Connector must be used as async context manager")
            
        # Check cache
        cache_key = f"{endpoint}:{str(params)}"
        if cache_key in self.cache:
            logger.debug("Cache hit for %s", cache_key)
            return self.cache[cache_key]
            
        logger.debug("Making request to %s/%s with params: %s", self.base_url, endpoint, params)
        # Make request
        try:
            async with self.session.get(f"{self.base_url}/{endpoint}", params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
            # Update cache
            self.cache[cache_key] = data
            logger.debug("Successfully cached response for %s", cache_key)
            return data
        except aiohttp.ClientError as e:
            logger.error("Request failed for %s/%s: %s", self.base_url, endpoint, str(e))
            raise
        
    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about available datasets"""
        pass
        
    @abstractmethod
    async def search_datasets(self, query: str) -> Dict[str, Any]:
        """Search for datasets matching query"""
        pass
        
    @abstractmethod
    async def get_dataset_schema(self, dataset_id: str) -> Dict[str, Any]:
        """Get schema information for a specific dataset"""
        pass 