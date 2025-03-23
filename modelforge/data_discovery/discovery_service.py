from typing import List, Dict, Any, Type, Callable, Optional
import asyncio
from datetime import datetime

from .catalog import DatasetCatalog
from .models import DatasetMetadata, DatasetSchema
from .connectors import INEConnector, AEMETConnector, EurostatConnector
from .connectors.base import BaseConnector
from modelforge.logging.logger import get_logger

# Create logger for this module
logger = get_logger(__name__)

class DataDiscoveryService:
    """
    Main service for discovering and cataloging datasets.
    Must be used as an async context manager to properly initialize and clean up connectors.
    
    Example:
        async with DataDiscoveryService() as service:
            await service.refresh_catalog()
            datasets = service.search_datasets("query")
    """
    
    def __init__(self, use_persistent_storage: bool = False):
        """
        Initialize the data discovery service
        
        Args:
            use_persistent_storage: Whether to use Supabase for persistent storage
        """
        logger.info("Initializing DataDiscoveryService")
        self.catalog = DatasetCatalog(use_persistent_storage=use_persistent_storage)
        self.use_persistent_storage = use_persistent_storage
        
        # Set up connector classes but don't initialize them yet
        self.connectors = {
            'ine': INEConnector,
            'aemet': AEMETConnector,
            'eurostat': EurostatConnector,
        }
        
        # Will hold active connector instances when context is entered
        self.active_connectors = {}
        
    async def __aenter__(self):
        """Initialize all connectors when entering the context"""
        logger.info("Entering DataDiscoveryService context")
        
        # Initialize all connectors and enter their contexts
        for name, connector_class in self.connectors.items():
            logger.debug(f"Initializing connector: {name}")
            connector = connector_class()
            self.active_connectors[name] = await connector.__aenter__()
        
        # Load catalog from persistent storage if enabled
        if self.use_persistent_storage:
            logger.info("Loading catalog from persistent storage")
            await self.catalog.load_from_storage()
            
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up all connectors when exiting the context"""
        logger.info("Exiting DataDiscoveryService context")
        
        # Exit all connector contexts
        for name, connector in self.active_connectors.items():
            logger.debug(f"Closing connector: {name}")
            await connector.__aexit__(exc_type, exc_val, exc_tb)
            
        self.active_connectors = {}
        
    async def refresh_catalog(self) -> None:
        """Refresh the catalog by fetching latest metadata from all connectors"""
        if not self.active_connectors:
            raise RuntimeError("DataDiscoveryService must be used as an async context manager")
            
        logger.info("Refreshing dataset catalog")
            
        # Refresh all connectors in parallel
        logger.info(f"Starting parallel refresh of {len(self.active_connectors)} connectors")
        refresh_tasks = [
            self.refresh_connector(name, connector)
            for name, connector in self.active_connectors.items()
        ]
        
        all_datasets = await asyncio.gather(*refresh_tasks)
        
        # Update catalog
        total_datasets = 0
        for datasets in all_datasets:
            for dataset in datasets:
                self.catalog.add_dataset(dataset)
                total_datasets += 1
        
        logger.info(f"Catalog refresh complete, {total_datasets} datasets available")
        
        # Save to persistent storage if enabled
        if self.use_persistent_storage:
            logger.info("Saving catalog to persistent storage")
            await self.catalog.save_to_storage()
    
    async def refresh_connector(self, name: str, connector: BaseConnector) -> List[DatasetMetadata]:
        """
        Refresh a single connector by fetching its datasets and converting to standard metadata format
        
        Args:
            name: Connector name identifier
            connector: The connector instance to refresh
            
        Returns:
            List of standardized DatasetMetadata objects
        """
        logger.info(f"Refreshing connector: {name}")
        datasets = []
        try:
            # Get standardized metadata from connector
            datasets = await connector.convert_to_standard_metadata()
            logger.info(f"Successfully refreshed {name} connector, found {len(datasets)} datasets")
        except Exception as e:
            logger.error(f"Error refreshing connector {name}: {str(e)}")
            
        return datasets
                  
    def search_datasets(self, query: str, tags: List[str] = None) -> List[DatasetMetadata]:
        """Search for datasets matching query and tags"""
        logger.info(f"Searching datasets with query '{query}' and tags {tags}")
        results = self.catalog.search_datasets(query, tags)
        logger.info(f"Found {len(results)} matching datasets")
        return results
        
    def get_dataset_metadata(self, name: str) -> DatasetMetadata:
        """Get metadata for a specific dataset"""
        logger.info(f"Getting metadata for dataset '{name}'")
        return self.catalog.get_dataset(name)
        
    def list_all_datasets(self) -> List[DatasetMetadata]:
        """List all available datasets"""
        logger.info("Listing all datasets")
        datasets = self.catalog.list_datasets()
        logger.info(f"Found {len(datasets)} total datasets")
        return datasets
        
    @classmethod
    def add_connector(cls, name: str, connector_class: Type[BaseConnector]):
        """
        Register a new connector class with the service
        
        Args:
            name: Name to identify the connector
            connector_class: The connector class to register
        """
        cls.connectors[name] = connector_class 