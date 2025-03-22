"""Tests for the intent parser module."""

import pytest
from modelforge.intent_parser import MLSpecification, TaskType, parse_intent

def test_valid_time_series_spec():
    """Test creating a valid time series specification."""
    spec = MLSpecification(
        task_type=TaskType.TIME_SERIES_REGRESSION,
        target="sales",
        features=["temp", "unemployment_rate"],
        metric="rmse",
        horizon="3M"
    )
    assert spec.task_type == TaskType.TIME_SERIES_REGRESSION
    assert spec.target == "sales"
    assert "temp" in spec.features
    assert spec.metric == "rmse"
    assert spec.horizon == "3M"

def test_valid_classification_spec():
    """Test creating a valid classification specification."""
    spec = MLSpecification(
        task_type=TaskType.CLASSIFICATION,
        target="churn",
        features=["age", "subscription_length"],
        metric="accuracy"
    )
    assert spec.task_type == TaskType.CLASSIFICATION
    assert spec.target == "churn"
    assert len(spec.features) == 2
    assert spec.metric == "accuracy"
    assert spec.horizon is None

def test_missing_horizon_time_series():
    """Test that time series tasks require a horizon."""
    with pytest.raises(ValueError):
        MLSpecification(
            task_type=TaskType.TIME_SERIES_REGRESSION,
            target="sales",
            features=["temp"],
            metric="rmse"
        )

def test_parse_intent():
    """Test parsing natural language into ML specification."""
    description = "Predict monthly sales using temperature and unemployment rate data"
    spec = parse_intent(description)
    assert isinstance(spec, MLSpecification)
    assert spec.task_type == TaskType.TIME_SERIES_REGRESSION
    assert spec.target == "sales"
    assert len(spec.features) > 0
    assert spec.metric == "rmse"
    assert spec.horizon is not None 