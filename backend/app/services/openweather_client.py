"""
OpenWeatherMap API client for weather data
"""

import logging
from typing import Dict, Any, Optional
from .base_client import BaseWeatherClient

logger = logging.getLogger(__name__)

class OpenWeatherClient(BaseWeatherClient):
    """Client for OpenWeatherMap API"""
    
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.openweathermap.org/data/2.5"
        )
    
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data for given coordinates"""
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"  # Use metric units
        }
        
        response = await self.make_request("/weather", params)
        return self._normalize_current_weather(response)
    
    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast for given coordinates"""
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
        }
        
        response = await self.make_request("/forecast", params)
        return self._normalize_forecast(response)
    
    async def get_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather alerts for given coordinates"""
        # OpenWeatherMap doesn't have a direct alerts endpoint
        # We'll return empty alerts for now
        return {
            "alerts": [],
            "source": "openweathermap",
            "location": {"latitude": lat, "longitude": lon}
        }
    
    def _normalize_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OpenWeatherMap current weather data to common format"""
        try:
            return {
                "location": {
                    "latitude": data.get("coord", {}).get("lat", 0),
                    "longitude": data.get("coord", {}).get("lon", 0),
                    "timezone": data.get("timezone", 0),
                    "elevation": 0  # Not provided by OpenWeatherMap
                },
                "temperature": data.get("main", {}).get("temp", 0),
                "humidity": data.get("main", {}).get("humidity", 0),
                "pressure": data.get("main", {}).get("pressure", 0),
                "wind_speed": data.get("wind", {}).get("speed", 0),
                "wind_direction": data.get("wind", {}).get("deg", 0),
                "visibility": data.get("visibility", 0) / 1000,  # Convert to km
                "cloud_cover": data.get("clouds", {}).get("all", 0),
                "precipitation": data.get("rain", {}).get("1h", 0) or data.get("snow", {}).get("1h", 0),
                "weather_description": data.get("weather", [{}])[0].get("description", ""),
                "weather_code": data.get("weather", [{}])[0].get("id", 0),
                "timestamp": data.get("dt", 0),
                "source": "openweathermap"
            }
        except Exception as e:
            logger.error(f"Error normalizing OpenWeatherMap data: {e}")
            return {}
    
    def _normalize_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OpenWeatherMap forecast data to common format"""
        try:
            forecasts = []
            for item in data.get("list", []):
                forecast = {
                    "timestamp": item.get("dt", 0),
                    "temperature": item.get("main", {}).get("temp", 0),
                    "humidity": item.get("main", {}).get("humidity", 0),
                    "pressure": item.get("main", {}).get("pressure", 0),
                    "wind_speed": item.get("wind", {}).get("speed", 0),
                    "wind_direction": item.get("wind", {}).get("deg", 0),
                    "cloud_cover": item.get("clouds", {}).get("all", 0),
                    "precipitation": item.get("rain", {}).get("3h", 0) or item.get("snow", {}).get("3h", 0),
                    "weather_description": item.get("weather", [{}])[0].get("description", ""),
                    "weather_code": item.get("weather", [{}])[0].get("id", 0)
                }
                forecasts.append(forecast)
            
            return {
                "forecasts": forecasts,
                "location": {
                    "latitude": data.get("city", {}).get("coord", {}).get("lat", 0),
                    "longitude": data.get("city", {}).get("coord", {}).get("lon", 0),
                    "timezone": data.get("city", {}).get("timezone", 0),
                    "elevation": 0
                },
                "source": "openweathermap"
            }
        except Exception as e:
            logger.error(f"Error normalizing OpenWeatherMap forecast data: {e}")
            return {}
