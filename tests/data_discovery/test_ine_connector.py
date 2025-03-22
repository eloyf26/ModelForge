import pytest
from datetime import datetime
from aioresponses import aioresponses
from modelforge.data_discovery.connectors.ine import INEConnector

@pytest.fixture
def mock_responses():
    """Create mock responses for the INE API"""
    with aioresponses() as mocked:
        yield mocked

@pytest.fixture
def ine_connector():
    """Create a fresh INE connector for each test"""
    return INEConnector()

@pytest.mark.asyncio
async def test_get_metadata(mock_responses, ine_connector):
    """Test getting metadata from INE API"""
    mock_data = {
        "operaciones": [
            {
                "Id": "IPC",
                "Nombre": "Consumer Price Index",
                "Descripcion": "Monthly CPI data"
            }
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.get_metadata()
        assert result == mock_data

@pytest.mark.asyncio
async def test_search_datasets(mock_responses, ine_connector):
    """Test searching datasets in INE API"""
    mock_data = {
        "resultados": [
            {
                "Id": "IPC",
                "Nombre": "Consumer Price Index",
                "Relevancia": 0.9
            }
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/Search?q=inflation",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.search_datasets("inflation")
        assert result == mock_data

@pytest.mark.asyncio
async def test_get_dataset_schema(mock_responses, ine_connector):
    """Test getting dataset schema from INE API"""
    mock_data = {
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
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/VARIABLES_OPERACION/IPC",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.get_dataset_schema("IPC")
        assert result == mock_data

@pytest.mark.asyncio
async def test_get_dataset_data_with_dates(mock_responses, ine_connector):
    """Test getting data with date range"""
    mock_data = {
        "Data": [
            {
                "Fecha": "2024-01-01",
                "Valor": 103.5
            }
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC?date=20240101:20240131",
        payload=mock_data
    )

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)

    async with ine_connector as conn:
        result = await conn.get_dataset_data("IPC", start_date=start_date, end_date=end_date)
        assert result == mock_data

@pytest.mark.asyncio
async def test_get_dataset_data_with_last_n(mock_responses, ine_connector):
    """Test getting last N periods of data"""
    mock_data = {
        "Data": [
            {
                "Fecha": "2024-01-01",
                "Valor": 103.5
            }
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC?nult=12",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.get_dataset_data("IPC", last_n=12)
        assert result == mock_data

@pytest.mark.asyncio
async def test_get_dataset_data_with_options(mock_responses, ine_connector):
    """Test getting data with additional options"""
    mock_data = {
        "Data": [
            {
                "Fecha": "2024-01-01",
                "Valor": 103.5,
                "Metadata": {"unit": "index"}
            }
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC?p=1&det=2&tip=AM",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.get_dataset_data(
            "IPC",
            periodicity=1,  # Monthly
            detail_level=2,
            friendly_format=True,
            include_metadata=True
        )
        assert result == mock_data

@pytest.mark.asyncio
async def test_get_series_by_filters(mock_responses, ine_connector):
    """Test getting data series using filters"""
    mock_data = {
        "Series": [
            {
                "Id": "IPC2016_1_1",
                "Nombre": "CPI Madrid",
                "Data": [{"Fecha": "2024-01-01", "Valor": 103.5}]
            }
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/DATOS_METADATAOPERACION/IPC?g1=115:29&p=1&nult=12",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.get_series_by_filters(
            "IPC",
            filters={"115": "29"},  # Madrid province
            periodicity=1,  # Monthly
            last_n=12
        )
        assert result == mock_data

@pytest.mark.asyncio
async def test_get_available_periodicities(mock_responses, ine_connector):
    """Test getting available periodicities"""
    mock_data = {
        "periodicidades": [
            {"Id": 1, "Nombre": "Monthly"},
            {"Id": 3, "Nombre": "Quarterly"},
            {"Id": 12, "Nombre": "Yearly"}
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/PERIODICIDADES",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.get_available_periodicities()
        assert result == mock_data

@pytest.mark.asyncio
async def test_get_variable_values(mock_responses, ine_connector):
    """Test getting variable values"""
    mock_data = {
        "valores": [
            {"Id": "29", "Nombre": "Madrid"},
            {"Id": "08", "Nombre": "Barcelona"}
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/VALORES_VARIABLEOPERACION/115/IPC",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.get_variable_values("IPC", "115")
        assert result == mock_data

@pytest.mark.asyncio
async def test_get_series_metadata(mock_responses, ine_connector):
    """Test getting series metadata"""
    mock_data = {
        "Series": [
            {
                "Id": "IPC2016_1_1",
                "Nombre": "CPI Madrid",
                "Periodicidad": "Monthly",
                "UnidadMedida": "Index 2016=100"
            }
        ]
    }
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/SERIE_METADATAOPERACION/IPC?g1=115:29&p=1&tip=A",
        payload=mock_data
    )

    async with ine_connector as conn:
        result = await conn.get_series_metadata(
            "IPC",
            filters={"115": "29"},  # Madrid province
            periodicity=1,  # Monthly
            friendly_format=True
        )
        assert result == mock_data

@pytest.mark.asyncio
async def test_rate_limiting(mock_responses, ine_connector):
    """Test that rate limiting is working"""
    mock_data = {"data": "test"}
    mock_responses.get(
        "https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES",
        payload=mock_data
    )

    async with ine_connector as conn:
        start_time = datetime.now()
        # Make 3 requests that should be rate limited
        await conn.get_metadata()
        await conn.get_metadata()
        await conn.get_metadata()
        end_time = datetime.now()

        # Should take at least 2 seconds due to rate limiting (1 req/sec)
        duration = (end_time - start_time).total_seconds()
        assert duration >= 2 