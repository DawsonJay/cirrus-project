#!/usr/bin/env python3
"""
Simple station database builder - get complete list and filter by coordinates
Much simpler approach: get all stations once, filter by Canadian coordinates
"""

import asyncio
import aiohttp
import sqlite3
from datetime import datetime
from typing import List, Dict, Set
from pathlib import Path
from app.config import settings

def get_database_connection():
    """Get database connection"""
    db_path = Path("data/weather_pool.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

class SimpleStationDatabase:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_stations(self) -> List[Dict]:
        """Get complete list of all stations from NOAA API"""
        print("🔍 Getting complete list of all NOAA stations...")
        
        all_stations = []
        offset = 0
        limit = 1000
        
        while True:
            print(f"  📡 Fetching stations {offset} to {offset + limit}...")
            
            try:
                url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
                params = {
                    'limit': limit,
                    'offset': offset,
                    'sortfield': 'id',
                    'sortorder': 'asc'
                }
                headers = {'token': settings.NOAA_CDO_TOKEN}
                
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        if not results:
                            break
                            
                        all_stations.extend(results)
                        print(f"    ✅ Got {len(results)} stations (total: {len(all_stations)})")
                        
                        # Check if we got fewer results than requested (end of data)
                        if len(results) < limit:
                            break
                            
                        offset += limit
                        
                        # Rate limiting - be more conservative
                        await asyncio.sleep(1.0)
                        
                    else:
                        print(f"    ❌ Error {response.status}")
                        if response.status == 503:
                            print("    ⏳ Service unavailable, waiting 30 seconds...")
                            await asyncio.sleep(30)
                            continue  # Retry this batch
                        else:
                            break
                        
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                break
        
        print(f"✅ Retrieved {len(all_stations)} total stations")
        return all_stations
    
    def filter_canadian_stations(self, all_stations: List[Dict]) -> List[Dict]:
        """Filter stations to only those in Canada based on coordinates"""
        print("🗺️  Filtering for Canadian stations...")
        
        # Canadian geographic bounds (more precise)
        canada_bounds = {
            'min_lat': 41.7,   # Southern border (Point Pelee, Ontario)
            'max_lat': 83.1,   # Northern border (Alert, Nunavut)
            'min_lon': -141.0, # Western border (Yukon/Alaska border)
            'max_lon': -52.6   # Eastern border (Cape Spear, Newfoundland)
        }
        
        canadian_stations = []
        
        for station in all_stations:
            lat = station.get('latitude')
            lon = station.get('longitude')
            
            if lat is None or lon is None:
                continue
                
            # Check if station is within Canadian bounds
            if (canada_bounds['min_lat'] <= lat <= canada_bounds['max_lat'] and
                canada_bounds['min_lon'] <= lon <= canada_bounds['max_lon']):
                canadian_stations.append(station)
        
        print(f"✅ Found {len(canadian_stations)} Canadian stations")
        return canadian_stations
    
    def create_database(self):
        """Create the station database table"""
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS all_canadian_stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255),
                latitude REAL,
                longitude REAL,
                elevation REAL,
                state VARCHAR(50),
                country VARCHAR(50),
                wmo_id VARCHAR(50),
                gsn_flag VARCHAR(10),
                hcn_flag VARCHAR(10),
                first_year INTEGER,
                last_year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database table created")
    
    def store_stations(self, stations: List[Dict]):
        """Store stations in database"""
        print("💾 Storing stations in database...")
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        for station in stations:
            cursor.execute('''
                INSERT OR REPLACE INTO all_canadian_stations (
                    station_id, name, latitude, longitude, elevation, state, country,
                    wmo_id, gsn_flag, hcn_flag, first_year, last_year
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                station.get('first_year'),
                station.get('last_year')
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Stored {len(stations)} stations")
    
    def get_stations_for_period(self, start_year: int, end_year: int) -> List[Dict]:
        """Get stations that were active during a specific period"""
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT station_id, name, latitude, longitude, elevation, state, country,
                   first_year, last_year
            FROM all_canadian_stations
            WHERE first_year <= ? AND last_year >= ?
            ORDER BY name
        ''', (end_year, start_year))
        
        results = cursor.fetchall()
        conn.close()
        
        stations = []
        for row in results:
            stations.append({
                'station_id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'elevation': row[4],
                'state': row[5],
                'country': row[6],
                'first_year': row[7],
                'last_year': row[8]
            })
        
        return stations
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the station database"""
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Total stations
        cursor.execute('SELECT COUNT(*) FROM all_canadian_stations')
        total_stations = cursor.fetchone()[0]
        
        # Date range
        cursor.execute('SELECT MIN(first_year), MAX(last_year) FROM all_canadian_stations')
        date_range = cursor.fetchone()
        
        # Geographic coverage
        cursor.execute('''
            SELECT 
                MIN(latitude), MAX(latitude), 
                MIN(longitude), MAX(longitude)
            FROM all_canadian_stations
        ''')
        geo_coverage = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_stations': total_stations,
            'date_range': {
                'first_year': date_range[0],
                'last_year': date_range[1]
            },
            'geographic_coverage': {
                'min_lat': geo_coverage[0],
                'max_lat': geo_coverage[1],
                'min_lon': geo_coverage[2],
                'max_lon': geo_coverage[3]
            }
        }

async def main():
    """Build the simple station database"""
    async with SimpleStationDatabase() as db:
        # Create database table
        db.create_database()
        
        # Get all stations
        all_stations = await db.get_all_stations()
        
        # Filter for Canadian stations
        canadian_stations = db.filter_canadian_stations(all_stations)
        
        # Store in database
        db.store_stations(canadian_stations)
        
        # Show statistics
        stats = db.get_database_stats()
        print(f"\n📊 Database Statistics:")
        print(f"  Total Canadian stations: {stats['total_stations']}")
        print(f"  Date range: {stats['date_range']['first_year']} - {stats['date_range']['last_year']}")
        print(f"  Geographic coverage: {stats['geographic_coverage']['min_lat']:.2f}°N to {stats['geographic_coverage']['max_lat']:.2f}°N")
        print(f"  Longitude: {stats['geographic_coverage']['min_lon']:.2f}°W to {stats['geographic_coverage']['max_lon']:.2f}°W")
        
        # Test getting stations for a specific period
        print(f"\n🔍 Testing period lookup (2020-2024):")
        active_stations = db.get_stations_for_period(2020, 2024)
        print(f"  Found {len(active_stations)} stations active during 2020-2024")
        
        if active_stations:
            print("  Sample stations:")
            for i, station in enumerate(active_stations[:5]):
                print(f"    {i+1}. {station['name']} ({station['station_id']}) - {station['first_year']}-{station['last_year']}")

if __name__ == "__main__":
    asyncio.run(main())
