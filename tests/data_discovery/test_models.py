import pytest
from datetime import datetime
from pydantic import HttpUrl

from modelforge.data_discovery.models import DatasetSchema, DatasetMetadata


def test_dataset_schema_creation():
    """Test DatasetSchema creation"""
    schema = DatasetSchema(
        name="test_field",
        data_type="string",
        description="A test field",
        is_nullable=False
    )
    
    assert schema.name == "test_field"
    assert schema.data_type == "string"
    assert schema.description == "A test field"
    assert schema.is_nullable is False


def test_dataset_metadata_creation(sample_dataset_schema):
    """Test DatasetMetadata creation"""
    metadata = DatasetMetadata(
        id="test-dataset-123",
        name="Test Dataset",
        source="test_source",
        endpoint=HttpUrl("https://example.com/api/test"),
        schema=sample_dataset_schema,
        update_frequency="daily",
        last_updated=datetime.now(),
        description="Test dataset description",
        tags=["test", "dataset"],
        license="MIT",
        rate_limit=60
    )
    
    assert metadata.id == "test-dataset-123"
    assert metadata.name == "Test Dataset"
    assert metadata.source == "test_source"
    assert str(metadata.endpoint) == "https://example.com/api/test"
    assert len(metadata.schema) == 3
    assert "id" in metadata.schema
    assert "value" in metadata.schema
    assert "date" in metadata.schema
    assert metadata.update_frequency == "daily"
    assert isinstance(metadata.last_updated, datetime)
    assert metadata.description == "Test dataset description"
    assert metadata.tags == ["test", "dataset"]
    assert metadata.license == "MIT"
    assert metadata.rate_limit == 60


def test_dataset_metadata_defaults():
    """Test DatasetMetadata with minimal required fields"""
    # Create a minimal schema for testing
    schema = {
        "id": DatasetSchema(name="id", data_type="string", is_nullable=False)
    }
    
    metadata = DatasetMetadata(
        id="minimal-test",
        name="Minimal Test",
        source="test",
        endpoint=HttpUrl("https://example.com/minimal"),
        schema=schema,
        update_frequency="monthly",
        last_updated=datetime.now()
    )
    
    # Check that optional fields have their default values
    assert metadata.description is None
    assert metadata.tags == []
    assert metadata.license is None
    assert metadata.rate_limit is None 