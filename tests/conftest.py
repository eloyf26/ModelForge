import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path for imports to work correctly in tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up pytest environment variables for testing
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment for all tests"""
    os.environ["SUPABASE_URL"] = "https://test-supabase-url.com"
    os.environ["SUPABASE_KEY"] = "test-supabase-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-api-key"
    os.environ["INE_API_KEY"] = "test-ine-api-key"
    os.environ["AEMET_API_KEY"] = "test-aemet-api-key"
    os.environ["EUROSTAT_API_KEY"] = "test-eurostat-api-key"
    
    # Setup any other necessary environment variables or configuration
    
    yield
    
    # Clean up after tests if needed 