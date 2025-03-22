import pytest
from aioresponses import aioresponses
from modelforge.data_discovery.discovery_service import DataDiscoveryService
from modelforge.data_discovery.connectors.ine import INEConnector

@pytest.fixture
def mock_responses():
    """Create mock responses for the INE API"""
    with aioresponses() as mocked:
        yield mocked

@pytest.fixture
def discovery_service():
    """Create a fresh discovery service for each test"""
    return DataDiscoveryService([INEConnector()])

@pytest.mark.asyncio
async def test_refresh_catalog(mock_responses, discovery_service):
    """Test refreshing the catalog from all connectors"""
    # Mock INE API responses
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES",
        payload={
            "operaciones": [
                {
                    "Id": "IPC",
                    "Nombre": "Consumer Price Index",
                    "Descripcion": "Monthly CPI data"
                }
            ]
        }
    )

    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/VARIABLES_OPERACION/IPC",
        payload={
            "variables": [
                {
                    "Id": "date",
                    "Nombre": "Reference date",
                    "Tipo": "datetime"
                },
                {
                    "Id": "value",
                    "Nombre": "Index value",
                    "Tipo": "float"
                }
            ]
        }
    )

    # Refresh catalog
    await discovery_service.refresh_catalog()

    # Verify catalog contents
    datasets = discovery_service.catalog.list_datasets()
    assert len(datasets) == 1
    assert datasets[0].id == "IPC"
    assert datasets[0].name == "Consumer Price Index"
    assert datasets[0].description == "Monthly CPI data"

@pytest.mark.asyncio
async def test_search_datasets(mock_responses, discovery_service):
    """Test searching datasets"""
    # First refresh catalog with mock data
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES",
        payload={
            "operaciones": [
                {
                    "Id": "IPC",
                    "Nombre": "Consumer Price Index",
                    "Descripcion": "Monthly CPI data"
                },
                {
                    "Id": "UNEMP",
                    "Nombre": "Unemployment Rate",
                    "Descripcion": "Monthly unemployment data"
                }
            ]
        }
    )

    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/VARIABLES_OPERACION/IPC",
        payload={
            "variables": [
                {
                    "Id": "value",
                    "Nombre": "Index value",
                    "Tipo": "float"
                }
            ]
        }
    )

    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/VARIABLES_OPERACION/UNEMP",
        payload={
            "variables": [
                {
                    "Id": "value",
                    "Nombre": "Rate value",
                    "Tipo": "float"
                }
            ]
        }
    )

    await discovery_service.refresh_catalog()

    # Search for datasets
    results = discovery_service.search_datasets("price")
    assert len(results) == 1
    assert results[0].id == "IPC"

    results = discovery_service.search_datasets("unemployment")
    assert len(results) == 1
    assert results[0].id == "UNEMP"

    results = discovery_service.search_datasets("nonexistent")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_get_dataset_metadata(mock_responses, discovery_service):
    """Test getting metadata for a specific dataset"""
    # First refresh catalog with mock data
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES",
        payload={
            "operaciones": [
                {
                    "Id": "IPC",
                    "Nombre": "Consumer Price Index",
                    "Descripcion": "Monthly CPI data"
                }
            ]
        }
    )

    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/VARIABLES_OPERACION/IPC",
        payload={
            "variables": [
                {
                    "Id": "value",
                    "Nombre": "Index value",
                    "Tipo": "float"
                }
            ]
        }
    )

    await discovery_service.refresh_catalog()

    # Get metadata for a specific dataset
    metadata = discovery_service.get_dataset_metadata("IPC")
    assert metadata.id == "IPC"
    assert metadata.name == "Consumer Price Index"
    assert metadata.description == "Monthly CPI data"

    # Try to get metadata for a nonexistent dataset
    with pytest.raises(KeyError):
        discovery_service.get_dataset_metadata("nonexistent") 