"""Tests for the intent parser module."""

import pytest
from unittest.mock import patch, MagicMock
import os
import openai
from modelforge.intent_parser import (
    MLSpecification, 
    TaskType, 
    parse_intent, 
    ParsingError,
    _call_llm
)

# Test MLSpecification validation
@pytest.fixture
def mock_openai_response():
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='''{
                    "task_type": "time_series_regression",
                    "target": "sales",
                    "features": ["temp", "unemployment_rate"],
                    "metric": "rmse",
                    "horizon": "3M"
                }'''
            )
        )
    ]
    return mock_response

def test_valid_time_series_spec():
    """Test valid time series specification."""
    spec = MLSpecification(
        task_type="time_series_regression",
        target="sales",
        features=["temp"],
        metric="rmse",
        horizon="3M"
    )
    assert spec.task_type == "time_series_regression"

def test_valid_classification_spec():
    """Test valid classification specification."""
    spec = MLSpecification(
        task_type="classification",
        target="churn",
        features=["age", "balance"],
        metric="accuracy"
    )
    assert spec.task_type == "classification"

def test_missing_horizon_time_series():
    """Test that missing horizon raises error for time series."""
    with pytest.raises(ValueError):
        MLSpecification(
            task_type="time_series_regression",
            target="sales",
            features=["temp"],
            metric="rmse"
        )

def test_invalid_metric_classification():
    """Test that invalid metrics are rejected."""
    with pytest.raises(ValueError):
        MLSpecification(
            task_type="classification",
            target="churn",
            metric="rmse"  # Invalid for classification
        )

def test_invalid_metric_regression():
    """Test that invalid metrics are rejected for regression."""
    with pytest.raises(ValueError):
        MLSpecification(
            task_type="regression",
            target="price",
            metric="accuracy"  # Invalid for regression
        )

# Test LLM integration
def test_parse_intent_success(mock_openai_response):
    """Test successful parsing of natural language description."""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client

        description = "Predict monthly sales using temperature and unemployment rate data"
        spec = parse_intent(description)
        
        assert spec.task_type == "time_series_regression"
        assert spec.target == "sales"
        assert "temp" in spec.features
        assert "unemployment_rate" in spec.features
        assert spec.metric == "rmse"
        assert spec.horizon == "3M"

def test_parse_intent_invalid_json():
    """Test handling of invalid JSON response from LLM."""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(content="Invalid JSON")
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with pytest.raises(ParsingError, match="Failed to parse LLM response as JSON"):
            parse_intent("Predict sales")

def test_parse_intent_api_error():
    """Test handling of OpenAI API error."""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        with pytest.raises(ParsingError, match="Unexpected error during LLM call"):
            parse_intent("Predict sales")

def test_parse_intent_missing_api_key():
    """Test handling of missing API key."""
    with patch.dict('os.environ', clear=True):
        with pytest.raises(ParsingError, match="OpenAI API key not found"):
            parse_intent("Predict sales")

def test_parse_intent_invalid_spec():
    """Test handling of invalid specification from LLM."""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='''{
                        "task_type": "time_series_regression",
                        "target": "sales",
                        "features": ["temp"],
                        "metric": "rmse"
                    }'''  # Missing required horizon
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with pytest.raises(ParsingError, match="Invalid specification from LLM"):
            parse_intent("Predict sales") 