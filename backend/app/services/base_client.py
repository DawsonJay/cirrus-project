"""
Base API client for weather services
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseWeatherClient(ABC):
    """Base class for weather API clients"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, params: Dict[str, Any] = None, use_post: bool = False) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
            
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
            
        # Add API key if available
        if self.api_key:
            params["key"] = self.api_key
            
        try:
            if use_post:
                # Use POST for large requests to avoid URL length limits
                async with self.session.post(url, data=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API request failed: {response.status} - {await response.text()}")
                        return {}
            else:
                # Use GET for normal requests
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API request failed: {response.status} - {await response.text()}")
                        return {}
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return {}
    
    @abstractmethod
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data for given coordinates"""
        pass
        
    @abstractmethod
    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast for given coordinates"""
        pass
        
    @abstractmethod
    async def get_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather alerts for given coordinates"""
        pass
