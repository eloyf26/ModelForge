from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from .base import BaseConnector
from ..catalog import DatasetMetadata, DatasetSchema
import time
import aiohttp

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
    
    async def convert_to_standard_metadata(self) -> List[DatasetMetadata]:
        """
        Convert INE metadata to standard DatasetMetadata format
        
        Fetches metadata from the INE API and converts it to a list of
        standardized DatasetMetadata objects.
        
        Returns:
            List of DatasetMetadata objects
        """
        datasets = []
        try:
            # Get metadata from INE API
            metadata = await self.get_metadata()
            
            # Check if operaciones key exists in the response
            if 'operaciones' not in metadata:
                self.logger.error("Invalid response format: 'operaciones' key not found in INE API response")
                return datasets
                
            self.logger.debug(f"Processing {len(metadata['operaciones'])} datasets from INE API")
            for dataset in metadata['operaciones']:
                try:
                    # Get schema information
                    schema_info = await self.get_dataset_schema(dataset['Id'])
                    
                    # Convert to our schema format
                    schema = {}
                    if 'variables' in schema_info:
                        for field in schema_info['variables']:
                            schema[field['Id']] = DatasetSchema(
                                name=field['Id'],
                                data_type=field['Tipo'],
                                description=field.get('Nombre'),
                                is_nullable=True
                            )
                    
                    # Create dataset metadata
                    dataset_metadata = DatasetMetadata(
                        id=dataset['Id'],
                        name=dataset['Nombre'],
                        source="ine",
                        endpoint=f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{dataset['Id']}",
                        schema=schema,
                        update_frequency='unknown',
                        last_updated=datetime.now(),
                        description=dataset.get('Descripcion'),
                        tags=[],
                        license=None,
                        rate_limit=self.rate_limit
                    )
                    datasets.append(dataset_metadata)
                except Exception as e:
                    self.logger.error(f"Error processing INE dataset {dataset.get('Id', 'unknown')}: {str(e)}")
                
            self.logger.info(f"Successfully converted {len(datasets)} INE datasets to standard format")
        except Exception as e:
            self.logger.error(f"Error converting INE metadata: {str(e)}")
            
        return datasets
        
    async def get_dataset_data(
        self, 
        dataset_id: str, 
        start_date: Optional[Union[datetime, str]] = None,
        end_date: Optional[Union[datetime, str]] = None,
        last_n: Optional[int] = None,
        periodicity: Optional[int] = None,
        friendly_format: bool = False,
        include_metadata: bool = False,
        detail_level: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get actual data for a specific INE dataset
        
        Args:
            dataset_id: The dataset identifier
            start_date: Start date for data range (datetime object or string in format YYYYMMDD)
            end_date: End date for data range (datetime object or string in format YYYYMMDD)
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
            # Convert datetime to string if needed
            if isinstance(start_date, datetime):
                start_date_str = start_date.strftime("%Y%m%d")
            else:
                # Assume it's already a string
                start_date_str = start_date
                
            if end_date is not None:
                if isinstance(end_date, datetime):
                    end_date_str = end_date.strftime("%Y%m%d")
                else:
                    # Assume it's already a string
                    end_date_str = end_date
                    
                date_str = f"{start_date_str}:{end_date_str}"
            else:
                date_str = start_date_str
                
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