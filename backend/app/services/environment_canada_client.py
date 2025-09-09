"""
Environment Canada API client
Official Canadian weather data - completely free
"""

import aiohttp
from typing import Dict, Any
from .base_client import BaseWeatherClient

class EnvironmentCanadaClient(BaseWeatherClient):
    """Client for Environment Canada weather API"""
    
    def __init__(self):
        super().__init__(
            api_key=None,  # Environment Canada doesn't require API key
            base_url="https://api.weather.gc.ca"
        )
    
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data from Environment Canada"""
        # Environment Canada uses different endpoints for different data types
        # We'll need to make multiple requests to get comprehensive data
        
        # Get current conditions
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        
        response = await self.make_request("/collections/climate-daily/items", params)
        return self._normalize_current_weather(response)
    
    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast from Environment Canada"""
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        
        response = await self.make_request("/collections/forecast/items", params)
        return self._normalize_forecast(response)
    
    async def get_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather alerts from Environment Canada"""
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        
        response = await self.make_request("/collections/alerts/items", params)
        return self._normalize_alerts(response)
    
    def _normalize_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Environment Canada current weather data"""
        if not data or "features" not in data:
            return {}
            
        # Environment Canada returns GeoJSON format
        features = data["features"]
        if not features:
            return {}
            
        properties = features[0].get("properties", {})
        return {
            "temperature": properties.get("temperature", 0),
            "humidity": properties.get("humidity", 0),
            "wind_speed": properties.get("wind_speed", 0),
            "wind_direction": properties.get("wind_direction", 0),
            "pressure": properties.get("pressure", 0),
            "precipitation": properties.get("precipitation", 0),
            "weather_code": properties.get("weather_code", 0),
            "source": "environment-canada",
            "timestamp": properties.get("timestamp", "")
        }
    
    def _normalize_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Environment Canada forecast data"""
        if not data or "features" not in data:
            return {}
            
        features = data["features"]
        if not features:
            return {}
            
        # Process forecast features
        forecast_data = []
        for feature in features:
            properties = feature.get("properties", {})
            forecast_data.append({
                "date": properties.get("date", ""),
                "temperature_max": properties.get("temperature_max", 0),
                "temperature_min": properties.get("temperature_min", 0),
                "precipitation": properties.get("precipitation", 0),
                "wind_speed": properties.get("wind_speed", 0),
                "weather_code": properties.get("weather_code", 0)
            })
        
        return {
            "forecast_days": len(forecast_data),
            "forecast_data": forecast_data,
            "source": "environment-canada"
        }
    
    def _normalize_alerts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Environment Canada weather alerts"""
        if not data or "features" not in data:
            return {"alerts": [], "source": "environment-canada"}
            
        features = data["features"]
        alerts = []
        
        for feature in features:
            properties = feature.get("properties", {})
            alerts.append({
                "id": properties.get("id", ""),
                "title": properties.get("title", ""),
                "description": properties.get("description", ""),
                "severity": properties.get("severity", ""),
                "issued_at": properties.get("issued_at", ""),
                "expires_at": properties.get("expires_at", "")
            })
        
        return {
            "alerts": alerts,
            "source": "environment-canada"
        }
