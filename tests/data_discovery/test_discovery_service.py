import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from modelforge.data_discovery.discovery_service import DataDiscoveryService
from modelforge.data_discovery.connectors.base import BaseConnector


@pytest.fixture
def mock_connectors():
    """Mock for all connectors"""
    ine_connector = MagicMock(spec=BaseConnector)
    ine_connector.__aenter__ = AsyncMock(return_value=ine_connector)
    ine_connector.__aexit__ = AsyncMock(return_value=None)
    ine_connector.convert_to_standard_metadata = AsyncMock(return_value=[])
    
    aemet_connector = MagicMock(spec=BaseConnector)
    aemet_connector.__aenter__ = AsyncMock(return_value=aemet_connector)
    aemet_connector.__aexit__ = AsyncMock(return_value=None)
    aemet_connector.convert_to_standard_metadata = AsyncMock(return_value=[])
    
    eurostat_connector = MagicMock(spec=BaseConnector)
    eurostat_connector.__aenter__ = AsyncMock(return_value=eurostat_connector)
    eurostat_connector.__aexit__ = AsyncMock(return_value=None)
    eurostat_connector.convert_to_standard_metadata = AsyncMock(return_value=[])
    
    return {
        'ine': ine_connector,
        'aemet': aemet_connector,
        'eurostat': eurostat_connector
    }


@pytest.mark.asyncio
async def test_service_context_manager(mock_connectors):
    """Test the service as a context manager"""
    # Mock connector classes to return specific mock instances
    with patch('modelforge.data_discovery.discovery_service.INEConnector', return_value=mock_connectors['ine']), \
         patch('modelforge.data_discovery.discovery_service.AEMETConnector', return_value=mock_connectors['aemet']), \
         patch('modelforge.data_discovery.discovery_service.EurostatConnector', return_value=mock_connectors['eurostat']):
        
        async with DataDiscoveryService() as service:
            assert len(service.active_connectors) == 3
            assert service.active_connectors['ine'] == mock_connectors['ine']
            assert service.active_connectors['aemet'] == mock_connectors['aemet']
            assert service.active_connectors['eurostat'] == mock_connectors['eurostat']
        
        # Verify all connectors were properly exited
        for name, connector in mock_connectors.items():
            connector.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_connector(sample_datasets_list):
    """Test refreshing a single connector"""
    connector = MagicMock(spec=BaseConnector)
    connector.convert_to_standard_metadata = AsyncMock(return_value=sample_datasets_list)
    
    service = DataDiscoveryService()
    result = await service.refresh_connector("test", connector)
    
    assert result == sample_datasets_list
    connector.convert_to_standard_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_connector_error():
    """Test handling errors when refreshing a connector"""
    connector = MagicMock(spec=BaseConnector)
    connector.convert_to_standard_metadata = AsyncMock(side_effect=Exception("Test error"))
    
    service = DataDiscoveryService()
    result = await service.refresh_connector("test", connector)
    
    # Should return empty list on error
    assert result == []
    connector.convert_to_standard_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_catalog(mock_connectors, sample_datasets_list, mock_catalog):
    """Test refreshing the entire catalog"""
    # Make one connector return actual datasets
    mock_connectors['ine'].convert_to_standard_metadata.return_value = sample_datasets_list
    
    with patch('modelforge.data_discovery.discovery_service.INEConnector', return_value=mock_connectors['ine']), \
         patch('modelforge.data_discovery.discovery_service.AEMETConnector', return_value=mock_connectors['aemet']), \
         patch('modelforge.data_discovery.discovery_service.EurostatConnector', return_value=mock_connectors['eurostat']), \
         patch('modelforge.data_discovery.discovery_service.DatasetCatalog', return_value=mock_catalog):
        
        service = DataDiscoveryService()
        service.active_connectors = {
            'ine': mock_connectors['ine'],
            'aemet': mock_connectors['aemet'],
            'eurostat': mock_connectors['eurostat']
        }
        
        await service.refresh_catalog()
        
        # Verify all connectors were called
        for connector in mock_connectors.values():
            connector.convert_to_standard_metadata.assert_called_once()
        
        # Verify datasets were added to catalog
        assert mock_catalog.add_dataset.call_count == len(sample_datasets_list)
        for i, dataset in enumerate(sample_datasets_list):
            mock_catalog.add_dataset.assert_any_call(dataset)


@pytest.mark.asyncio
async def test_service_search_datasets(mock_catalog):
    """Test searching for datasets"""
    with patch('modelforge.data_discovery.discovery_service.DatasetCatalog', return_value=mock_catalog):
        service = DataDiscoveryService()
        service.search_datasets("test query", tags=["tag1", "tag2"])
        
        # Verify catalog search was called with right arguments
        mock_catalog.search_datasets.assert_called_once_with("test query", ["tag1", "tag2"])


@pytest.mark.asyncio
async def test_get_dataset_metadata(mock_catalog, sample_dataset_metadata):
    """Test getting metadata for a specific dataset"""
    mock_catalog.get_dataset.return_value = sample_dataset_metadata
    
    with patch('modelforge.data_discovery.discovery_service.DatasetCatalog', return_value=mock_catalog):
        service = DataDiscoveryService()
        result = service.get_dataset_metadata("test-dataset-001")
        
        # Verify catalog get was called and returned the right dataset
        mock_catalog.get_dataset.assert_called_once_with("test-dataset-001")
        assert result == sample_dataset_metadata


@pytest.mark.asyncio
async def test_list_all_datasets(mock_catalog, sample_datasets_list):
    """Test listing all datasets"""
    mock_catalog.list_datasets.return_value = sample_datasets_list
    
    with patch('modelforge.data_discovery.discovery_service.DatasetCatalog', return_value=mock_catalog):
        service = DataDiscoveryService()
        result = service.list_all_datasets()
        
        # Verify catalog list was called and returned the right datasets
        mock_catalog.list_datasets.assert_called_once()
        assert result == sample_datasets_list


@pytest.mark.asyncio
async def test_add_connector():
    """Test adding a new connector"""
    # Create a custom connector class
    class TestConnector(BaseConnector):
        # Add mocks for abstract methods
        def __init__(self, *args, **kwargs):
            super().__init__("https://example.com")
            self.get_metadata = AsyncMock(return_value={})
            self.search_datasets = AsyncMock(return_value={})
            self.get_dataset_schema = AsyncMock(return_value={})
            
        async def fetch_datasets(self):
            return []
        
        async def convert_to_standard_metadata(self):
            return []
    
    # Add class attribute for test
    if not hasattr(DataDiscoveryService, 'connectors'):
        DataDiscoveryService.connectors = {}
        
    # Add the connector to the service
    DataDiscoveryService.add_connector("test", TestConnector)
    
    # Verify connector was added
    assert "test" in DataDiscoveryService.connectors
    assert DataDiscoveryService.connectors["test"] == TestConnector
    
    # Clean up after test
    del DataDiscoveryService.connectors["test"] 