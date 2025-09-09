"""
Weather service that pools data from multiple APIs
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .open_meteo_client import OpenMeteoClient
from .environment_canada_client import EnvironmentCanadaClient
from .weather_unlocked_client import WeatherUnlockedClient
from .openweather_client import OpenWeatherClient
from ..config import settings

logger = logging.getLogger(__name__)

class WeatherService:
    """Service that pools weather data from multiple APIs"""
    
    def __init__(self):
        self.clients = []
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available API clients"""
        # Always available (no API key required)
        self.clients.append(OpenMeteoClient())
        self.clients.append(EnvironmentCanadaClient())
        
        # Require API keys
        if settings.OPENWEATHER_API_KEY:
            self.clients.append(OpenWeatherClient(settings.OPENWEATHER_API_KEY))
        
        # Weather Unlocked disabled due to connectivity issues
        # if settings.WEATHER_UNLOCKED_APP_ID and settings.WEATHER_UNLOCKED_API_KEY:
        #     self.clients.append(WeatherUnlockedClient(settings.WEATHER_UNLOCKED_APP_ID, settings.WEATHER_UNLOCKED_API_KEY))
        
        logger.info(f"Initialized {len(self.clients)} weather API clients")
    
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data from all available APIs"""
        tasks = []
        
        for client in self.clients:
            task = asyncio.create_task(
                self._safe_get_current_weather(client, lat, lon)
            )
            tasks.append(task)
        
        # Wait for all API calls to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and empty results
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result:
                valid_results.append(result)
        
        if not valid_results:
            return {"error": "No weather data available from any API"}
        
        # Pool and average the data
        return self._pool_current_weather_data(valid_results)
    
    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast from all available APIs"""
        tasks = []
        
        for client in self.clients:
            task = asyncio.create_task(
                self._safe_get_forecast(client, lat, lon, days)
            )
            tasks.append(task)
        
        # Wait for all API calls to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and empty results
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result:
                valid_results.append(result)
        
        if not valid_results:
            return {"error": "No forecast data available from any API"}
        
        # Pool and average the data
        return self._pool_forecast_data(valid_results)
    
    async def get_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather alerts from all available APIs"""
        tasks = []
        
        for client in self.clients:
            task = asyncio.create_task(
                self._safe_get_weather_alerts(client, lat, lon)
            )
            tasks.append(task)
        
        # Wait for all API calls to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and empty results
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result:
                valid_results.append(result)
        
        if not valid_results:
            return {"alerts": [], "sources": []}
        
        # Combine alerts from all sources
        return self._pool_alert_data(valid_results)
    
    async def _safe_get_current_weather(self, client, lat: float, lon: float) -> Dict[str, Any]:
        """Safely get current weather data from a client"""
        try:
            async with client:
                return await client.get_current_weather(lat, lon)
        except Exception as e:
            logger.error(f"Error getting current weather from {client.__class__.__name__}: {str(e)}")
            return {}
    
    async def _safe_get_forecast(self, client, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Safely get forecast data from a client"""
        try:
            async with client:
                return await client.get_forecast(lat, lon, days)
        except Exception as e:
            logger.error(f"Error getting forecast from {client.__class__.__name__}: {str(e)}")
            return {}
    
    async def _safe_get_weather_alerts(self, client, lat: float, lon: float) -> Dict[str, Any]:
        """Safely get weather alerts from a client"""
        try:
            async with client:
                return await client.get_weather_alerts(lat, lon)
        except Exception as e:
            logger.error(f"Error getting alerts from {client.__class__.__name__}: {str(e)}")
            return {}
    
    def _pool_current_weather_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Pool and average current weather data from multiple sources"""
        if not results:
            return {}
        
        # Calculate averages for numeric values
        temperatures = [r.get("temperature", 0) for r in results if r.get("temperature") is not None]
        humidities = [r.get("humidity", 0) for r in results if r.get("humidity") is not None]
        wind_speeds = [r.get("wind_speed", 0) for r in results if r.get("wind_speed") is not None]
        pressures = [r.get("pressure", 0) for r in results if r.get("pressure") is not None]
        precipitations = [r.get("precipitation", 0) for r in results if r.get("precipitation") is not None]
        cloud_covers = [r.get("cloud_cover", 0) for r in results if r.get("cloud_cover") is not None]
        
        # Get location from first result (should be consistent across APIs)
        location = results[0].get("location", {})
        
        return {
            "location": location,
            "temperature": sum(temperatures) / len(temperatures) if temperatures else 0,
            "humidity": sum(humidities) / len(humidities) if humidities else 0,
            "wind_speed": sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0,
            "wind_direction": results[0].get("wind_direction", 0),  # Use first available
            "pressure": sum(pressures) / len(pressures) if pressures else 0,
            "precipitation": sum(precipitations) / len(precipitations) if precipitations else 0,
            "weather_code": results[0].get("weather_code", 0),  # Use first available
            "cloud_cover": sum(cloud_covers) / len(cloud_covers) if cloud_covers else 0,
            "weather_description": results[0].get("weather_description", ""),  # Use first available
            "visibility": results[0].get("visibility", 0),  # Use first available
            "sources": [r.get("source", "unknown") for r in results],
            "source_count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _pool_forecast_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Pool and average forecast data from multiple sources"""
        if not results:
            return {}
        
        # For now, return the first available forecast
        # TODO: Implement more sophisticated pooling logic
        return {
            **results[0],
            "sources": [r.get("source", "unknown") for r in results],
            "source_count": len(results)
        }
    
    def _pool_alert_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine alert data from multiple sources"""
        all_alerts = []
        sources = []
        
        for result in results:
            alerts = result.get("alerts", [])
            source = result.get("source", "unknown")
            
            for alert in alerts:
                alert["source"] = source
                all_alerts.append(alert)
            
            sources.append(source)
        
        return {
            "alerts": all_alerts,
            "sources": sources,
            "source_count": len(sources),
            "alert_count": len(all_alerts)
        }
