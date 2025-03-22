"""
Data Discovery module for ModelForge AI.
Handles dataset discovery, API connections, and metadata catalog management.
"""

from .catalog import DatasetCatalog
from .connectors import INEConnector, AEMETConnector, EurostatConnector
from .discovery_service import DataDiscoveryService

__all__ = ['DatasetCatalog', 'INEConnector', 'AEMETConnector', 'EurostatConnector', 'DataDiscoveryService'] 