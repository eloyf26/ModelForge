import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from modelforge.intent_parser import parse_intent
from modelforge.data_discovery.catalog import DatasetCatalog
from modelforge.data_discovery.discovery_service import DiscoveryService
from modelforge.data_discovery.ine_connector import INEConnector

async def run_workflow():
    print("1. Starting Intent Parsing...")
    # Load OpenAI API key from .env
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Please set OPENAI_API_KEY in your .env file")

    # Parse the natural language description
    description = "Predict Spain's inflation rate for the next 3 months using economic indicators"
    print(f"\nInput description: {description}")
    
    spec = parse_intent(description)
    print("\nParsed ML Specification:")
    print(f"Task Type: {spec.task_type}")
    print(f"Target: {spec.target}")
    print(f"Features: {spec.features}")
    print(f"Metric: {spec.metric}")
    print(f"Horizon: {spec.horizon}")

    print("\n2. Starting Data Discovery...")
    # Initialize data discovery components
    catalog = DatasetCatalog()
    ine = INEConnector()
    discovery = DiscoveryService(catalog, ine)

    # Search for relevant datasets based on the specification
    search_query = f"{spec.target} spain"
    print(f"\nSearching for datasets with query: {search_query}")
    
    datasets = await discovery.search_datasets(search_query)
    print(f"\nFound {len(datasets)} relevant datasets:")
    
    for dataset in datasets:
        print(f"\nDataset: {dataset.name}")
        print(f"ID: {dataset.id}")
        print(f"Description: {dataset.description}")
        print(f"Tags: {dataset.tags}")
        print("Schema:", dataset.schema)
        print("---")

    # Get specific dataset data (IPC - Consumer Price Index)
    print("\n3. Fetching Actual Data...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # Last year of data
    
    print(f"\nFetching IPC data from {start_date.date()} to {end_date.date()}")
    data = await ine.get_dataset_data(
        dataset_id="IPC",
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d")
    )
    
    print("\nLatest IPC data points:")
    for entry in data[-5:]:  # Show last 5 entries
        print(entry)

if __name__ == "__main__":
    print("Starting ModelForge AI Workflow Example...")
    print("----------------------------------------")
    asyncio.run(run_workflow()) 