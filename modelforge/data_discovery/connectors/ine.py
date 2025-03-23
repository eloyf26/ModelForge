from typing import Any, Dict, List, Optional
from datetime import datetime
from .base import BaseConnector

class INEConnector(BaseConnector):
    """Connector for the Spanish Statistical Office (INE) API"""
    
    def __init__(self):
        super().__init__(
            base_url="https://servicios.ine.es/wstempus/js",
            rate_limit=100  # 100 requests per minute as per spec
        )
        
    async def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about available INE datasets"""
        return await self._make_request("ES/OPERACIONES_DISPONIBLES")
        
    async def search_datasets(self, query: str) -> Dict[str, Any]:
        """Search for INE datasets matching query"""
        return await self._make_request("ES/Search", params={"q": query})
        
    async def get_dataset_schema(self, dataset_id: str) -> Dict[str, Any]:
        """Get schema information for a specific INE dataset"""
        return await self._make_request(f"ES/VARIABLES_OPERACION/{dataset_id}")
        
    async def get_dataset_data(
        self, 
        dataset_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        last_n: Optional[int] = None,
        periodicity: Optional[int] = None,
        friendly_format: bool = False,
        include_metadata: bool = False,
        detail_level: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get actual data for a specific INE dataset
        
        Args:
            dataset_id: The dataset identifier
            start_date: Start date for data range
            end_date: End date for data range
            last_n: Get last N periods instead of date range
            periodicity: Filter by periodicity (1=monthly, 3=quarterly, 6=biannual, 12=yearly)
            friendly_format: Return data in a more readable format
            include_metadata: Include metadata in response
            detail_level: Detail level (0, 1, or 2)
        """
        params = {}
        
        # Handle date range or last N periods
        if last_n is not None:
            params["nult"] = last_n
        elif start_date is not None:
            date_str = start_date.strftime("%Y%m%d")
            if end_date is not None:
                date_str += ":" + end_date.strftime("%Y%m%d")
            params["date"] = date_str
            
        # Add optional parameters
        if periodicity is not None:
            params["p"] = periodicity
            
        if detail_level is not None:
            params["det"] = detail_level
            
        # Handle output format
        if friendly_format or include_metadata:
            tip = ""
            if friendly_format:
                tip += "A"
            if include_metadata:
                tip += "M"
            params["tip"] = tip
            
        return await self._make_request(f"ES/DATOS_SERIE/{dataset_id}", params=params)
        
    async def get_series_by_filters(
        self,
        operation_id: str,
        filters: Dict[str, str],
        periodicity: Optional[int] = None,
        last_n: Optional[int] = None,
        detail_level: Optional[int] = None,
        friendly_format: bool = False,
        include_metadata: bool = False
    ) -> Dict[str, Any]:
        """Get data series using filters
        
        Args:
            operation_id: The operation identifier (e.g. 'IPC')
            filters: Dictionary of filters where key is filter number (g1, g2, etc)
                    and value is filter spec (e.g. "115:29" for Madrid province)
            periodicity: Filter by periodicity (1=monthly, 3=quarterly, 6=biannual, 12=yearly)
            last_n: Get last N periods
            detail_level: Detail level (0, 1, or 2)
            friendly_format: Return data in a more readable format
            include_metadata: Include metadata in response
        """
        params = {}
        
        # Add filters
        for i, (var_id, value) in enumerate(filters.items(), 1):
            params[f"g{i}"] = f"{var_id}:{value}"
            
        # Add optional parameters
        if periodicity is not None:
            params["p"] = periodicity
            
        if last_n is not None:
            params["nult"] = last_n
            
        if detail_level is not None:
            params["det"] = detail_level
            
        # Handle output format
        if friendly_format or include_metadata:
            tip = ""
            if friendly_format:
                tip += "A"
            if include_metadata:
                tip += "M"
            params["tip"] = tip
            
        return await self._make_request(f"ES/DATOS_METADATAOPERACION/{operation_id}", params=params)
        
    async def get_available_periodicities(self) -> Dict[str, Any]:
        """Get list of available periodicities"""
        return await self._make_request("ES/PERIODICIDADES")
        
    async def get_variable_values(
        self,
        operation_id: str,
        variable_id: str
    ) -> Dict[str, Any]:
        """Get possible values for a variable in an operation
        
        Args:
            operation_id: The operation identifier (e.g. 'IPC')
            variable_id: The variable identifier
        """
        return await self._make_request(f"ES/VALORES_VARIABLEOPERACION/{variable_id}/{operation_id}")
        
    async def get_series_metadata(
        self,
        operation_id: str,
        filters: Dict[str, str],
        periodicity: Optional[int] = None,
        detail_level: Optional[int] = None,
        friendly_format: bool = False
    ) -> Dict[str, Any]:
        """Get metadata for series matching filters
        
        Args:
            operation_id: The operation identifier (e.g. 'IPC')
            filters: Dictionary of filters where key is filter number (g1, g2, etc)
                    and value is filter spec (e.g. "115:29" for Madrid province)
            periodicity: Filter by periodicity (1=monthly, 3=quarterly, 6=biannual, 12=yearly)
            detail_level: Detail level (0, 1, or 2)
            friendly_format: Return data in a more readable format
        """
        params = {}
        
        # Add filters
        for i, (var_id, value) in enumerate(filters.items(), 1):
            params[f"g{i}"] = f"{var_id}:{value}"
            
        # Add optional parameters
        if periodicity is not None:
            params["p"] = periodicity
            
        if detail_level is not None:
            params["det"] = detail_level
            
        if friendly_format:
            params["tip"] = "A"
            
        return await self._make_request(f"ES/SERIE_METADATAOPERACION/{operation_id}", params=params) 