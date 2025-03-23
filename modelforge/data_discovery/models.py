from typing import Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

class DatasetSchema(BaseModel):
    """Schema definition for a dataset field"""
    name: str
    data_type: str
    description: Optional[str] = None
    is_nullable: bool = True

class DatasetMetadata(BaseModel):
    """Metadata for a single dataset"""
    id: str
    name: str
    source: str
    endpoint: HttpUrl
    schema: Dict[str, DatasetSchema]
    update_frequency: str
    last_updated: datetime
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    license: Optional[str] = None
    rate_limit: Optional[int] = None  # requests per minute 