from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import time
import aiohttp
import asyncio
from cachetools import TTLCache
from ratelimit import limits, sleep_and_retry
from modelforge.logging.logger import get_logger
from ..catalog import DatasetMetadata

class BaseConnector(ABC):
    """Base class for API connectors with rate limiting and caching"""
    
    def __init__(self, base_url: str, rate_limit: int = 60):
        self.base_url = base_url.rstrip('/')
        self.rate_limit = rate_limit
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour cache TTL
        self.logger = get_logger(f"{self.__class__.__name__}")
        self.logger.info(f"Initialized connector for {self.base_url} with rate limit of {rate_limit} requests per minute")
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.logger.debug("Created aiohttp client session")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.logger.debug("Closed aiohttp client session")
            
    @sleep_and_retry
    @limits(calls=1, period=1)  # Basic rate limiting
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a rate-limited API request with caching and validation"""
        if not self.session:
            self.logger.error("Connector must be used as async context manager")
            raise RuntimeError("Connector must be used as async context manager")
            
        # Check cache
        cache_key = f"{endpoint}:{str(params)}"
        if cache_key in self.cache:
            self.logger.debug(f"Cache hit for {endpoint}")
            return self.cache[cache_key]
            
        # Make request
        self.logger.debug(f"Making request to {endpoint} with params {params}")
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/{endpoint}", params=params) as response:
                response.raise_for_status()
                try:
                    data = await response.json()
                except Exception as e:
                    self.logger.error(f"Failed to parse JSON response from {endpoint}: {str(e)}")
                    return {}
                
            request_time = time.time() - start_time
            self.logger.debug(f"Request to {endpoint} completed in {request_time:.2f}s")
            
            # Validate that data is a dictionary or list
            if not isinstance(data, (dict, list)):
                self.logger.error(f"Invalid response format from {endpoint}: expected dict or list, got {type(data)}")
                return {}
                
            # Update cache
            self.cache[cache_key] = data
            return data
        except aiohttp.ClientError as e:
            self.logger.error(f"Request to {endpoint} failed: {str(e)}")
            return {}
        
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

    @abstractmethod
    async def convert_to_standard_metadata(self) -> List[DatasetMetadata]:
        """
        Convert connector-specific metadata to standard DatasetMetadata format
        
        This method should fetch the metadata from the API and convert it to a list of
        standardized DatasetMetadata objects that can be used by the DataDiscoveryService.
        
        Returns:
            List of DatasetMetadata objects representing all available datasets from this connector
        """
        pass 