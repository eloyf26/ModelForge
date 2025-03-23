"""
Data Discovery module for ModelForge AI.
Handles dataset discovery, API connections, and metadata catalog management.
"""

from .models import DatasetMetadata, DatasetSchema
from .catalog import DatasetCatalog
from .connectors import INEConnector, AEMETConnector, EurostatConnector
from .discovery_service import DataDiscoveryService

__all__ = ['DatasetMetadata', 'DatasetSchema', 'DatasetCatalog', 'INEConnector', 'AEMETConnector', 'EurostatConnector', 'DataDiscoveryService'] 