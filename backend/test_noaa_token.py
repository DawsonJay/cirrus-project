#!/usr/bin/env python3
"""
Test NOAA CDO API with token
"""

import asyncio
import os
from dotenv import load_dotenv
from app.services.noaa_data_collector import NOAADataCollector

# Load environment variables
load_dotenv()

async def test_with_token():
    """Test NOAA data collector with token"""
    print("🧪 Testing NOAA Data Collector with Token...")
    
    # Check if token is available
    token = os.getenv("NOAA_CDO_TOKEN")
    if not token:
        print("❌ No NOAA_CDO_TOKEN found in environment")
        print("   Add your token to .env file:")
        print("   NOAA_CDO_TOKEN=your_token_here")
        return
    
    print(f"✅ Token found: {token[:10]}...")
    
    async with NOAADataCollector() as collector:
        # Test with Vancouver coordinates
        lat, lon = 49.2827, -123.1207
        
        result = await collector.collect_weather_for_location(lat, lon)
        
        print(f"✅ Collection complete!")
        print(f"   Location: {result['location']}")
        print(f"   Stations found: {result['stations_found']}")
        print(f"   Current weather: {result['current_weather'] is not None}")
        print(f"   Historical records: {len(result['historical_weather'])}")
        print(f"   NOAA CDO available: {result['noaa_cdo_available']}")
        print(f"   NOAA CDO records: {len(result['noaa_cdo_data'])}")
        
        if result['current_weather']:
            print(f"   Current temp: {result['current_weather'].get('temperature')}°C")
        
        if result['historical_weather']:
            print(f"   Latest historical: {result['historical_weather'][0]}")
        
        if result['noaa_cdo_data']:
            print(f"   Latest NOAA CDO: {result['noaa_cdo_data'][0]}")
        else:
            print("   No NOAA CDO data - check token or API limits")

if __name__ == "__main__":
    asyncio.run(test_with_token())

