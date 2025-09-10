#!/usr/bin/env python3
"""
Small API test script - makes only 1 API call to verify the new structure works
This is safe and won't waste API calls
"""

import asyncio
import aiohttp
import sqlite3
from datetime import datetime, date
import os
from app.config import settings

async def test_single_api_call():
    """Make a single small API call to test the new data structure"""
    
    # Test coordinates (Vancouver)
    test_lat = 49.2827
    test_lon = -123.1207
    
    # GEM API parameters for comprehensive weather data
    params = {
        'latitude': test_lat,
        'longitude': test_lon,
        'models': 'gem_seamless',
        'current': [
            'temperature_2m', 'relative_humidity_2m', 'dewpoint_2m',
            'apparent_temperature', 'precipitation', 'rain', 'showers',
            'snowfall', 'snow_depth', 'weather_code', 'pressure_msl',
            'surface_pressure', 'cloud_cover', 'cloud_cover_low',
            'cloud_cover_mid', 'cloud_cover_high', 'visibility',
            'evapotranspiration', 'vapour_pressure_deficit',
            'wind_speed_10m', 'wind_speed_100m', 'wind_direction_10m',
            'wind_direction_100m', 'wind_gusts_10m',
            'soil_temperature_0cm', 'soil_temperature_6cm',
            'soil_temperature_18cm', 'soil_temperature_54cm',
            'soil_moisture_0_1cm', 'soil_moisture_1_3cm',
            'soil_moisture_3_9cm', 'soil_moisture_9_27cm',
            'soil_moisture_27_81cm',
            'cape', 'cin', 'lifted_index', 'showalter_index'
        ]
    }
    
    # Build URL
    base_url = "https://customer-api.open-meteo.com/v1/forecast"
    if settings.OPEN_METEO_API_KEY:
        url = f"{base_url}?apikey={settings.OPEN_METEO_API_KEY}"
    else:
        url = base_url
        params['key'] = 'demo'  # Fallback for testing
    
    print(f"🧪 Testing single API call to: {base_url}")
    print(f"📍 Coordinates: {test_lat}, {test_lon}")
    print(f"🔑 Using API key: {'Yes' if settings.OPEN_METEO_API_KEY else 'No'}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                print(f"📡 Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ API call successful!")
                    
                    # Show what data we got
                    if 'current' in data:
                        current = data['current']
                        print(f"📊 Data points received: {len(current)}")
                        print(f"🌡️  Temperature: {current.get('temperature_2m', 'N/A')}°C")
                        print(f"💧 Humidity: {current.get('relative_humidity_2m', 'N/A')}%")
                        print(f"🌬️  Wind Speed: {current.get('wind_speed_10m', 'N/A')} m/s")
                        print(f"⚡ CAPE: {current.get('cape', 'N/A')} J/kg")
                        print(f"🛑 CIN: {current.get('cin', 'N/A')} J/kg")
                        
                        # Test storing in new schema
                        await test_store_data(test_lat, test_lon, current)
                        
                    else:
                        print("❌ No 'current' data in response")
                        print(f"Response: {data}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ API call failed: {response.status}")
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"❌ API call error: {e}")

async def test_store_data(lat, lon, weather_data):
    """Test storing data in the new schema"""
    
    # Ensure database exists with new schema
    if not os.path.exists("data/weather_pool.db"):
        print("🔄 Creating new database with schema v2...")
        os.system("python3 migrate_to_schema_v2.py")
    
    conn = sqlite3.connect("data/weather_pool.db")
    cursor = conn.cursor()
    
    try:
        # Insert or get grid point
        cursor.execute("""
            INSERT OR IGNORE INTO grid_points (latitude, longitude, region)
            VALUES (?, ?, ?)
        """, (lat, lon, 'southern' if lat < 40 else 'central' if lat < 50 else 'northern' if lat < 70 else 'arctic'))
        
        cursor.execute("SELECT id FROM grid_points WHERE latitude = ? AND longitude = ?", (lat, lon))
        grid_point_id = cursor.fetchone()[0]
        
        # Insert weather data
        cursor.execute("""
            INSERT OR REPLACE INTO weather_data_3d (
                grid_point_id, date_slice, timestamp_utc, temperature_2m,
                relative_humidity_2m, dewpoint_2m, apparent_temperature,
                precipitation, rain, showers, snowfall, snow_depth,
                weather_code, pressure_msl, surface_pressure,
                cloud_cover, cloud_cover_low, cloud_cover_mid, cloud_cover_high,
                visibility, evapotranspiration, vapour_pressure_deficit,
                wind_speed_10m, wind_speed_100m, wind_direction_10m,
                wind_direction_100m, wind_gusts_10m,
                soil_temperature_0cm, soil_temperature_6cm,
                soil_temperature_18cm, soil_temperature_54cm,
                soil_moisture_0_1cm, soil_moisture_1_3cm,
                soil_moisture_3_9cm, soil_moisture_9_27cm,
                soil_moisture_27_81cm, cape, cin, lifted_index,
                showalter_index, data_source, api_call_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            grid_point_id, date.today(), datetime.utcnow(),
            weather_data.get('temperature_2m'),
            weather_data.get('relative_humidity_2m'),
            weather_data.get('dewpoint_2m'),
            weather_data.get('apparent_temperature'),
            weather_data.get('precipitation'),
            weather_data.get('rain'),
            weather_data.get('showers'),
            weather_data.get('snowfall'),
            weather_data.get('snow_depth'),
            weather_data.get('weather_code'),
            weather_data.get('pressure_msl'),
            weather_data.get('surface_pressure'),
            weather_data.get('cloud_cover'),
            weather_data.get('cloud_cover_low'),
            weather_data.get('cloud_cover_mid'),
            weather_data.get('cloud_cover_high'),
            weather_data.get('visibility'),
            weather_data.get('evapotranspiration'),
            weather_data.get('vapour_pressure_deficit'),
            weather_data.get('wind_speed_10m'),
            weather_data.get('wind_speed_100m'),
            weather_data.get('wind_direction_10m'),
            weather_data.get('wind_direction_100m'),
            weather_data.get('wind_gusts_10m'),
            weather_data.get('soil_temperature_0cm'),
            weather_data.get('soil_temperature_6cm'),
            weather_data.get('soil_temperature_18cm'),
            weather_data.get('soil_temperature_54cm'),
            weather_data.get('soil_moisture_0_1cm'),
            weather_data.get('soil_moisture_1_3cm'),
            weather_data.get('soil_moisture_3_9cm'),
            weather_data.get('soil_moisture_9_27cm'),
            weather_data.get('soil_moisture_27_81cm'),
            weather_data.get('cape'),
            weather_data.get('cin'),
            weather_data.get('lifted_index'),
            weather_data.get('showalter_index'),
            'gem_api',
            'test_call_001'
        ))
        
        conn.commit()
        print("✅ Data stored successfully in new schema!")
        
        # Verify storage
        cursor.execute("SELECT COUNT(*) FROM weather_data_3d WHERE grid_point_id = ?", (grid_point_id,))
        count = cursor.fetchone()[0]
        print(f"📊 Weather records for this point: {count}")
        
    except Exception as e:
        print(f"❌ Storage error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(test_single_api_call())
