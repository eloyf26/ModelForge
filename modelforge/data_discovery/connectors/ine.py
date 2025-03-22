from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from ..catalog import DatasetMetadata, DatasetSchema
from .base import BaseConnector

logger = logging.getLogger(__name__)

class INEConnector(BaseConnector):
    """Connector for the Spanish Statistical Office (INE) API"""
    
    def __init__(self):
        super().__init__(
            base_url="https://servicios.ine.es/wstempus/js/ES",
            rate_limit=100  # 100 requests per minute as per spec
        )
        
    async def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about available INE datasets"""
        try:
            logger.debug("Fetching INE metadata")
            return await self._make_request("OPERACIONES_DISPONIBLES")
        except Exception as e:
            logger.error("Failed to fetch INE metadata: %s", str(e))
            return {
                "name": "INE API",
                "description": "Spanish National Statistics Institute API",
                "version": "1.0"
            }
        
    async def search_datasets(self, query: str) -> List[DatasetMetadata]:
        """Search for INE datasets matching query"""
        logger.info("Searching INE datasets with query: %s", query)
        try:
            response = await self._make_request("Search", params={"q": query})
            if not response:
                logger.warning("No datasets found for query: %s", query)
                return []
                
            datasets = []
            for item in response:
                try:
                    dataset = DatasetMetadata(
                        id=str(item.get("COD", "")),
                        name=item.get("NAME", ""),
                        description=item.get("DESCRIPTION", ""),
                        tags=["inflation", "prices", "economy"] if "IPC" in str(item.get("COD", "")) else [],
                        schema=DatasetSchema(fields={
                            "date": "datetime",
                            "value": "float",
                            "change": "float"
                        }),
                        source="INE",
                        endpoint="https://servicios.ine.es/wstempus/js/ES",
                        update_frequency="monthly",
                        last_updated=datetime.now()
                    )
                    datasets.append(dataset)
                    logger.debug("Found dataset: %s", dataset.id)
                except Exception as e:
                    logger.error("Failed to parse dataset metadata: %s", str(e))
                    continue
            logger.info("Found %d datasets matching query: %s", len(datasets), query)
            return datasets
        except Exception as e:
            logger.error("Failed to search datasets: %s", str(e))
            return []
        
    async def get_dataset_schema(self, dataset_id: str) -> Dict[str, Any]:
        """Get schema information for a specific INE dataset"""
        logger.debug("Fetching schema for dataset: %s", dataset_id)
        try:
            response = await self._make_request(f"VARIABLES_OPERACION/{dataset_id}")
            if not response:
                logger.warning("No schema found for dataset: %s", dataset_id)
                return {"fields": {}}
            return {"fields": {
                "date": "datetime",
                "value": "float",
                "change": "float"
            }}
        except Exception as e:
            logger.error("Failed to fetch schema for dataset %s: %s", dataset_id, str(e))
            return {"fields": {}}
        
    async def get_dataset_data(self, dataset_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get data for a specific INE dataset within a date range"""
        logger.info("Fetching data for dataset %s from %s to %s", dataset_id, start_date, end_date)
        try:
            date_str = f"{start_date.strftime('%Y%m%d')}:{end_date.strftime('%Y%m%d')}"
            response = await self._make_request(f"DATOS_SERIE/{dataset_id}", params={"date": date_str})
            
            if not response or not isinstance(response, dict) or "Data" not in response:
                logger.warning("No data found for dataset %s in date range", dataset_id)
                return []
                
            data = []
            for item in response.get("Data", []):
                try:
                    data.append({
                        "date": item.get("Fecha"),
                        "value": item.get("Valor"),
                        "change": item.get("Variacion")
                    })
                except Exception as e:
                    logger.error("Failed to parse data item: %s", str(e))
                    continue
            logger.info("Retrieved %d data points for dataset %s", len(data), dataset_id)
            return data
        except Exception as e:
            logger.error("Failed to fetch data for dataset %s: %s", dataset_id, str(e))
            return []
        
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
        logger.info("Fetching series for operation %s with filters: %s", operation_id, filters)
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
            
        logger.debug("Making request with params: %s", params)
        return await self._make_request(f"ES/DATOS_METADATAOPERACION/{operation_id}", params=params)
        
    async def get_available_periodicities(self) -> Dict[str, Any]:
        """Get list of available periodicities"""
        logger.debug("Fetching available periodicities")
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
        logger.debug("Fetching values for variable %s in operation %s", variable_id, operation_id)
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
        logger.info("Fetching metadata for operation %s with filters: %s", operation_id, filters)
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
            
        logger.debug("Making request with params: %s", params)
        return await self._make_request(f"ES/SERIE_METADATAOPERACION/{operation_id}", params=params) 