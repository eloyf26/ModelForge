"""Intent parser module for converting natural language to ML specifications."""

from typing import Dict, Any, Optional
import json
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from enum import Enum

class TaskType(str, Enum):
    TIME_SERIES_REGRESSION = "time_series_regression"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"

class MLSpecification(BaseModel):
    """ML specification schema."""
    task_type: TaskType
    target: str
    features: list[str] = Field(default_factory=list)
    metric: str
    horizon: Optional[str] = None  # Only for time series tasks

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_type": "time_series_regression",
                "target": "sales",
                "features": ["temp", "unemployment_rate", "sentiment_score"],
                "metric": "rmse",
                "horizon": "3M"
            }
        }
    )

    @model_validator(mode='after')
    def validate_time_series_requirements(self) -> 'MLSpecification':
        """Validate that time series tasks have required fields."""
        if self.task_type == TaskType.TIME_SERIES_REGRESSION and not self.horizon:
            raise ValueError("horizon is required for time series regression tasks")
        return self

# LLM prompt template for converting natural language to ML spec
PROMPT_TEMPLATE = """
Extract the ML specification from the following natural language description.
Return a JSON object with the following fields:
- task_type: The type of ML task (time_series_regression, classification, regression, clustering)
- target: The target variable to predict
- features: List of relevant features mentioned
- metric: The evaluation metric to use
- horizon: For time series tasks, the prediction horizon (e.g., "3M" for 3 months)

Description: {description}

Format the response as a valid JSON object.
"""

def parse_intent(description: str) -> MLSpecification:
    """
    Convert natural language description into ML specification.
    
    Args:
        description: Natural language description of the ML task
        
    Returns:
        MLSpecification object
        
    Raises:
        ValueError: If the specification is invalid
    """
    try:
        # TODO: Replace with actual LLM call when implemented
        # This is a mock implementation for now
        mock_response = {
            "task_type": "time_series_regression",
            "target": "sales",
            "features": ["temp", "unemployment_rate", "sentiment_score"],
            "metric": "rmse",
            "horizon": "3M"
        }
        
        # Validate the specification
        spec = MLSpecification(**mock_response)
        return spec
        
    except Exception as e:
        raise ValueError(f"Failed to parse intent: {str(e)}") 