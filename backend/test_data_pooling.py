"""
Test data pooling from multiple weather APIs
"""

import asyncio
import json
from app.services.weather_service import WeatherService

async def test_data_pooling():
    """Test data pooling from multiple APIs"""
    print("Testing Data Pooling from Multiple Weather APIs")
    print("=" * 60)
    
    # Initialize weather service
    weather_service = WeatherService()
    
    # Test coordinates for Toronto
    lat, lon = 43.6532, -79.3832
    
    print(f"Testing coordinates: {lat}, {lon} (Toronto)")
    print()
    
    # Get current weather from all APIs
    print("🌡️  CURRENT WEATHER DATA:")
    print("-" * 40)
    
    current_weather = await weather_service.get_current_weather(lat, lon)
    
    if current_weather:
        print(f"📍 Location: {current_weather['location']['latitude']:.4f}, {current_weather['location']['longitude']:.4f}")
        print(f"🌡️  Temperature: {current_weather['temperature']:.1f}°C")
        print(f"💧 Humidity: {current_weather['humidity']:.1f}%")
        print(f"🌬️  Wind Speed: {current_weather['wind_speed']:.1f} km/h")
        print(f"☁️  Cloud Cover: {current_weather['cloud_cover']:.1f}%")
        print(f"📊 Pressure: {current_weather['pressure']:.1f} hPa")
        print(f"👁️  Visibility: {current_weather['visibility']:.1f} km")
        print(f"🌧️  Precipitation: {current_weather['precipitation']:.1f} mm")
        print(f"📝 Description: {current_weather['weather_description']}")
        print(f"🔗 Sources: {', '.join(current_weather['sources'])}")
        print(f"📊 Source Count: {len(current_weather['sources'])}")
    else:
        print("❌ No current weather data available")
    
    print()
    
    # Get forecast data
    print("📅 FORECAST DATA:")
    print("-" * 40)
    
    forecast = await weather_service.get_forecast(lat, lon, days=3)
    
    if forecast and forecast.get('forecasts'):
        print(f"📊 Forecast Days: {len(forecast['forecasts'])}")
        print(f"🔗 Sources: {', '.join(forecast['sources'])}")
        print(f"📊 Source Count: {len(forecast['sources'])}")
        
        # Show first few forecasts
        print("\nFirst 3 forecasts:")
        for i, f in enumerate(forecast['forecasts'][:3]):
            print(f"  {i+1}. Temp: {f['temperature']:.1f}°C, Humidity: {f['humidity']:.1f}%, Wind: {f['wind_speed']:.1f} km/h")
    else:
        print("❌ No forecast data available")
    
    print()
    
    # Get weather alerts
    print("⚠️  WEATHER ALERTS:")
    print("-" * 40)
    
    alerts = await weather_service.get_weather_alerts(lat, lon)
    
    if alerts and alerts.get('alerts'):
        print(f"📊 Alert Count: {len(alerts['alerts'])}")
        print(f"🔗 Sources: {', '.join(alerts['sources'])}")
        print(f"📊 Source Count: {len(alerts['sources'])}")
        
        for alert in alerts['alerts']:
            print(f"  ⚠️  {alert['title']}: {alert['description']}")
    else:
        print("✅ No weather alerts")
        print(f"🔗 Sources: {', '.join(alerts['sources']) if alerts else 'None'}")
        print(f"📊 Source Count: {len(alerts['sources']) if alerts else 0}")
    
    print()
    print("✅ Data pooling test completed!")

if __name__ == "__main__":
    asyncio.run(test_data_pooling())
