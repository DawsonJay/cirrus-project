"""
Weather Unlocked API client
High rate limit: 60,000 calls/day
"""

from typing import Dict, Any
from .base_client import BaseWeatherClient

class WeatherUnlockedClient(BaseWeatherClient):
    """Client for Weather Unlocked API"""
    
    def __init__(self, app_id: str, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="http://api.weatherunlocked.com/api"
        )
        self.app_id = app_id
    
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data from Weather Unlocked"""
        # Weather Unlocked uses location in the URL path, not as parameters
        location = f"{lat},{lon}"
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key
        }
        
        response = await self.make_request(f"/current/{location}", params)
        return self._normalize_current_weather(response)
    
    async def get_forecast(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast from Weather Unlocked"""
        # Weather Unlocked uses location in the URL path
        location = f"{lat},{lon}"
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "days": days
        }
        
        response = await self.make_request(f"/forecast/{location}", params)
        return self._normalize_forecast(response)
    
    async def get_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather alerts from Weather Unlocked"""
        # Weather Unlocked may not provide detailed alerts
        return {"alerts": [], "source": "weather-unlocked"}
    
    def _normalize_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Weather Unlocked current weather data"""
        if not data:
            return {}
            
        return {
            "location": {
                "latitude": data.get("lat", 0),
                "longitude": data.get("lon", 0),
                "timezone": data.get("timezone", ""),
                "elevation": data.get("elevation", 0)
            },
            "temperature": data.get("temp_c", 0),
            "humidity": data.get("humid_pct", 0),
            "wind_speed": data.get("windspd_kmh", 0),
            "wind_direction": data.get("winddir_compass", 0),
            "pressure": data.get("pressure_mb", 0),
            "precipitation": data.get("precip_mm", 0),
            "weather_code": data.get("wx_code", 0),
            "cloud_cover": data.get("cloudtotal_pct", 0),
            "weather_description": data.get("wx_desc", ""),
            "feels_like": data.get("feelslike_c", 0),
            "source": "weather-unlocked",
            "timestamp": data.get("time", "")
        }
    
    def _normalize_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Weather Unlocked forecast data"""
        if not data or "Days" not in data:
            return {}
            
        days = data["Days"]
        forecast_data = []
        
        for day in days:
            forecast_data.append({
                "date": day.get("date", ""),
                "temperature_max": day.get("temp_max_c", 0),
                "temperature_min": day.get("temp_min_c", 0),
                "precipitation": day.get("precip_mm", 0),
                "wind_speed": day.get("windspd_max_kmh", 0),
                "weather_code": day.get("wx_code", 0)
            })
        
        return {
            "forecast_days": len(forecast_data),
            "forecast_data": forecast_data,
            "source": "weather-unlocked"
        }
