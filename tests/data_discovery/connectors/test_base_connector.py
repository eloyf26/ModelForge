import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from modelforge.data_discovery.connectors.base import BaseConnector


class TestConnector(BaseConnector):
    """Test implementation of BaseConnector for testing"""
    
    async def fetch_datasets(self):
        """Test implementation of fetch_datasets"""
        return []
    
    async def convert_to_standard_metadata(self):
        """Test implementation of convert_to_standard_metadata"""
        return []


@pytest.mark.asyncio
async def test_base_connector_context_manager():
    """Test the BaseConnector context manager protocol"""
    async with TestConnector() as connector:
        assert isinstance(connector, TestConnector)


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test the rate limiting functionality"""
    connector = TestConnector()
    connector.rate_limit = 5  # 5 requests per second
    
    # Create a mock for the rate limited function
    mock_func = AsyncMock()
    mock_func.side_effect = [1, 2, 3, 4, 5]
    
    # Run multiple rate limited calls
    start_time = asyncio.get_event_loop().time()
    results = []
    for _ in range(5):
        result = await connector._rate_limited_call(mock_func)
        results.append(result)
    end_time = asyncio.get_event_loop().time()
    
    # Check that we got all results
    assert results == [1, 2, 3, 4, 5]
    assert mock_func.call_count == 5
    
    # With a rate limit of 5 per second, 5 calls should take at least 0.8 seconds (4/5 seconds)
    # We use a slightly lower value to account for timing variations
    assert end_time - start_time >= 0.7


@pytest.mark.asyncio
async def test_backoff_retry():
    """Test the backoff retry functionality"""
    connector = TestConnector()
    
    # Create a mock function that fails twice and then succeeds
    mock_func = AsyncMock()
    mock_func.side_effect = [Exception("First failure"), Exception("Second failure"), "success"]
    
    # Set retry params to speed up the test
    with patch.object(connector, 'retry_attempts', 3):
        with patch.object(connector, 'retry_backoff', 0.1):
            result = await connector._with_retry(mock_func)
    
    assert result == "success"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_backoff_retry_max_attempts():
    """Test the backoff retry gives up after max attempts"""
    connector = TestConnector()
    
    # Create a mock function that always fails
    mock_func = AsyncMock()
    mock_func.side_effect = Exception("Always fails")
    
    # Set retry params to speed up the test
    with patch.object(connector, 'retry_attempts', 2):
        with patch.object(connector, 'retry_backoff', 0.1):
            with pytest.raises(Exception, match="Always fails"):
                await connector._with_retry(mock_func)
    
    assert mock_func.call_count == 2 