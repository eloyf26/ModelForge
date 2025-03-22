import pytest
from datetime import datetime
from modelforge.data_discovery.catalog import DatasetCatalog, DatasetMetadata, DatasetSchema

@pytest.fixture
def catalog():
    """Create a fresh catalog for each test"""
    return DatasetCatalog()

@pytest.fixture
def sample_dataset():
    """Create a sample dataset metadata"""
    return DatasetMetadata(
        id="IPC",
        name="Consumer Price Index",
        source="ine",
        endpoint="https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC",
        schema={
            "date": DatasetSchema(
                name="date",
                data_type="datetime",
                description="Reference date"
            ),
            "value": DatasetSchema(
                name="value",
                data_type="float",
                description="Index value"
            )
        },
        update_frequency="monthly",
        last_updated=datetime.now(),
        description="Monthly CPI data",
        tags=["economic", "inflation"]
    )

def test_add_and_get_dataset(catalog, sample_dataset):
    """Test adding and retrieving a dataset"""
    catalog.add_dataset(sample_dataset)
    retrieved = catalog.get_dataset("IPC")
    assert retrieved == sample_dataset

def test_search_datasets_by_name(catalog, sample_dataset):
    """Test searching datasets by name"""
    catalog.add_dataset(sample_dataset)
    results = catalog.search_datasets("price")
    assert len(results) == 1
    assert results[0] == sample_dataset

def test_search_datasets_by_description(catalog, sample_dataset):
    """Test searching datasets by description"""
    catalog.add_dataset(sample_dataset)
    results = catalog.search_datasets("cpi")
    assert len(results) == 1
    assert results[0] == sample_dataset

def test_search_datasets_by_tags(catalog, sample_dataset):
    """Test searching datasets by tags"""
    catalog.add_dataset(sample_dataset)
    results = catalog.search_datasets("inflation")
    assert len(results) == 1
    assert results[0] == sample_dataset

def test_search_datasets_no_match(catalog, sample_dataset):
    """Test searching datasets with no matches"""
    catalog.add_dataset(sample_dataset)
    results = catalog.search_datasets("nonexistent")
    assert len(results) == 0

def test_list_datasets(catalog, sample_dataset):
    """Test listing all datasets"""
    catalog.add_dataset(sample_dataset)
    datasets = catalog.list_datasets()
    assert len(datasets) == 1
    assert datasets[0] == sample_dataset

def test_remove_dataset(catalog, sample_dataset):
    """Test removing a dataset"""
    catalog.add_dataset(sample_dataset)
    catalog.remove_dataset("IPC")
    with pytest.raises(KeyError):
        catalog.get_dataset("IPC") 