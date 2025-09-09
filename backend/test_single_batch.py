#!/usr/bin/env python3
"""
Test a single batch size to avoid rate limits
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.open_meteo_client import OpenMeteoClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_single_batch_size(batch_size: int):
    """Test a single batch size"""
    print(f"Testing batch size: {batch_size}")
    
    # Generate test coordinates
    coordinates = []
    for i in range(batch_size):
        # Use coordinates across Canada
        lat = 43.0 + (i % 20) * 0.1  # Spread across latitudes
        lon = -79.0 - (i % 30) * 0.1  # Spread across longitudes
        coordinates.append((lat, lon))
    
    try:
        async with OpenMeteoClient() as client:
            params = {
                "latitude": [coord[0] for coord in coordinates],
                "longitude": [coord[1] for coord in coordinates],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "timezone": "auto"
            }
            
            # Use POST for large batches
            use_post = batch_size > 50
            print(f"Using {'POST' if use_post else 'GET'} request...")
            
            response = await client.make_request("/forecast", params, use_post=use_post)
            
            if response and isinstance(response, list) and len(response) == batch_size:
                print(f"✅ SUCCESS: Batch size {batch_size} works!")
                print(f"   Response contains {len(response)} data points")
                print(f"   First point: {response[0].get('latitude', 'N/A')}, {response[0].get('longitude', 'N/A')}")
                return True
            else:
                print(f"❌ FAILED: Wrong response format")
                print(f"   Response type: {type(response)}")
                if isinstance(response, list):
                    print(f"   Response length: {len(response)}")
                return False
                
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])
    else:
        batch_size = 300  # Default test size
    
    print(f"=== TESTING BATCH SIZE {batch_size} ===")
    asyncio.run(test_single_batch_size(batch_size))
