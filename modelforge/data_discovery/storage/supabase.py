import os
import json
from typing import Dict, List, Optional, Any
import asyncpg
from datetime import datetime, timedelta
from ..models import DatasetMetadata
from modelforge.logging.logger import get_logger

logger = get_logger(__name__)

class SupabaseStorage:
    """
    Supabase storage connector for persisting the catalog data using direct PostgreSQL connection
    """
    
    def __init__(self, table_name: str = "dataset_catalog"):
        """
        Initialize Supabase connector using environment variables
        
        Args:
            table_name: The Supabase table to use for storage
        """
        self.db_url = os.environ.get('SUPABASE_DB_URL')
        self.table_name = table_name
        
        if not self.db_url:
            logger.error("Supabase database URL not found in environment variables")
            raise ValueError("SUPABASE_DB_URL environment variable must be set")
            
        logger.info(f"Initialized Supabase storage connector using table: {table_name}")
        
    async def _get_connection(self):
        """Get a database connection from the pool"""
        return await asyncpg.connect(
            self.db_url,
            statement_cache_size=0  # Disable statement cache for pgbouncer compatibility
        )
        
    async def _ensure_table_exists(self, conn):
        """Ensure the dataset catalog table exists with appropriate columns"""
        # First, check if the table exists
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
            """, 
            self.table_name
        )
        
        if not table_exists:
            # Create table with all columns
            await conn.execute(f'''
                CREATE TABLE {self.table_name} (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    schema JSONB NOT NULL,
                    update_frequency TEXT NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    description TEXT,
                    tags JSONB,
                    license TEXT,
                    rate_limit INTEGER,
                    raw_data JSONB NOT NULL
                )
            ''')
            logger.info(f"Table {self.table_name} created")
        else:
            logger.info(f"Table {self.table_name} already exists")
       
    async def save_datasets(self, datasets: List[DatasetMetadata]) -> bool:
        """
        Save a list of datasets to Supabase with individual columns
        
        Args:
            datasets: List of dataset metadata objects to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = await self._get_connection()
            try:
                # Ensure the table exists
                await self._ensure_table_exists(conn)
                
                # Start a transaction
                async with conn.transaction():
                    # Process each dataset and insert with individual columns
                    for dataset in datasets:
                        # Convert to dict for the raw data column
                        json_data = dataset.model_dump(mode='json')
                        
                        # Format tags as JSON array
                        tags_json = json.dumps(dataset.tags) if dataset.tags else None
                        
                        # Convert schema to JSON
                        schema_json = json.dumps({
                            k: v.model_dump(mode='json') 
                            for k, v in dataset.schema.items()
                        })
                        
                        # Create a duplicate of json_data for the data column
                        data_json = json.dumps(json_data)
                        
                        await conn.execute(
                            f'''
                            INSERT INTO {self.table_name} (
                                id, name, source, endpoint, schema, 
                                update_frequency, last_updated, description,
                                tags, license, rate_limit, raw_data
                            )
                            VALUES (
                                $1, $2, $3, $4, $5, 
                                $6, $7, $8, $9, $10, $11, $12
                            )
                            ON CONFLICT (id) DO UPDATE
                            SET 
                                name = $2,
                                source = $3,
                                endpoint = $4,
                                schema = $5,
                                update_frequency = $6,
                                last_updated = $7,
                                description = $8,
                                tags = $9,
                                license = $10,
                                rate_limit = $11,
                                raw_data = $12
                            ''',
                            dataset.id, 
                            dataset.name,
                            dataset.source,
                            str(dataset.endpoint),
                            schema_json,
                            dataset.update_frequency,
                            dataset.last_updated,
                            dataset.description,
                            tags_json,
                            dataset.license,
                            dataset.rate_limit,
                            data_json
                        )
                        
                logger.info(f"Successfully saved {len(datasets)} datasets to Supabase")
                return True
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error saving datasets to Supabase: {str(e)}")
            return False
            
    async def load_datasets(self) -> List[DatasetMetadata]:
        """
        Load all datasets from Supabase
        
        Returns:
            List of dataset metadata objects
        """
        try:
            conn = await self._get_connection()
            try:
                # Ensure the table exists
                await self._ensure_table_exists(conn)
                
                # Fetch all datasets - using raw_data for complete reconstruction
                rows = await conn.fetch(f"SELECT raw_data FROM {self.table_name}")
                
                # Convert JSON data back to DatasetMetadata objects
                datasets = []
                for row in rows:
                    # Parse the JSON string to dict
                    json_data = json.loads(row['raw_data'])
                    datasets.append(DatasetMetadata.model_validate(json_data))
                    
                logger.info(f"Successfully loaded {len(datasets)} datasets from Supabase")
                return datasets
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error loading datasets from Supabase: {str(e)}")
            return []
    
    async def clear_datasets(self) -> bool:
        """
        Clear all datasets from storage
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = await self._get_connection()
            try:
                # Ensure the table exists
                await self._ensure_table_exists(conn)
                
                # Delete all records
                await conn.execute(f"DELETE FROM {self.table_name}")
                
                logger.info("Successfully cleared all datasets from Supabase")
                return True
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error clearing datasets from Supabase: {str(e)}")
            return False
            
    async def query_by_source(self, source: str) -> List[DatasetMetadata]:
        """
        Query datasets by their source
        
        Args:
            source: The source name to filter by
            
        Returns:
            List of datasets from the specified source
        """
        try:
            conn = await self._get_connection()
            try:
                results = []
                rows = await conn.fetch(
                    f"SELECT raw_data FROM {self.table_name} WHERE source = $1",
                    source
                )
                
                for row in rows:
                    json_data = json.loads(row['raw_data'])
                    results.append(DatasetMetadata.model_validate(json_data))
                
                logger.info(f"Found {len(results)} datasets from source '{source}'")
                return results
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error querying datasets by source: {str(e)}")
            return []
            
    async def query_by_update_date(self, days: int = 30) -> List[DatasetMetadata]:
        """
        Query datasets updated within the specified number of days
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recently updated datasets
        """
        try:
            conn = await self._get_connection()
            try:
                results = []
                rows = await conn.fetch(
                    f"SELECT raw_data FROM {self.table_name} WHERE last_updated > NOW() - INTERVAL '{days} days'"
                )
                
                for row in rows:
                    json_data = json.loads(row['raw_data'])
                    results.append(DatasetMetadata.model_validate(json_data))
                
                logger.info(f"Found {len(results)} datasets updated in the last {days} days")
                return results
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error querying datasets by update date: {str(e)}")
            return []
            
    async def query_by_tag(self, tag: str) -> List[DatasetMetadata]:
        """
        Query datasets that have a specific tag
        
        Args:
            tag: The tag to search for
            
        Returns:
            List of datasets with the specified tag
        """
        try:
            conn = await self._get_connection()
            try:
                results = []
                # Use the @> operator to check if the JSON array contains the value
                rows = await conn.fetch(
                    f"SELECT raw_data FROM {self.table_name} WHERE tags @> $1",
                    json.dumps([tag])
                )
                
                for row in rows:
                    json_data = json.loads(row['raw_data'])
                    results.append(DatasetMetadata.model_validate(json_data))
                
                logger.info(f"Found {len(results)} datasets with tag '{tag}'")
                return results
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error querying datasets by tag: {str(e)}")
            return []
            
    async def advanced_search(
        self,
        sources: Optional[List[str]] = None,
        updated_after: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        name_contains: Optional[str] = None,
        limit: int = 100
    ) -> List[DatasetMetadata]:
        """
        Perform an advanced search with multiple filters.
        
        Args:
            sources: Optional list of source names to filter by
            updated_after: Optional datetime to filter datasets updated after this date
            tags: Optional list of tags to filter by (datasets must have at least one of these tags)
            name_contains: Optional string to search within dataset names
            limit: Maximum number of results to return

        Returns:
            List of DatasetMetadata objects matching the criteria
        """
        try:
            conn = await self._get_connection()
            try:
                query_parts = [f"SELECT raw_data FROM {self.table_name} WHERE 1=1"]
                params = []
                param_idx = 1

                # Add source filter
                if sources and len(sources) > 0:
                    source_conditions = []
                    for source in sources:
                        source_conditions.append(f"source = ${param_idx}")
                        params.append(source)
                        param_idx += 1
                    
                    if source_conditions:
                        query_parts.append(f"AND ({' OR '.join(source_conditions)})")

                # Add last_updated filter
                if updated_after:
                    # Convert datetime to string in a format PostgreSQL understands
                    query_parts.append(f"AND last_updated > ${param_idx}")
                    params.append(updated_after)
                    param_idx += 1

                # Add tags filter (using PostgreSQL array contains operator)
                if tags and len(tags) > 0:
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append(f"tags @> ARRAY[${param_idx}]::text[]")
                        params.append(tag)
                        param_idx += 1
                    
                    if tag_conditions:
                        query_parts.append(f"AND ({' OR '.join(tag_conditions)})")

                # Add name contains filter
                if name_contains:
                    query_parts.append(f"AND name ILIKE ${param_idx}")
                    params.append(f"%{name_contains}%")
                    param_idx += 1

                query_parts.append(f"LIMIT {limit}")
                
                query = " ".join(query_parts)
                logger.debug(f"Advanced search query: {query}, params: {params}")
                
                # Execute query
                rows = await conn.fetch(query, *params)
                
                datasets = []
                for row in rows:
                    json_data = json.loads(row['raw_data'])
                    dataset = DatasetMetadata.model_validate(json_data)
                    datasets.append(dataset)
                
                logger.info(f"Found {len(datasets)} datasets in advanced search")
                return datasets
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error performing advanced search: {str(e)}")
            return [] 