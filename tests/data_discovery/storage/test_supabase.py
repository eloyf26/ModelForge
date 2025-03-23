import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json
from datetime import datetime

from modelforge.data_discovery.storage.supabase import SupabaseStorage
from modelforge.data_discovery.models import DatasetMetadata


@pytest.fixture
def mock_supabase_client():
    """Mock for Supabase client"""
    mock_client = MagicMock()
    mock_client.table.return_value = mock_client
    mock_client.select.return_value = mock_client
    mock_client.eq.return_value = mock_client
    mock_client.upsert.return_value = mock_client
    mock_client.execute = AsyncMock()
    return mock_client


@pytest.mark.asyncio
async def test_initialize_connection(mock_supabase_client):
    """Test initializing Supabase connection"""
    with patch('modelforge.data_discovery.storage.supabase.create_client', return_value=mock_supabase_client):
        storage = SupabaseStorage()
        await storage._initialize_connection()
        
        assert storage.client is mock_supabase_client


@pytest.mark.asyncio
async def test_save_datasets(sample_datasets_list, mock_supabase_client):
    """Test saving datasets to Supabase"""
    with patch('modelforge.data_discovery.storage.supabase.create_client', return_value=mock_supabase_client):
        storage = SupabaseStorage()
        await storage._initialize_connection()
        
        # Convert datetime objects to strings for the comparison
        serialized_datasets = []
        for dataset in sample_datasets_list:
            # Convert to dict and manually handle datetime
            dataset_dict = dataset.model_dump()
            dataset_dict["last_updated"] = dataset_dict["last_updated"].isoformat()
            serialized_datasets.append(dataset_dict)
        
        await storage.save_datasets(sample_datasets_list)
        
        # Verify client was called correctly
        mock_supabase_client.table.assert_called_with('datasets')
        mock_supabase_client.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_load_datasets(sample_datasets_list, mock_supabase_client):
    """Test loading datasets from Supabase"""
    # Convert datasets to dict representation that would come from Supabase
    datasets_data = []
    for dataset in sample_datasets_list:
        dataset_dict = dataset.model_dump()
        # Convert to ISO format for storage simulation
        dataset_dict["last_updated"] = dataset_dict["last_updated"].isoformat()
        # Convert schema to JSON string for storage simulation
        dataset_dict["schema"] = json.dumps(
            {k: v.model_dump() for k, v in dataset.schema.items()}
        )
        datasets_data.append(dataset_dict)
    
    mock_response = MagicMock()
    mock_response.data = datasets_data
    mock_supabase_client.execute.return_value = mock_response
    
    with patch('modelforge.data_discovery.storage.supabase.create_client', return_value=mock_supabase_client):
        storage = SupabaseStorage()
        await storage._initialize_connection()
        
        loaded_datasets = await storage.load_datasets()
        
        # Check we got the expected number of datasets
        assert len(loaded_datasets) == len(sample_datasets_list)
        # Verify they are DatasetMetadata objects
        assert all(isinstance(ds, DatasetMetadata) for ds in loaded_datasets)
        # Check IDs match what we expect
        assert sorted([ds.id for ds in loaded_datasets]) == sorted([ds.id for ds in sample_datasets_list])
        
        # Verify client was called correctly
        mock_supabase_client.table.assert_called_with('datasets')
        mock_supabase_client.select.assert_called_once()
        mock_supabase_client.execute.assert_called_once() 