#!/usr/bin/env python3
"""
Fetch all stations within Canadian coordinates and save to unfiltered_stations.json
"""

import json
import asyncio
import aiohttp
import os

async def fetch_all_stations_unfiltered():
    """Fetch ALL stations within Canadian bounds without any filtering"""
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        print('❌ NOAA_CDO_TOKEN not found in environment')
        return []
    
    print('🌤️  Fetching ALL stations within Canadian coordinates')
    print('=' * 60)
    
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
    headers = {'token': token}
    params = {
        'extent': '41.0,-141.0,84.0,-52.0',  # lat_min,lon_min,lat_max,lon_max
        'limit': 1000,  # Max per request
        'sortfield': 'name',
        'sortorder': 'asc'
    }
    
    all_stations = []
    offset = 0
    
    async with aiohttp.ClientSession() as session:
        while True:
            params['offset'] = offset
            print(f"📡 Fetching stations {offset + 1}-{offset + 1000}...")
            
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        if not results:
                            print("✅ No more stations found")
                            break
                        
                        all_stations.extend(results)
                        print(f"✅ Found {len(results)} stations (total: {len(all_stations)})")
                        offset += 1000
                        
                        # Add a small delay to be nice to the API
                        await asyncio.sleep(0.5)
                        
                    elif response.status == 503:
                        print("❌ API temporarily unavailable (503)")
                        break
                    else:
                        print(f"❌ API error: {response.status}")
                        break
                        
            except Exception as e:
                print(f"❌ Error fetching stations: {e}")
                break
    
    return all_stations

async def main():
    """Main function to fetch and save unfiltered stations"""
    stations = await fetch_all_stations_unfiltered()
    
    if stations:
        # Save the unfiltered stations
        with open('unfiltered_stations.json', 'w') as f:
            json.dump(stations, f, indent=2)
        
        print(f'💾 Saved {len(stations)} unfiltered stations to unfiltered_stations.json')
        
        # Show some sample station names
        print('\n📊 Sample station names:')
        for i, station in enumerate(stations[:10]):
            print(f'  {i+1}: {station.get("name", "Unknown")}')
    else:
        print('❌ No stations fetched')

if __name__ == "__main__":
    asyncio.run(main())
