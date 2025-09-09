"""
Test script to verify API connections
Run this to test if all weather APIs are working
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.weather_service import WeatherService

async def test_api_connections():
    """Test all API connections"""
    print("Testing weather API connections...")
    print("=" * 50)
    
    # Test coordinates for Toronto, Canada
    lat, lon = 43.6532, -79.3832
    
    weather_service = WeatherService()
    
    try:
        # Test current weather
        print("Testing current weather data...")
        current_weather = await weather_service.get_current_weather(lat, lon)
        
        if "error" in current_weather:
            print(f"❌ Error: {current_weather['error']}")
        else:
            print("✅ Current weather data retrieved successfully!")
            print(f"   Temperature: {current_weather.get('temperature', 'N/A')}°C")
            print(f"   Humidity: {current_weather.get('humidity', 'N/A')}%")
            print(f"   Wind Speed: {current_weather.get('wind_speed', 'N/A')} km/h")
            print(f"   Sources: {current_weather.get('sources', [])}")
            print(f"   Source Count: {current_weather.get('source_count', 0)}")
        
        print("\n" + "=" * 50)
        
        # Test forecast
        print("Testing forecast data...")
        forecast = await weather_service.get_forecast(lat, lon, days=3)
        
        if "error" in forecast:
            print(f"❌ Error: {forecast['error']}")
        else:
            print("✅ Forecast data retrieved successfully!")
            print(f"   Forecast Days: {forecast.get('forecast_days', 'N/A')}")
            print(f"   Sources: {forecast.get('sources', [])}")
            print(f"   Source Count: {forecast.get('source_count', 0)}")
        
        print("\n" + "=" * 50)
        
        # Test alerts
        print("Testing weather alerts...")
        alerts = await weather_service.get_weather_alerts(lat, lon)
        
        print("✅ Weather alerts retrieved successfully!")
        print(f"   Alert Count: {alerts.get('alert_count', 0)}")
        print(f"   Sources: {alerts.get('sources', [])}")
        print(f"   Source Count: {alerts.get('source_count', 0)}")
        
        if alerts.get('alerts'):
            print("   Active Alerts:")
            for alert in alerts['alerts']:
                print(f"     - {alert.get('title', 'Unknown')} ({alert.get('source', 'Unknown')})")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All API connection tests completed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_api_connections())
