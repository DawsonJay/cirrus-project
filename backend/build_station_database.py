#!/usr/bin/env python3
"""
Build comprehensive database of all Canadian weather stations from NOAA
This creates a reference database of stations and their active periods
"""

import asyncio
import sqlite3
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import json
import time
from app.config import settings
from app.database.schema_noaa import get_database_connection

class StationDatabaseBuilder:
    def __init__(self):
        self.session = None
        self.station_cache = {}
        self.processed_stations = set()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_canadian_stations(self) -> List[Dict]:
        """Get comprehensive list of all Canadian weather stations from NOAA"""
        print("🔍 Discovering all Canadian weather stations...")
        
        # Strategy 1: Get stations by major Canadian cities
        canadian_cities = [
            {"name": "Toronto", "lat": 43.6532, "lon": -79.3832},
            {"name": "Vancouver", "lat": 49.2827, "lon": -125.1208},
            {"name": "Montreal", "lat": 45.5017, "lon": -73.5673},
            {"name": "Calgary", "lat": 51.0447, "lon": -114.0719},
            {"name": "Edmonton", "lat": 53.5461, "lon": -113.4938},
            {"name": "Ottawa", "lat": 45.4215, "lon": -75.6972},
            {"name": "Winnipeg", "lat": 49.8951, "lon": -97.1384},
            {"name": "Quebec City", "lat": 46.8139, "lon": -71.2080},
            {"name": "Hamilton", "lat": 43.2557, "lon": -79.8711},
            {"name": "Kitchener", "lat": 43.4501, "lon": -80.4829},
            {"name": "London", "lat": 42.9849, "lon": -81.2453},
            {"name": "Victoria", "lat": 48.4284, "lon": -123.3656},
            {"name": "Halifax", "lat": 44.6488, "lon": -63.5752},
            {"name": "Oshawa", "lat": 43.8971, "lon": -78.8658},
            {"name": "Windsor", "lat": 42.3149, "lon": -83.0364},
            {"name": "Saskatoon", "lat": 52.1579, "lon": -106.6702},
            {"name": "Regina", "lat": 50.4452, "lon": -104.6189},
            {"name": "Sherbrooke", "lat": 45.4042, "lon": -71.8929},
            {"name": "Kelowna", "lat": 49.8880, "lon": -119.4960},
            {"name": "Barrie", "lat": 44.3894, "lon": -79.6903},
            {"name": "Abbotsford", "lat": 49.0504, "lon": -122.3045},
            {"name": "Sudbury", "lat": 46.5229, "lon": -81.3182},
            {"name": "Kingston", "lat": 44.2312, "lon": -76.4860},
            {"name": "Saguenay", "lat": 48.4281, "lon": -71.0684},
            {"name": "Trois-Rivières", "lat": 46.3432, "lon": -72.5432},
            {"name": "Guelph", "lat": 43.5448, "lon": -80.2482},
            {"name": "Cambridge", "lat": 43.3616, "lon": -80.3144},
            {"name": "Whitby", "lat": 43.8975, "lon": -78.9428},
            {"name": "Ajax", "lat": 43.8501, "lon": -79.0329},
            {"name": "Milton", "lat": 43.5183, "lon": -79.8774},
            {"name": "St. Catharines", "lat": 43.1594, "lon": -79.2469},
            {"name": "Thunder Bay", "lat": 48.3809, "lon": -89.2477},
            {"name": "Gatineau", "lat": 45.4765, "lon": -75.7013},
            {"name": "Waterloo", "lat": 43.4643, "lon": -80.5204},
            {"name": "Saint John", "lat": 45.2733, "lon": -66.0633},
            {"name": "Dartmouth", "lat": 44.6709, "lon": -63.5773},
            {"name": "Kamloops", "lat": 50.6745, "lon": -120.3273},
            {"name": "Red Deer", "lat": 52.2681, "lon": -113.8112},
            {"name": "Lethbridge", "lat": 49.6939, "lon": -112.8418},
            {"name": "Nanaimo", "lat": 49.1659, "lon": -123.9401},
            {"name": "Sarnia", "lat": 42.9746, "lon": -82.4066},
            {"name": "Chilliwack", "lat": 49.1579, "lon": -121.9514},
            {"name": "Newmarket", "lat": 44.0529, "lon": -79.4593},
            {"name": "Kamloops", "lat": 50.6745, "lon": -120.3273},
            {"name": "Prince George", "lat": 53.9171, "lon": -122.7497},
            {"name": "Medicine Hat", "lat": 50.0394, "lon": -110.6766},
            {"name": "Drummondville", "lat": 45.8834, "lon": -72.4824},
            {"name": "Belleville", "lat": 44.1628, "lon": -77.3832},
            {"name": "Fort McMurray", "lat": 56.7267, "lon": -111.3790},
            {"name": "Prince Albert", "lat": 53.2032, "lon": -105.7531},
            {"name": "Moncton", "lat": 46.0878, "lon": -64.7782},
            {"name": "Saint-Jérôme", "lat": 45.7756, "lon": -74.0036},
            {"name": "Granby", "lat": 45.4000, "lon": -72.7333},
            {"name": "Fredericton", "lat": 45.9636, "lon": -66.6431},
            {"name": "Chatham-Kent", "lat": 42.4032, "lon": -82.1831},
            {"name": "Red Deer", "lat": 52.2681, "lon": -113.8112},
            {"name": "Lethbridge", "lat": 49.6939, "lon": -112.8418},
            {"name": "Sault Ste. Marie", "lat": 46.5219, "lon": -84.3195},
            {"name": "Peterborough", "lat": 44.3091, "lon": -78.3197},
            {"name": "Kawartha Lakes", "lat": 44.3501, "lon": -78.7469},
            {"name": "Sarnia", "lat": 42.9746, "lon": -82.4066},
            {"name": "Chilliwack", "lat": 49.1579, "lon": -121.9514},
            {"name": "Newmarket", "lat": 44.0529, "lon": -79.4593},
            {"name": "Kamloops", "lat": 50.6745, "lon": -120.3273},
            {"name": "Prince George", "lat": 53.9171, "lon": -122.7497},
            {"name": "Medicine Hat", "lat": 50.0394, "lon": -110.6766},
            {"name": "Drummondville", "lat": 45.8834, "lon": -72.4824},
            {"name": "Belleville", "lat": 44.1628, "lon": -77.3832},
            {"name": "Fort McMurray", "lat": 56.7267, "lon": -111.3790},
            {"name": "Prince Albert", "lat": 53.2032, "lon": -105.7531},
            {"name": "Moncton", "lat": 46.0878, "lon": -64.7782},
            {"name": "Saint-Jérôme", "lat": 45.7756, "lon": -74.0036},
            {"name": "Granby", "lat": 45.4000, "lon": -72.7333},
            {"name": "Fredericton", "lat": 45.9636, "lon": -66.6431},
            {"name": "Chatham-Kent", "lat": 42.4032, "lon": -82.1831},
            {"name": "Whitehorse", "lat": 60.7212, "lon": -135.0568},
            {"name": "Yellowknife", "lat": 62.4540, "lon": -114.3718},
            {"name": "Iqaluit", "lat": 63.7467, "lon": -68.5170},
            {"name": "Alert", "lat": 82.5018, "lon": -62.3481},
            {"name": "Resolute", "lat": 74.6975, "lon": -94.8322},
            {"name": "Eureka", "lat": 79.9947, "lon": -85.9336},
            {"name": "Cambridge Bay", "lat": 69.1178, "lon": -105.0594},
            {"name": "Inuvik", "lat": 68.3607, "lon": -133.7230},
            {"name": "Hay River", "lat": 60.8156, "lon": -115.7999},
            {"name": "Fort Smith", "lat": 60.0042, "lon": -111.8937},
            {"name": "Beaufort Sea", "lat": 70.0000, "lon": -140.0000},
            {"name": "Hudson Bay", "lat": 60.0000, "lon": -85.0000},
            {"name": "Labrador", "lat": 54.0000, "lon": -62.0000},
            {"name": "Newfoundland", "lat": 48.0000, "lon": -56.0000},
            {"name": "Nova Scotia", "lat": 44.0000, "lon": -63.0000},
            {"name": "PEI", "lat": 46.0000, "lon": -63.0000},
            {"name": "New Brunswick", "lat": 46.0000, "lon": -66.0000},
            {"name": "Quebec", "lat": 46.0000, "lon": -74.0000},
            {"name": "Ontario", "lat": 44.0000, "lon": -79.0000},
            {"name": "Manitoba", "lat": 53.0000, "lon": -98.0000},
            {"name": "Saskatchewan", "lat": 52.0000, "lon": -106.0000},
            {"name": "Alberta", "lat": 53.0000, "lon": -114.0000},
            {"name": "British Columbia", "lat": 53.0000, "lon": -125.0000},
            {"name": "Yukon", "lat": 64.0000, "lon": -139.0000},
            {"name": "Northwest Territories", "lat": 64.0000, "lon": -114.0000},
            {"name": "Nunavut", "lat": 70.0000, "lon": -90.0000}
        ]
        
        all_stations = set()
        
        # Get stations around each city
        for city in canadian_cities:
            print(f"  📍 Searching around {city['name']}...")
            stations = await self.get_stations_near_location(
                city['lat'], city['lon'], radius_km=200
            )
            all_stations.update(stations)
            await asyncio.sleep(0.1)  # Rate limiting
        
        # Strategy 2: Get stations by Canadian provinces/territories
        canadian_regions = [
            {"name": "Ontario", "lat": 50.0000, "lon": -85.0000},
            {"name": "Quebec", "lat": 53.0000, "lon": -70.0000},
            {"name": "British Columbia", "lat": 53.0000, "lon": -125.0000},
            {"name": "Alberta", "lat": 53.0000, "lon": -114.0000},
            {"name": "Manitoba", "lat": 53.0000, "lon": -98.0000},
            {"name": "Saskatchewan", "lat": 52.0000, "lon": -106.0000},
            {"name": "Nova Scotia", "lat": 44.0000, "lon": -63.0000},
            {"name": "New Brunswick", "lat": 46.0000, "lon": -66.0000},
            {"name": "Newfoundland", "lat": 48.0000, "lon": -56.0000},
            {"name": "PEI", "lat": 46.0000, "lon": -63.0000},
            {"name": "Yukon", "lat": 64.0000, "lon": -139.0000},
            {"name": "Northwest Territories", "lat": 64.0000, "lon": -114.0000},
            {"name": "Nunavut", "lat": 70.0000, "lon": -90.0000}
        ]
        
        for region in canadian_regions:
            print(f"  🗺️  Searching {region['name']}...")
            stations = await self.get_stations_near_location(
                region['lat'], region['lon'], radius_km=500
            )
            all_stations.update(stations)
            await asyncio.sleep(0.1)  # Rate limiting
        
        # Strategy 3: Get stations by latitude/longitude bounds
        print("  🌐 Searching by geographic bounds...")
        bounds_stations = await self.get_stations_by_bounds()
        all_stations.update(bounds_stations)
        
        print(f"✅ Found {len(all_stations)} unique Canadian weather stations")
        return list(all_stations)
    
    async def get_stations_near_location(self, lat: float, lon: float, radius_km: int = 100) -> Set[str]:
        """Get stations near a specific location"""
        try:
            url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
            params = {
                'extent': f"{lat-radius_km/111},{lon-radius_km/111},{lat+radius_km/111},{lon+radius_km/111}",
                'limit': 1000,
                'datacategoryid': 'TEMP',
                'sortfield': 'name',
                'sortorder': 'asc'
            }
            
            headers = {'token': settings.NOAA_CDO_TOKEN}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    stations = set()
                    for station in data.get('results', []):
                        if station.get('id'):
                            stations.add(station['id'])
                    return stations
                else:
                    print(f"    ⚠️  Error {response.status} for location {lat},{lon}")
                    return set()
        except Exception as e:
            print(f"    ❌ Exception for location {lat},{lon}: {e}")
            return set()
    
    async def get_stations_by_bounds(self) -> Set[str]:
        """Get stations by Canadian geographic bounds"""
        try:
            # Canadian bounds: roughly 42N to 84N, 141W to 52W
            url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
            params = {
                'extent': '42,-141,84,-52',  # lat_min, lon_min, lat_max, lon_max
                'limit': 1000,
                'datacategoryid': 'TEMP',
                'sortfield': 'name',
                'sortorder': 'asc'
            }
            
            headers = {'token': settings.NOAA_CDO_TOKEN}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    stations = set()
                    for station in data.get('results', []):
                        if station.get('id'):
                            stations.add(station['id'])
                    return stations
                else:
                    print(f"    ⚠️  Error {response.status} for bounds search")
                    return set()
        except Exception as e:
            print(f"    ❌ Exception for bounds search: {e}")
            return set()
    
    async def get_station_details(self, station_id: str) -> Optional[Dict]:
        """Get detailed information about a specific station"""
        try:
            url = f"https://www.ncei.noaa.gov/cdo-web/api/v2/stations/{station_id}"
            headers = {'token': settings.NOAA_CDO_TOKEN}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"    ⚠️  Error {response.status} for station {station_id}")
                    return None
        except Exception as e:
            print(f"    ❌ Exception for station {station_id}: {e}")
            return None
    
    async def get_station_data_coverage(self, station_id: str) -> Dict:
        """Get data coverage information for a station"""
        try:
            url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
            params = {
                'stationid': station_id,
                'limit': 1,
                'sortfield': 'date',
                'sortorder': 'desc'
            }
            headers = {'token': settings.NOAA_CDO_TOKEN}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    if results:
                        latest_date = results[0].get('date')
                        return {
                            'has_recent_data': True,
                            'latest_date': latest_date,
                            'data_count': data.get('metadata', {}).get('resultset', {}).get('count', 0)
                        }
                    else:
                        return {
                            'has_recent_data': False,
                            'latest_date': None,
                            'data_count': 0
                        }
                else:
                    return {
                        'has_recent_data': False,
                        'latest_date': None,
                        'data_count': 0
                    }
        except Exception as e:
            print(f"    ❌ Exception getting coverage for {station_id}: {e}")
            return {
                'has_recent_data': False,
                'latest_date': None,
                'data_count': 0
            }
    
    def create_station_database(self):
        """Create the station database tables"""
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Create stations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_stations_audit (
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
                has_recent_data BOOLEAN DEFAULT FALSE,
                latest_data_date DATE,
                data_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create station data coverage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS station_data_coverage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id VARCHAR(50) NOT NULL,
                data_type VARCHAR(50) NOT NULL,
                first_date DATE,
                last_date DATE,
                record_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (station_id) REFERENCES weather_stations_audit(station_id),
                UNIQUE (station_id, data_type)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Station database tables created")
    
    async def build_station_database(self):
        """Build comprehensive station database"""
        print("🏗️  Building comprehensive weather station database...")
        
        # Create database tables
        self.create_station_database()
        
        # Get all Canadian stations
        station_ids = await self.get_all_canadian_stations()
        
        print(f"📊 Processing {len(station_ids)} stations...")
        
        conn = get_database_connection()
        cursor = conn.cursor()
        
        processed = 0
        for station_id in station_ids:
            if station_id in self.processed_stations:
                continue
                
            print(f"  🔍 Processing station {station_id} ({processed + 1}/{len(station_ids)})...")
            
            # Get station details
            station_details = await self.get_station_details(station_id)
            if not station_details:
                continue
            
            # Get data coverage
            coverage = await self.get_station_data_coverage(station_id)
            
            # Insert station into database
            cursor.execute('''
                INSERT OR REPLACE INTO weather_stations_audit (
                    station_id, name, latitude, longitude, elevation, state, country,
                    wmo_id, gsn_flag, hcn_flag, first_year, last_year,
                    has_recent_data, latest_data_date, data_count, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                station_id,
                station_details.get('name'),
                station_details.get('latitude'),
                station_details.get('longitude'),
                station_details.get('elevation'),
                station_details.get('state'),
                station_details.get('country'),
                station_details.get('wmo_id'),
                station_details.get('gsn_flag'),
                station_details.get('hcn_flag'),
                station_details.get('first_year'),
                station_details.get('last_year'),
                coverage['has_recent_data'],
                coverage['latest_date'],
                coverage['data_count'],
                coverage['has_recent_data']  # Active if has recent data
            ))
            
            self.processed_stations.add(station_id)
            processed += 1
            
            # Rate limiting
            if processed % 10 == 0:
                conn.commit()
                print(f"    💾 Committed {processed} stations...")
                await asyncio.sleep(1)  # Rate limiting
        
        conn.commit()
        conn.close()
        
        print(f"✅ Station database built with {processed} stations")
        return processed

async def main():
    """Main function to build the station database"""
    async with StationDatabaseBuilder() as builder:
        await builder.build_station_database()

if __name__ == "__main__":
    asyncio.run(main())
