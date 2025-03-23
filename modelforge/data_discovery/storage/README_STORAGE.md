# Persistent Storage for Data Discovery Catalog

The ModelForge Data Discovery service supports optional persistent storage using Supabase PostgreSQL database.

## Prerequisites

- A Supabase account and project
- Supabase PostgreSQL connection string
- Environment variable set for database connection

## Setting Up Supabase

1. Create a new Supabase project at https://supabase.com
2. Navigate to Project Settings > Database to find your connection information
3. The tables will be created automatically by the application

## Configuration

Set the following environment variable:

```bash
SUPABASE_DB_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

You can use a `.env` file with the `python-dotenv` package to manage this variable:

```
# .env file
SUPABASE_DB_URL=postgresql://postgres.pfksyydstegxicyjkrcm:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
```

Note: Make sure to use the connection string with the transaction pooler (`pooler.supabase.com`) for optimal performance.

## Usage

Enable persistent storage when initializing the `DataDiscoveryService`:

```python
from modelforge.data_discovery.discovery_service import DataDiscoveryService

async with DataDiscoveryService(use_persistent_storage=True) as service:
    # Catalog will be loaded from PostgreSQL on initialization
    # and saved back to PostgreSQL after refresh
    await service.refresh_catalog()
    
    # Use the service as normal
    datasets = service.search_datasets("GDP")
```

## Storage Behavior

- When a service is initialized with `use_persistent_storage=True`, it will attempt to load existing data from the PostgreSQL database
- After calling `refresh_catalog()`, the updated dataset metadata will be saved back to the database
- Data is stored as JSONB and converted back to `DatasetMetadata` objects when loaded
- Tables are created automatically if they don't exist

## Example

See `modelforge/data_discovery/examples/use_supabase_storage.py` for a complete example of using Supabase PostgreSQL for persistent storage.

## Database Schema

The PostgreSQL table schema is:

```sql
CREATE TABLE IF NOT EXISTS dataset_catalog (
    id TEXT PRIMARY KEY,
    data JSONB NOT NULL
)
```

Where:
- `id`: The dataset ID
- `data`: The full JSON representation of the dataset metadata

## Advantages Over REST API

- More efficient for transaction processing
- Better concurrency and performance for bulk operations
- Direct database access with lower latency
- No API request limits or throttling

## Dependencies

This implementation requires:
- asyncpg: Asynchronous PostgreSQL library
- python-dotenv: For loading environment variables (optional) 