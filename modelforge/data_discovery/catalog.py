from typing import Dict, List, Optional
from .models import DatasetMetadata, DatasetSchema
from .storage.supabase import SupabaseStorage

class DatasetCatalog:
    """Manages the catalog of available datasets"""
    def __init__(self, use_persistent_storage: bool = False):
        self._datasets: Dict[str, DatasetMetadata] = {}
        self._cache_ttl: int = 3600  # 1 hour cache TTL
        self._use_persistent_storage = use_persistent_storage
        self._storage = SupabaseStorage() if use_persistent_storage else None

    async def load_from_storage(self) -> None:
        """Load datasets from persistent storage if enabled"""
        if not self._use_persistent_storage or not self._storage:
            return
            
        datasets = await self._storage.load_datasets()
        for dataset in datasets:
            self._datasets[dataset.id] = dataset

    async def save_to_storage(self) -> None:
        """Save datasets to persistent storage if enabled"""
        if not self._use_persistent_storage or not self._storage:
            return
            
        await self._storage.save_datasets(list(self._datasets.values()))

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