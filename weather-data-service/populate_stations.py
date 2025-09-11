#!/usr/bin/env python3
"""
populate_stations.py - Fetch all Canadian weather stations from NOAA API

This script fetches all Canadian weather stations from the NOAA API
and populates our database with them.
"""

import asyncio
import aiohttp
import os
import json
from database_config import get_database_connection

async def fetch_canadian_stations():
    """Fetch all Canadian weather stations from NOAA API"""
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        print("❌ Error: NOAA_CDO_TOKEN environment variable is required")
        return []
    
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
    headers = {'token': token}
    params = {
        'locationid': 'CA',  # Canada
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
                        
                        print(f"✅ Found {len(results)} stations")
                        all_stations.extend(results)
                        
                        # Check if we got all available stations
                        metadata = data.get('metadata', {})
                        resultset = metadata.get('resultset', {})
                        count = resultset.get('count', 0)
                        
                        if len(all_stations) >= count:
                            print(f"✅ Fetched all {count} stations")
                            break
                        
                        offset += 1000
                    else:
                        print(f"❌ API error: {response.status}")
                        break
                        
            except Exception as e:
                print(f"❌ Error fetching stations: {e}")
                break
    
    return all_stations

def store_stations(stations):
    """Store stations in the database"""
    if not stations:
        print("❌ No stations to store")
        return
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Clear existing stations
        cursor.execute("DELETE FROM all_canadian_stations")
        print(f"🗑️  Cleared existing stations")
        
        # Insert new stations
        for station in stations:
            cursor.execute('''
                INSERT INTO all_canadian_stations (
                    station_id, name, latitude, longitude, elevation, state, country,
                    wmo_id, gsn_flag, hcn_flag, first_year, last_year, active_periods
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (station_id) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    elevation = EXCLUDED.elevation,
                    state = EXCLUDED.state,
                    country = EXCLUDED.country,
                    wmo_id = EXCLUDED.wmo_id,
                    gsn_flag = EXCLUDED.gsn_flag,
                    hcn_flag = EXCLUDED.hcn_flag,
                    first_year = EXCLUDED.first_year,
                    last_year = EXCLUDED.last_year,
                    active_periods = EXCLUDED.active_periods
            ''', (
                station.get('id'),
                station.get('name'),
                station.get('latitude'),
                station.get('longitude'),
                station.get('elevation'),
                station.get('state'),
                station.get('country'),
                station.get('wmo_id'),
                station.get('gsn_flag'),
                station.get('hcn_flag'),
                station.get('mindate', '').split('-')[0] if station.get('mindate') else None,
                station.get('maxdate', '').split('-')[0] if station.get('maxdate') else None,
                json.dumps([{
                    "start": station.get('mindate', ''),
                    "end": station.get('maxdate', ''),
                    "days": 0  # We'll calculate this later
                }])
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Stored {len(stations)} stations in database")
        
    except Exception as e:
        print(f"❌ Error storing stations: {e}")

async def main():
    """Main function"""
    print("🌤️  Populating Canadian Weather Stations")
    print("=" * 50)
    
    # Check for required environment variables
    if not os.getenv('NOAA_CDO_TOKEN'):
        print("❌ Error: NOAA_CDO_TOKEN environment variable is required")
        return
    
    # Fetch stations from NOAA API
    print("📡 Fetching Canadian stations from NOAA API...")
    stations = await fetch_canadian_stations()
    
    if stations:
        print(f"📊 Found {len(stations)} Canadian stations")
        
        # Store stations in database
        print("💾 Storing stations in database...")
        store_stations(stations)
        
        print("✅ Station population complete!")
    else:
        print("❌ No stations found")

if __name__ == "__main__":
    asyncio.run(main())
