"""
Open-Meteo API client
Free weather API with no strict rate limits
"""

from typing import Dict, Any
from .base_client import BaseWeatherClient

class OpenMeteoClient(BaseWeatherClient):
    """Client for Open-Meteo weather API"""
    
    def __init__(self):
        super().__init__(
            api_key=None,  # Open-Meteo doesn't require API key
            base_url="https://api.open-meteo.com/v1"
        )
    
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data from Open-Meteo"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "timezone": "auto"
        }
        
        response = await self.make_request("/forecast", params)
        return self._normalize_current_weather(response)
    
    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast from Open-Meteo"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,showers_sum,snowfall_sum,weather_code,wind_speed_10m_max,wind_direction_10m_dominant",
            "timezone": "auto",
            "forecast_days": days
        }
        
        response = await self.make_request("/forecast", params)
        return self._normalize_forecast(response)
    
    async def get_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather alerts from Open-Meteo (limited alert data)"""
        # Open-Meteo doesn't provide detailed alerts, return empty for now
        return {"alerts": [], "source": "open-meteo"}
    
    def _normalize_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Open-Meteo current weather data"""
        if not data or "current" not in data:
            return {}
            
        current = data["current"]
        return {
            "location": {
                "latitude": data.get("latitude", 0),
                "longitude": data.get("longitude", 0),
                "timezone": data.get("timezone", ""),
                "elevation": data.get("elevation", 0)
            },
            "temperature": current.get("temperature_2m", 0),
            "humidity": current.get("relative_humidity_2m", 0),
            "wind_speed": current.get("wind_speed_10m", 0),
            "wind_direction": current.get("wind_direction_10m", 0),
            "pressure": current.get("pressure_msl", 0),
            "precipitation": current.get("precipitation", 0),
            "weather_code": current.get("weather_code", 0),
            "cloud_cover": current.get("cloud_cover", 0),
            "source": "open-meteo",
            "timestamp": current.get("time", "")
        }
    
    def _normalize_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Open-Meteo forecast data"""
        if not data or "daily" not in data:
            return {}
            
        daily = data["daily"]
        # Convert to structured forecast format
        times = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precipitations = daily.get("precipitation_sum", [])
        wind_speeds = daily.get("wind_speed_10m_max", [])
        weather_codes = daily.get("weather_code", [])
        
        forecast = []
        for i in range(len(times)):
            forecast.append({
                "date": times[i],
                "temperature_max": max_temps[i] if i < len(max_temps) else None,
                "temperature_min": min_temps[i] if i < len(min_temps) else None,
                "precipitation": precipitations[i] if i < len(precipitations) else None,
                "wind_speed": wind_speeds[i] if i < len(wind_speeds) else None,
                "weather_code": weather_codes[i] if i < len(weather_codes) else None
            })
        
        return {
            "forecast": forecast,
            "forecast_days": len(forecast),
            "source": "open-meteo",
            "generated_at": data.get("generationtime_ms", 0)
        }
