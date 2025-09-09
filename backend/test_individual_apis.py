"""
Test each API individually to see what's working
"""

import asyncio
import json
from app.services.open_meteo_client import OpenMeteoClient
from app.services.openweather_client import OpenWeatherClient
from app.services.environment_canada_client import EnvironmentCanadaClient
from app.services.weather_unlocked_client import WeatherUnlockedClient

async def test_individual_apis():
    """Test each API individually"""
    print("Testing Individual Weather APIs")
    print("=" * 50)
    
    # Test coordinates for Toronto
    lat, lon = 43.6532, -79.3832
    
    print(f"Testing coordinates: {lat}, {lon} (Toronto)")
    print()
    
    # Test Open-Meteo
    print("🌍 OPEN-METEO API:")
    print("-" * 30)
    try:
        client = OpenMeteoClient()
        async with client:
            current = await client.get_current_weather(lat, lon)
            forecast = await client.get_forecast(lat, lon, 3)
            alerts = await client.get_weather_alerts(lat, lon)
            
            print(f"✅ Current Weather: {current.get('temperature', 'N/A')}°C")
            print(f"✅ Forecast: {len(forecast.get('forecasts', []))} days")
            print(f"✅ Alerts: {len(alerts.get('alerts', []))} alerts")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test OpenWeatherMap
    print("🌤️  OPENWEATHERMAP API:")
    print("-" * 30)
    try:
        from app.config import settings
        if settings.OPENWEATHER_API_KEY:
            client = OpenWeatherClient(settings.OPENWEATHER_API_KEY)
            async with client:
                current = await client.get_current_weather(lat, lon)
                forecast = await client.get_forecast(lat, lon, 3)
                alerts = await client.get_weather_alerts(lat, lon)
                
                print(f"✅ Current Weather: {current.get('temperature', 'N/A')}°C")
                print(f"✅ Forecast: {len(forecast.get('forecasts', []))} days")
                print(f"✅ Alerts: {len(alerts.get('alerts', []))} alerts")
        else:
            print("❌ No API key configured")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test Environment Canada
    print("🍁 ENVIRONMENT CANADA API:")
    print("-" * 30)
    try:
        client = EnvironmentCanadaClient()
        async with client:
            current = await client.get_current_weather(lat, lon)
            forecast = await client.get_forecast(lat, lon, 3)
            alerts = await client.get_weather_alerts(lat, lon)
            
            print(f"Current Weather: {current.get('temperature', 'N/A')}°C")
            print(f"Forecast: {len(forecast.get('forecasts', []))} days")
            print(f"Alerts: {len(alerts.get('alerts', []))} alerts")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test Weather Unlocked
    print("🔓 WEATHER UNLOCKED API:")
    print("-" * 30)
    try:
        from app.config import settings
        if settings.WEATHER_UNLOCKED_APP_ID and settings.WEATHER_UNLOCKED_API_KEY:
            client = WeatherUnlockedClient(settings.WEATHER_UNLOCKED_APP_ID, settings.WEATHER_UNLOCKED_API_KEY)
            async with client:
                current = await client.get_current_weather(lat, lon)
                forecast = await client.get_forecast(lat, lon, 3)
                alerts = await client.get_weather_alerts(lat, lon)
                
                print(f"✅ Current Weather: {current.get('temperature', 'N/A')}°C")
                print(f"✅ Forecast: {len(forecast.get('forecasts', []))} days")
                print(f"✅ Alerts: {len(alerts.get('alerts', []))} alerts")
        else:
            print("❌ No API credentials configured")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("✅ Individual API testing completed!")

if __name__ == "__main__":
    asyncio.run(test_individual_apis())
