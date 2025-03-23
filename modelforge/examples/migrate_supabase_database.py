import asyncio
import os
from dotenv import load_dotenv
from modelforge.data_discovery.storage.migrate_supabase_schema import migrate_schema
from modelforge.logging.logger import get_logger

# Load environment variables from .env file (if present)
load_dotenv()

# Create logger
logger = get_logger(__name__)

async def main():
    """
    Example script demonstrating how to migrate an existing Supabase database 
    from the old single JSON column structure to the new multi-column structure.
    
    Make sure to set the following environment variable:
    - SUPABASE_DB_URL: Your Supabase PostgreSQL connection string
      Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
    """
    # Check if required environment variables are set
    if not os.environ.get("SUPABASE_DB_URL"):
        logger.error("SUPABASE_DB_URL environment variable must be set")
        logger.info("Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres")
        return
    
    # Run the migration
    logger.info("Starting migration process...")
    success = await migrate_schema(table_name="dataset_catalog")
    
    if success:
        logger.info("""
Migration completed successfully. Benefits of the new structure:

1. Efficient querying: Direct queries on specific fields without parsing JSON
2. Better indexing: Indexes can be created on individual columns
3. Improved performance: Faster filtering, searching and sorting
4. Type safety: PostgreSQL validates types for each column

The new structure maintains compatibility with existing code while 
providing enhanced functionality for advanced queries.
        """)
    else:
        logger.error("Migration failed. Check the logs for details.")
        logger.info("You may need to manually examine your database or restore from backup.")

if __name__ == "__main__":
    asyncio.run(main()) 