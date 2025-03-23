import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import HttpUrl

from modelforge.data_discovery.models import DatasetMetadata, DatasetSchema
from modelforge.data_discovery.storage.supabase import SupabaseStorage
from modelforge.data_discovery.catalog import DatasetCatalog
from modelforge.data_discovery.connectors.base import BaseConnector


@pytest.fixture
def sample_dataset_schema():
    """Fixture for a sample dataset schema"""
    return {
        "id": DatasetSchema(name="id", data_type="string", description="Identifier", is_nullable=False),
        "value": DatasetSchema(name="value", data_type="float", description="Value", is_nullable=True),
        "date": DatasetSchema(name="date", data_type="date", description="Date", is_nullable=False)
    }


@pytest.fixture
def sample_dataset_metadata(sample_dataset_schema):
    """Fixture for a sample dataset metadata"""
    return DatasetMetadata(
        id="test-dataset-001",
        name="Test Dataset",
        source="test_source",
        endpoint=HttpUrl("https://example.com/api/data"),
        schema=sample_dataset_schema,
        update_frequency="daily",
        last_updated=datetime.now(),
        description="A test dataset for unit tests",
        tags=["test", "sample"],
        license="MIT",
        rate_limit=100
    )


@pytest.fixture
def sample_datasets_list(sample_dataset_metadata):
    """Fixture for a list of sample datasets"""
    datasets = [
        sample_dataset_metadata,
        DatasetMetadata(
            id="test-dataset-002",
            name="Another Test Dataset",
            source="test_source",
            endpoint=HttpUrl("https://example.com/api/data2"),
            schema=sample_dataset_metadata.schema,
            update_frequency="weekly",
            last_updated=datetime.now(),
            description="Another test dataset",
            tags=["test", "another"],
            license="Apache-2.0",
            rate_limit=50
        )
    ]
    return datasets


@pytest.fixture
def mock_supabase_storage():
    """Mock for SupabaseStorage"""
    with patch('modelforge.data_discovery.storage.supabase.SupabaseStorage') as mock:
        storage_instance = mock.return_value
        storage_instance.load_datasets = AsyncMock(return_value=[])
        storage_instance.save_datasets = AsyncMock()
        yield storage_instance


@pytest.fixture
def mock_connector():
    """Mock for BaseConnector"""
    connector = MagicMock(spec=BaseConnector)
    connector.__aenter__ = AsyncMock(return_value=connector)
    connector.__aexit__ = AsyncMock(return_value=None)
    connector.convert_to_standard_metadata = AsyncMock(return_value=[])
    return connector


@pytest.fixture
def mock_catalog():
    """Mock for DatasetCatalog"""
    catalog = MagicMock(spec=DatasetCatalog)
    catalog.load_from_storage = AsyncMock()
    catalog.save_to_storage = AsyncMock()
    catalog.search_datasets.return_value = []
    catalog.list_datasets.return_value = []
    return catalog 