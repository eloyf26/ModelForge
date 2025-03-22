"""Integration test for intent parser with environment variables."""

import os
import pytest
from modelforge.intent_parser import parse_intent, ParsingError

def test_missing_api_key():
    """Test that missing API key raises appropriate error."""
    # Temporarily remove API key if exists
    api_key = os.environ.pop('OPENAI_API_KEY', None)
    
    try:
        with pytest.raises(ParsingError, match="OpenAI API key not found"):
            parse_intent("Predict sales")
    finally:
        # Restore API key if it existed
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key

def test_live_intent_parsing():
    """Test live intent parsing with API key."""
    if not os.getenv('OPENAI_API_KEY'):
        pytest.skip("Skipping live test: OPENAI_API_KEY not set")
    
    description = "Predict monthly sales using temperature and unemployment rate data"
    spec = parse_intent(description)
    
    assert spec.task_type == "time_series_regression"
    assert spec.target == "sales"
    assert any("temp" in feature.lower() for feature in spec.features)
    assert any("unemployment" in feature.lower() for feature in spec.features)
    assert spec.metric in ["rmse", "mae", "mape", "smape"]
    assert spec.horizon is not None 