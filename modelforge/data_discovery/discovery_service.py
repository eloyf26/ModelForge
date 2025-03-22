from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from .catalog import DatasetCatalog, DatasetMetadata, DatasetSchema
from .connectors import INEConnector, AEMETConnector, EurostatConnector
from .connectors.base import BaseConnector

class DataDiscoveryService:
    """Main service for discovering and cataloging datasets"""
    
    def __init__(self, connectors: Optional[List[BaseConnector]] = None):
        self.catalog = DatasetCatalog()
        self.connectors = connectors or []
        self._active_connectors = []
        
    async def __aenter__(self):
        self._active_connectors = []
        for connector in self.connectors:
            await connector.__aenter__()
            self._active_connectors.append(connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for connector in self._active_connectors:
            await connector.__aexit__(exc_type, exc_val, exc_tb)
        self._active_connectors = []

    async def refresh_catalog(self) -> None:
        """Refresh the catalog by fetching latest metadata from all connectors"""
        async def refresh_connector(name: str, connector: Any) -> List[DatasetMetadata]:
            datasets = []
            async with connector as conn:
                metadata = await conn.get_metadata()
                
                # Handle INE API response format
                if 'operaciones' in metadata:
                    for dataset in metadata['operaciones']:
                        # Get schema information
                        schema_info = await conn.get_dataset_schema(dataset['Id'])
                        
                        # Convert to our schema format
                        schema = {}
                        for field in schema_info.get('variables', []):
                            schema[field['Id']] = DatasetSchema(
                                name=field['Id'],
                                data_type=field['Tipo'],
                                description=field.get('Nombre'),
                                is_nullable=True
                            )
                        
                        # Create dataset metadata
                        dataset_metadata = DatasetMetadata(
                            id=dataset['Id'],
                            name=dataset['Nombre'],
                            source=name,
                            endpoint=f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{dataset['Id']}",
                            schema=schema,
                            update_frequency='unknown',
                            last_updated=datetime.now(),
                            description=dataset.get('Descripcion'),
                            tags=[],
                            license=None,
                            rate_limit=self.connectors[name].rate_limit
                        )
                        datasets.append(dataset_metadata)
                else:
                    # Handle other API formats
                    for dataset in metadata.get('datasets', []):
                        # Get schema information
                        schema_info = await conn.get_dataset_schema(dataset['id'])
                        
                        # Convert to our schema format
                        schema = {}
                        for field in schema_info.get('variables', []):
                            schema[field['name']] = DatasetSchema(
                                name=field['name'],
                                data_type=field['type'],
                                description=field.get('description'),
                                is_nullable=field.get('nullable', True)
                            )
                        
                        # Create dataset metadata
                        dataset_metadata = DatasetMetadata(
                            id=dataset['id'],
                            name=dataset['name'],
                            source=name,
                            endpoint=dataset['endpoint'],
                            schema=schema,
                            update_frequency=dataset.get('frequency', 'unknown'),
                            last_updated=datetime.fromisoformat(dataset.get('last_updated', datetime.now().isoformat())),
                            description=dataset.get('description'),
                            tags=dataset.get('tags', []),
                            license=dataset.get('license'),
                            rate_limit=self.connectors[name].rate_limit
                        )
                        datasets.append(dataset_metadata)
                    
            return datasets
            
        # Refresh all connectors in parallel
        refresh_tasks = [
            refresh_connector(name, connector)
            for name, connector in self.connectors.items()
        ]
        
        all_datasets = await asyncio.gather(*refresh_tasks)
        
        # Update catalog
        for datasets in all_datasets:
            for dataset in datasets:
                self.catalog.add_dataset(dataset)
                
    async def search_datasets(self, query: str):
        if not self._active_connectors:
            raise RuntimeError("DataDiscoveryService must be used as async context manager")
        
        results = []
        for connector in self._active_connectors:
            result = await connector.search_datasets(query)
            results.extend(result)
        return results
        
    def get_dataset_metadata(self, name: str) -> DatasetMetadata:
        """Get metadata for a specific dataset"""
        return self.catalog.get_dataset(name)
        
    def list_all_datasets(self) -> List[DatasetMetadata]:
        """List all available datasets"""
        return self.catalog.list_datasets() 