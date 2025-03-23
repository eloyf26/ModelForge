"""Intent parser module for converting natural language to ML specifications."""

from typing import Dict, Any, Optional
import json
import logging
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from enum import Enum
import openai
import os
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

logger = logging.getLogger(__name__)

class TaskType(str, Enum):
    TIME_SERIES_REGRESSION = "time_series_regression"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"

class ParsingError(Exception):
    """Custom exception for parsing errors."""
    pass

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

    @field_validator('metric')
    def validate_metric(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate that the metric is appropriate for the task type."""
        valid_metrics = {
            'classification': ['accuracy', 'precision', 'recall', 'f1', 'auc'],
            'regression': ['rmse', 'mae', 'mse', 'r2'],
            'clustering': ['silhouette', 'calinski_harabasz', 'davies_bouldin'],
            'time_series_regression': ['rmse', 'mae', 'mape', 'smape']
        }
        
        task_type = values.data.get('task_type')
        if task_type is None:
            raise ValueError("task_type must be specified before metric")
            
        if task_type == TaskType.CLASSIFICATION and v.lower() not in valid_metrics['classification']:
            raise ValueError(f"Invalid metric for classification: {v}")
        elif task_type == TaskType.REGRESSION and v.lower() not in valid_metrics['regression']:
            raise ValueError(f"Invalid metric for regression: {v}")
        elif task_type == TaskType.CLUSTERING and v.lower() not in valid_metrics['clustering']:
            raise ValueError(f"Invalid metric for clustering: {v}")
        elif task_type == TaskType.TIME_SERIES_REGRESSION and v.lower() not in valid_metrics['time_series_regression']:
            raise ValueError(f"Invalid metric for time series regression: {v}")
            
        return v.lower()

# LLM prompt template for converting natural language to ML spec
PROMPT_TEMPLATE = """You are an AI assistant that converts natural language descriptions into structured ML specifications.

Given the following description, extract the ML specification and return it as a JSON object.

Description: {description}

The JSON object must include these fields:
- task_type: Must be one of ["time_series_regression", "classification", "regression", "clustering"]
- target: The target variable to predict (use simple, normalized names)
- features: List of relevant features mentioned (empty list if none specified)
- metric: The evaluation metric to use (must be appropriate for the task type)
- horizon: Required for time_series_regression tasks (e.g., "3M" for 3 months), optional for others

Rules:
1. For time series tasks, horizon is required
2. Metrics must match the task type:
   - classification: accuracy, precision, recall, f1, auc
   - regression: rmse, mae, mse, r2
   - clustering: silhouette, calinski_harabasz, davies_bouldin
   - time_series_regression: rmse, mae, mape, smape
3. Return ONLY the JSON object, no additional text
4. Use simple, normalized names (e.g., "sales" not "monthly_sales")

Format the response as a valid JSON object."""

def _call_llm_with_retry(prompt: str) -> Dict[str, Any]:
    """Internal function to call LLM with retry logic."""
    logger.debug("Calling LLM API with prompt: %s", prompt)
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Call GPT-4 API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that converts ML task descriptions into JSON specifications."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,  # Low temperature for consistent outputs
        max_tokens=500
    )
    
    # Extract and parse JSON response
    json_str = response.choices[0].message.content.strip()
    logger.debug("Received response from LLM: %s", json_str)
    return json.loads(json_str)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _call_llm(prompt: str) -> Dict[str, Any]:
    """
    Call LLM API with retry logic.
    
    Args:
        prompt: The formatted prompt to send to the LLM
        
    Returns:
        Dict containing the LLM's response
        
    Raises:
        ParsingError: If the LLM response cannot be parsed
    """
    # Check for API key first
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OpenAI API key not found in environment variables")
        raise ParsingError("OpenAI API key not found in environment variables")
        
    try:
        return _call_llm_with_retry(prompt)
    except openai.OpenAIError as e:
        logger.error("OpenAI API error: %s", str(e))
        raise ParsingError(f"OpenAI API error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM response as JSON: %s", str(e))
        raise ParsingError(f"Failed to parse LLM response as JSON: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error during LLM call: %s", str(e))
        raise ParsingError(f"Unexpected error during LLM call: {str(e)}")

def parse_intent(description: str) -> MLSpecification:
    """
    Convert natural language description into ML specification.
    
    Args:
        description: Natural language description of the ML task
        
    Returns:
        MLSpecification object
        
    Raises:
        ParsingError: If the specification cannot be parsed or is invalid
    """
    logger.info("Parsing intent from description: %s", description)
    try:
        # Format prompt with description
        prompt = PROMPT_TEMPLATE.format(description=description)
        
        try:
            # Call LLM to get specification
            spec_dict = _call_llm(prompt)
            logger.debug("Received specification from LLM: %s", spec_dict)
        except RetryError as e:
            # Extract original error from retry error
            if hasattr(e, 'last_attempt') and hasattr(e.last_attempt, 'exception'):
                raise e.last_attempt.exception()
            logger.error("Failed to get response from LLM after retries")
            raise ParsingError("Failed to get response from LLM after retries")
        
        # Validate and return specification
        try:
            spec = MLSpecification(**spec_dict)
            logger.info("Successfully parsed intent into specification: %s", spec)
            return spec
        except ValueError as e:
            logger.error("Invalid specification from LLM: %s", str(e))
            raise ParsingError(f"Invalid specification from LLM: {str(e)}")
            
    except ParsingError:
        raise
    except Exception as e:
        logger.error("Failed to parse intent: %s", str(e))
        raise ParsingError(f"Failed to parse intent: {str(e)}") 