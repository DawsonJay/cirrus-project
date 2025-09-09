#!/usr/bin/env python3
"""
Test script to find the optimal batch size for Open-Meteo API
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

async def test_batch_size(batch_size: int) -> bool:
    """Test if a specific batch size works"""
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
            response = await client.make_request("/forecast", params, use_post=use_post)
            
            if response and isinstance(response, list) and len(response) == batch_size:
                print(f"✅ Batch size {batch_size}: SUCCESS ({len(response)} points)")
                return True
            else:
                print(f"❌ Batch size {batch_size}: FAILED - Wrong response format")
                return False
                
    except Exception as e:
        print(f"❌ Batch size {batch_size}: FAILED - {e}")
        return False

async def find_optimal_batch_size():
    """Find the largest working batch size using binary search"""
    print("=== FINDING OPTIMAL BATCH SIZE ===\n")
    
    # Test different batch sizes
    test_sizes = [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000]
    
    working_sizes = []
    failed_sizes = []
    
    for size in test_sizes:
        success = await test_batch_size(size)
        if success:
            working_sizes.append(size)
        else:
            failed_sizes.append(size)
        
        # Add longer delay to avoid rate limits
        await asyncio.sleep(10)
    
    print(f"\n=== RESULTS ===")
    print(f"✅ Working batch sizes: {working_sizes}")
    print(f"❌ Failed batch sizes: {failed_sizes}")
    
    if working_sizes:
        max_working = max(working_sizes)
        print(f"\n🎯 RECOMMENDED BATCH SIZE: {max_working}")
        print(f"   This will give you {max_working} coordinates per API call")
        
        # Calculate efficiency for our 4,752 point grid
        total_points = 4752
        batches_needed = (total_points + max_working - 1) // max_working  # Ceiling division
        total_time = batches_needed * 2  # 2 seconds per batch (1 for request + 1 for delay)
        
        print(f"   For {total_points} grid points:")
        print(f"   - Batches needed: {batches_needed}")
        print(f"   - Total time: ~{total_time} seconds")
        print(f"   - API calls: {batches_needed}")
    else:
        print("❌ No working batch sizes found!")

if __name__ == "__main__":
    asyncio.run(find_optimal_batch_size())
