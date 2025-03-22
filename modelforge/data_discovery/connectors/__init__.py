"""API connectors for various data sources"""

from .base import BaseConnector
from .ine import INEConnector
from .aemet import AEMETConnector
from .eurostat import EurostatConnector

__all__ = ['BaseConnector', 'INEConnector', 'AEMETConnector', 'EurostatConnector'] 