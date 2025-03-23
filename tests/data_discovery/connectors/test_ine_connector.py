import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from modelforge.data_discovery.connectors.ine import INEConnector
from modelforge.data_discovery.models import DatasetMetadata


@pytest.fixture
def mock_ine_response():
    """Mock response from INE API"""
    return {
        "datasets": [
            {
                "id": "test-ine-001",
                "name": "Test INE Dataset",
                "url": "https://www.ine.es/api/test/001",
                "description": "Test INE dataset description",
                "frequency": "mensual",
                "update_date": "2023-06-01"
            },
            {
                "id": "test-ine-002",
                "name": "Test INE Dataset 2",
                "url": "https://www.ine.es/api/test/002",
                "description": "Test INE dataset 2 description",
                "frequency": "anual",
                "update_date": "2023-01-01"
            }
        ]
    }


@pytest.fixture
def mock_ine_schema_response():
    """Mock schema response from INE API"""
    return {
        "variables": [
            {"code": "id", "name": "Identifier", "type": "string"},
            {"code": "value", "name": "Value", "type": "float"},
            {"code": "date", "name": "Date", "type": "date"}
        ]
    }


@pytest.mark.asyncio
async def test_fetch_datasets(mock_ine_response):
    """Test fetching datasets from INE"""
    with patch.object(INEConnector, '_make_api_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_ine_response
        
        connector = INEConnector()
        datasets = await connector.fetch_datasets()
        
        assert len(datasets) == 2
        assert datasets[0]["id"] == "test-ine-001"
        assert datasets[1]["id"] == "test-ine-002"
        
        # Verify API was called correctly
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_dataset_schema(mock_ine_schema_response):
    """Test fetching dataset schema from INE"""
    with patch.object(INEConnector, '_make_api_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_ine_schema_response
        
        connector = INEConnector()
        schema = await connector._fetch_dataset_schema("test-ine-001")
        
        assert len(schema) == 3
        assert "id" in schema
        assert "value" in schema
        assert "date" in schema
        
        # Verify API was called with the right dataset ID
        mock_request.assert_called_once()
        args, _ = mock_request.call_args
        assert "test-ine-001" in args[0]


@pytest.mark.asyncio
async def test_convert_to_standard_metadata(mock_ine_response, mock_ine_schema_response):
    """Test converting INE data to standard metadata format"""
    with patch.object(INEConnector, '_make_api_request', new_callable=AsyncMock) as mock_request:
        # Setup mock to return different responses based on the URL
        def side_effect(url, *args, **kwargs):
            if "/catalogo" in url:
                return mock_ine_response
            else:
                return mock_ine_schema_response
        
        mock_request.side_effect = side_effect
        
        connector = INEConnector()
        metadata_list = await connector.convert_to_standard_metadata()
        
        assert len(metadata_list) == 2
        assert isinstance(metadata_list[0], DatasetMetadata)
        assert metadata_list[0].source == "INE"
        assert metadata_list[0].id == "test-ine-001"
        assert metadata_list[1].id == "test-ine-002"
        
        # Each dataset should have schema fields
        assert len(metadata_list[0].schema) > 0 