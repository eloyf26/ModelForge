from typing import Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

class DatasetSchema(BaseModel):
    """Schema definition for a dataset field"""
    name: str
    data_type: str
    description: Optional[str] = None
    is_nullable: bool = True

class DatasetMetadata(BaseModel):
    """Metadata for a single dataset"""
    id: str
    name: str
    source: str
    endpoint: HttpUrl
    schema: Dict[str, DatasetSchema]
    update_frequency: str
    last_updated: datetime
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    license: Optional[str] = None
    rate_limit: Optional[int] = None  # requests per minute

class DatasetCatalog:
    """Manages the catalog of available datasets"""
    def __init__(self):
        self._datasets: Dict[str, DatasetMetadata] = {}
        self._cache_ttl: int = 3600  # 1 hour cache TTL

    def add_dataset(self, metadata: DatasetMetadata) -> None:
        """Add a dataset to the catalog"""
        self._datasets[metadata.id] = metadata

    def get_dataset(self, id: str) -> DatasetMetadata:
        """Retrieve dataset metadata by ID"""
        if id not in self._datasets:
            raise KeyError(f"Dataset with ID '{id}' not found")
        return self._datasets[id]

    def search_datasets(self, query: str, tags: Optional[List[str]] = None) -> List[DatasetMetadata]:
        """Search datasets by query string and optional tags"""
        results = []
        query = query.lower()
        
        for dataset in self._datasets.values():
            # Match by name, description, or tags
            if (query in dataset.name.lower() or
                (dataset.description and query in dataset.description.lower()) or
                any(query in tag.lower() for tag in dataset.tags)):
                
                # Filter by tags if provided
                if tags and not all(tag in dataset.tags for tag in tags):
                    continue
                    
                results.append(dataset)
                
        return results

    def list_datasets(self) -> List[DatasetMetadata]:
        """List all datasets in the catalog"""
        return list(self._datasets.values())

    def remove_dataset(self, id: str) -> None:
        """Remove a dataset from the catalog"""
        if id in self._datasets:
            del self._datasets[id] 