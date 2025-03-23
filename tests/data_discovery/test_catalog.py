import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from modelforge.data_discovery.catalog import DatasetCatalog
from modelforge.data_discovery.models import DatasetMetadata


@pytest.mark.asyncio
async def test_catalog_init_no_storage():
    """Test initializing catalog without persistent storage"""
    catalog = DatasetCatalog(use_persistent_storage=False)
    assert catalog._storage is None
    assert catalog._use_persistent_storage is False


@pytest.mark.asyncio
async def test_catalog_init_with_storage(mock_supabase_storage):
    """Test initializing catalog with persistent storage"""
    with patch('modelforge.data_discovery.catalog.SupabaseStorage', return_value=mock_supabase_storage):
        catalog = DatasetCatalog(use_persistent_storage=True)
        assert catalog._storage is not None
        assert catalog._use_persistent_storage is True


@pytest.mark.asyncio
async def test_add_and_get_dataset(sample_dataset_metadata):
    """Test adding and retrieving a dataset"""
    catalog = DatasetCatalog()
    catalog.add_dataset(sample_dataset_metadata)
    
    # Retrieve and verify
    retrieved = catalog.get_dataset(sample_dataset_metadata.id)
    assert retrieved.id == sample_dataset_metadata.id
    assert retrieved.name == sample_dataset_metadata.name
    assert retrieved.source == sample_dataset_metadata.source


@pytest.mark.asyncio
async def test_get_dataset_not_found():
    """Test retrieving a non-existent dataset"""
    catalog = DatasetCatalog()
    
    with pytest.raises(KeyError):
        catalog.get_dataset("non-existent-id")


@pytest.mark.asyncio
async def test_search_datasets(sample_datasets_list):
    """Test searching datasets by query string"""
    catalog = DatasetCatalog()
    
    # Add sample datasets
    for dataset in sample_datasets_list:
        catalog.add_dataset(dataset)
    
    # Search with a query that should match one dataset
    results = catalog.search_datasets("another")
    assert len(results) == 1
    assert results[0].id == "test-dataset-002"
    
    # Search with a query that should match both datasets
    results = catalog.search_datasets("test")
    assert len(results) == 2
    
    # Search with a query that should match no datasets
    results = catalog.search_datasets("nonexistent")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_datasets_with_tags(sample_datasets_list):
    """Test searching datasets by query string and tags"""
    catalog = DatasetCatalog()
    
    # Add sample datasets
    for dataset in sample_datasets_list:
        catalog.add_dataset(dataset)
    
    # Search with a tag that should match one dataset
    results = catalog.search_datasets("test", tags=["another"])
    assert len(results) == 1
    assert results[0].id == "test-dataset-002"
    
    # Search with a tag that should match both datasets
    results = catalog.search_datasets("test", tags=["test"])
    assert len(results) == 2
    
    # Search with a tag that should match no datasets
    results = catalog.search_datasets("test", tags=["nonexistent"])
    assert len(results) == 0


@pytest.mark.asyncio
async def test_list_datasets(sample_datasets_list):
    """Test listing all datasets"""
    catalog = DatasetCatalog()
    
    # Add sample datasets
    for dataset in sample_datasets_list:
        catalog.add_dataset(dataset)
    
    # List all datasets
    results = catalog.list_datasets()
    assert len(results) == 2
    
    # Verify dataset IDs
    dataset_ids = [dataset.id for dataset in results]
    assert "test-dataset-001" in dataset_ids
    assert "test-dataset-002" in dataset_ids


@pytest.mark.asyncio
async def test_remove_dataset(sample_dataset_metadata):
    """Test removing a dataset"""
    catalog = DatasetCatalog()
    catalog.add_dataset(sample_dataset_metadata)
    
    # Verify dataset exists
    assert catalog.get_dataset(sample_dataset_metadata.id).id == sample_dataset_metadata.id
    
    # Remove dataset
    catalog.remove_dataset(sample_dataset_metadata.id)
    
    # Verify dataset is removed
    with pytest.raises(KeyError):
        catalog.get_dataset(sample_dataset_metadata.id)


@pytest.mark.asyncio
async def test_load_from_storage(sample_datasets_list, mock_supabase_storage):
    """Test loading datasets from storage"""
    mock_supabase_storage.load_datasets.return_value = sample_datasets_list
    
    with patch('modelforge.data_discovery.catalog.SupabaseStorage', return_value=mock_supabase_storage):
        catalog = DatasetCatalog(use_persistent_storage=True)
        await catalog.load_from_storage()
        
        # Verify storage was called
        mock_supabase_storage.load_datasets.assert_called_once()
        
        # Verify datasets were loaded
        assert len(catalog.list_datasets()) == 2
        assert catalog.get_dataset("test-dataset-001").id == "test-dataset-001"
        assert catalog.get_dataset("test-dataset-002").id == "test-dataset-002"


@pytest.mark.asyncio
async def test_save_to_storage(sample_datasets_list, mock_supabase_storage):
    """Test saving datasets to storage"""
    with patch('modelforge.data_discovery.catalog.SupabaseStorage', return_value=mock_supabase_storage):
        catalog = DatasetCatalog(use_persistent_storage=True)
        
        # Add sample datasets
        for dataset in sample_datasets_list:
            catalog.add_dataset(dataset)
        
        await catalog.save_to_storage()
        
        # Verify storage was called with the right datasets
        mock_supabase_storage.save_datasets.assert_called_once()
        saved_datasets = mock_supabase_storage.save_datasets.call_args[0][0]
        assert len(saved_datasets) == 2
        assert {ds.id for ds in saved_datasets} == {"test-dataset-001", "test-dataset-002"} 