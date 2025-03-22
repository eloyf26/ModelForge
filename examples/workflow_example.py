import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from modelforge.intent_parser import parse_intent
from modelforge.data_discovery.catalog import DatasetCatalog
from modelforge.data_discovery.discovery_service import DataDiscoveryService
from modelforge.data_discovery.connectors.ine import INEConnector

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
    discovery = DataDiscoveryService([INEConnector()])

    async with discovery:
        # Search for relevant datasets based on the specification
        search_query = f"{spec.target} spain"
        print(f"\nSearching for datasets with query: {search_query}")
        
        try:
            datasets = await discovery.search_datasets(search_query)
            if not datasets:
                print("\nNo datasets found matching the search criteria.")
                return
                
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
            start_date = end_date - timedelta(days=365)
            
            print(f"\nFetching IPC data from {start_date.date()} to {end_date.date()}")
            data = await discovery._active_connectors[0].get_dataset_data(
                dataset_id="IPC",
                start_date=start_date,
                end_date=end_date
            )
            
            print("\nLatest IPC data points:")
            if data and len(data) > 0:
                for entry in data[-5:]:  # Show last 5 entries
                    print(entry)
            else:
                print("No data available for the specified time period")
        except Exception as e:
            print(f"Error fetching data: {e}")

if __name__ == "__main__":
    print("Starting ModelForge AI Workflow Example...")
    print("----------------------------------------")
    asyncio.run(run_workflow()) 