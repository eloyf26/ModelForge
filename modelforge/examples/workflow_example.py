import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from modelforge.intent_parser import parse_intent
from modelforge.data_discovery.catalog import DatasetCatalog
from modelforge.data_discovery.discovery_service import DataDiscoveryService
from modelforge.data_discovery.connectors.ine import INEConnector
from modelforge.logging.logger import get_logger

# Create logger for this module
logger = get_logger(__name__)

async def run_workflow():
    logger.info("1. Starting Intent Parsing...")
    # Load OpenAI API key from .env
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not found in .env file - skipping intent parsing")
        # Continue with the example anyway, not critical for this demo

    logger.info("2. Starting Data Discovery...")
    # Initialize data discovery as a context manager
    async with DataDiscoveryService() as discovery:
        try:
            # Refresh the catalog to fetch the latest metadata
            await discovery.refresh_catalog()
            
            # Example 1: Search for Spain-related datasets
            search_query = "Spain"
            logger.info(f"Searching for datasets with query: {search_query}")
            
            datasets = discovery.search_datasets(search_query)
            logger.info(f"Found {len(datasets)} datasets related to Spain:")
            
            if len(datasets) > 0:
                for dataset in datasets:
                    logger.info(f"Dataset: {dataset.name}")
                    logger.debug(f"ID: {dataset.id}")
                    logger.debug(f"Description: {dataset.description}")
                    logger.debug(f"Tags: {dataset.tags}")
                    logger.debug(f"Schema: {dataset.schema}")
                    logger.debug("---")
            else:
                logger.info("No datasets found matching the Spain query.")           

            # Try to get the INE connector to fetch data
            ine_connector = discovery.active_connectors.get('ine')
            if ine_connector:
                try:
                    # Get specific dataset data (IPC - Consumer Price Index)
                    logger.info("3. Fetching Actual Data from INE...")
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=365)  # Last year of data
                    
                    logger.info(f"Fetching IPC data from {start_date.date()} to {end_date.date()}")
                    
                    # Note: We're using the string format directly now
                    data = await ine_connector.get_dataset_data(
                        dataset_id="IPC",
                        start_date=start_date.strftime("%Y%m%d"),
                        end_date=end_date.strftime("%Y%m%d")
                    )
                    
                    # Check if we got any data
                    if data and len(data) > 0:
                        logger.info("Latest IPC data points:")
                        # Show last 5 entries or all if fewer than 5
                        for entry in data[-min(5, len(data)):]:
                            logger.debug(f"{entry}")
                    else:
                        logger.info("No IPC data returned from the API.")
                except Exception as e:
                    logger.error(f"Error fetching IPC data: {str(e)}")
            else:
                logger.info("INE connector not available in active connectors.")
        except Exception as e:
            logger.error(f"Error in data discovery workflow: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting ModelForge AI Workflow Example...")
    logger.info("----------------------------------------")
    asyncio.run(run_workflow()) 