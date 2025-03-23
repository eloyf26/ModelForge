import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from modelforge.data_discovery.discovery_service import DataDiscoveryService
from modelforge.data_discovery.storage.supabase import SupabaseStorage
from modelforge.logging.logger import get_logger

# Load environment variables from .env file (if present)
load_dotenv()

# Create logger
logger = get_logger(__name__)

async def main():
    """
    Example script showing how to use Supabase for persistent storage with PostgreSQL
    
    Make sure to set the following environment variable:
    - SUPABASE_DB_URL: Your Supabase PostgreSQL connection string
      Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
    """
    # Check if required environment variables are set
    if not os.environ.get("SUPABASE_DB_URL"):
        logger.error("SUPABASE_DB_URL environment variable must be set")
        logger.info("Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres")
        return
    
    # Initialize the data discovery service with persistent storage enabled
    async with DataDiscoveryService(use_persistent_storage=True) as service:
        # First time: refresh catalog and save to Supabase
        logger.info("Refreshing catalog and saving to Supabase PostgreSQL database...")
        await service.refresh_catalog()
        
        # List all datasets that were just fetched
        datasets = service.list_all_datasets()
        logger.info(f"Fetched and saved {len(datasets)} datasets to PostgreSQL database")
        
        # Example search
        search_term = "PIB"  # Spanish GDP
        gdp_datasets = service.search_datasets(search_term)
        logger.info(f"Found {len(gdp_datasets)} datasets matching '{search_term}'")
        
        for dataset in gdp_datasets[:3]:  # Show first 3 matches
            logger.info(f"ID: {dataset.id}, Name: {dataset.name}")
            
    # Create a new service instance to demonstrate loading from Supabase
    logger.info("\nCreating new service instance to load data from PostgreSQL database...")
    async with DataDiscoveryService(use_persistent_storage=True) as service:
        # Load data from Supabase without refreshing from API sources
        datasets = service.list_all_datasets()
        logger.info(f"Loaded {len(datasets)} datasets from PostgreSQL database without API refresh")
        
        # Same search as before should work with the loaded data
        gdp_datasets = service.search_datasets(search_term)
        logger.info(f"Found {len(gdp_datasets)} datasets matching '{search_term}' in loaded data")
    
    # Demonstrate specialized query methods
    logger.info("\nDemonstrating specialized query methods using the column-based structure:")
    storage = SupabaseStorage()
    
    # Query by source
    logger.info("\n1. Query by source:")
    aemet_datasets = await storage.query_by_source("aemet")
    logger.info(f"Found {len(aemet_datasets)} datasets from AEMET source")
    for dataset in aemet_datasets[:2]:  # Show first 2
        logger.info(f"  ID: {dataset.id}, Name: {dataset.name}")
    
    # Query by update date
    logger.info("\n2. Query by update date:")
    recent_datasets = await storage.query_by_update_date(days=30)
    logger.info(f"Found {len(recent_datasets)} datasets updated in the last 30 days")
    
    # Query by tag (first, let's find some datasets with tags)
    if datasets:
        sample_dataset = datasets[0]
        if sample_dataset.tags:
            sample_tag = sample_dataset.tags[0]
            logger.info(f"\n3. Query by tag '{sample_tag}':")
            tagged_datasets = await storage.query_by_tag(sample_tag)
            logger.info(f"Found {len(tagged_datasets)} datasets with tag '{sample_tag}'")
    
    # Advanced search demonstration
    logger.info("\n4. Advanced search:")
    # Search for datasets from 'aemet' or 'eurostat' updated in the last 60 days
    advanced_results = await storage.advanced_search(
        sources=["aemet", "eurostat"],
        updated_after=datetime.now() - timedelta(days=60),
        name_contains="data"
    )
    logger.info(f"Advanced search found {len(advanced_results)} datasets matching criteria")
    for dataset in advanced_results[:3]:  # Show first 3
        logger.info(f"  ID: {dataset.id}, Name: {dataset.name}, Source: {dataset.source}")

if __name__ == "__main__":
    asyncio.run(main()) 