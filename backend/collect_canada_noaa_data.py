#!/usr/bin/env python3
"""
Canada NOAA Weather Data Collector
Collects all available weather data from NOAA CDO API for Canada over a given time period
"""

import asyncio
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import os
from dotenv import load_dotenv
from noaa_cdo_api import NOAAClient, Extent
from app.config import settings

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CanadaNOAACollector:
    """Collect weather data from NOAA CDO API for all of Canada"""
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or settings.DATABASE_PATH
        self.noaa_client = None
        self.session = None
        
        # Canada's approximate boundaries
        self.canada_extent = Extent(
            latitude_min=41.7,   # Southern border
            longitude_min=-141.0, # Western border  
            latitude_max=83.1,   # Northern border
            longitude_max=-52.6  # Eastern border
        )
        
        # Initialize NOAA client if token is available
        token = os.getenv('NOAA_CDO_TOKEN')
        if token:
            try:
                self.noaa_client = NOAAClient(token=token)
                logger.info("✅ NOAA CDO API client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize NOAA CDO client: {e}")
        else:
            logger.warning("⚠️ No NOAA CDO token found - using direct APIs only")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.noaa_client:
            try:
                self.noaa_client.close()
            except Exception as e:
                logger.warning(f"Error closing NOAA client: {e}")
    
    async def get_canada_stations(self) -> List[Dict]:
        """Get all weather stations in Canada from NOAA CDO API"""
        if not self.noaa_client:
            logger.warning("⚠️ NOAA CDO client not available")
            return []
        
        try:
            logger.info("🔍 Discovering weather stations in Canada...")
            
            # Get stations in Canada
            stations_response = await self.noaa_client.get_stations(
                extent=self.canada_extent,
                datasetid='GHCND',  # Global Historical Climatology Network Daily
                limit=1000  # Maximum limit
            )
            
            stations = stations_response.get('results', [])
            logger.info(f"✅ Found {len(stations)} weather stations in Canada")
            
            # Filter for stations with recent data (last 5 years)
            recent_cutoff = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
            recent_stations = [
                station for station in stations 
                if station.get('maxdate', '') > recent_cutoff
            ]
            
            logger.info(f"✅ {len(recent_stations)} stations have data from the last 5 years")
            
            return recent_stations
            
        except Exception as e:
            logger.error(f"❌ Error getting Canada stations: {e}")
            return []
    
    async def get_station_weather_data(self, station_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Get weather data for a specific station over a date range"""
        if not self.noaa_client:
            return []
        
        try:
            # Get weather data for the station
            data_response = await self.noaa_client.get_data(
                datasetid='GHCND',
                stationid=station_id,
                startdate=start_date,
                enddate=end_date,
                limit=1000  # Maximum limit per request
            )
            
            data = data_response.get('results', [])
            return data
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get data for station {station_id}: {e}")
            return []
    
    async def collect_canada_weather_data(self, days_back: int = 30) -> Dict[str, Any]:
        """Collect weather data for all of Canada over the specified time period"""
        logger.info(f"🌍 Starting Canada weather data collection for last {days_back} days")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"📅 Date range: {start_date_str} to {end_date_str}")
        
        # Get all stations in Canada
        stations = await self.get_canada_stations()
        if not stations:
            logger.error("❌ No stations found")
            return {'error': 'No stations found'}
        
        # Collect data from each station
        all_weather_data = []
        successful_stations = 0
        failed_stations = 0
        
        logger.info(f"🔄 Collecting data from {len(stations)} stations...")
        
        for i, station in enumerate(stations):
            station_id = station.get('id')
            station_name = station.get('name', 'Unknown')
            
            try:
                # Get weather data for this station
                weather_data = await self.get_station_weather_data(
                    station_id, start_date_str, end_date_str
                )
                
                if weather_data:
                    # Add station info to each weather record
                    for record in weather_data:
                        record['station_info'] = {
                            'id': station_id,
                            'name': station_name,
                            'latitude': station.get('latitude'),
                            'longitude': station.get('longitude'),
                            'elevation': station.get('elevation'),
                            'elevation_unit': station.get('elevationUnit')
                        }
                    
                    all_weather_data.extend(weather_data)
                    successful_stations += 1
                    logger.info(f"✅ Station {i+1}/{len(stations)}: {station_name} - {len(weather_data)} records")
                else:
                    failed_stations += 1
                    logger.warning(f"⚠️ Station {i+1}/{len(stations)}: {station_name} - No data")
                
                # Rate limiting - be nice to the API
                await asyncio.sleep(0.1)  # 100ms delay between requests
                
            except Exception as e:
                failed_stations += 1
                logger.error(f"❌ Station {i+1}/{len(stations)}: {station_name} - Error: {e}")
        
        # Summary
        logger.info(f"📊 Collection Summary:")
        logger.info(f"   Total stations: {len(stations)}")
        logger.info(f"   Successful: {successful_stations}")
        logger.info(f"   Failed: {failed_stations}")
        logger.info(f"   Total weather records: {len(all_weather_data)}")
        
        return {
            'date_range': {
                'start': start_date_str,
                'end': end_date_str,
                'days': days_back
            },
            'stations': {
                'total': len(stations),
                'successful': successful_stations,
                'failed': failed_stations
            },
            'weather_records': len(all_weather_data),
            'data': all_weather_data
        }
    
    def store_data_in_database(self, collection_result: Dict[str, Any]) -> bool:
        """Store the collected data in the database"""
        try:
            logger.info("💾 Storing data in database...")
            
            # Connect to database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist (using our NOAA schema)
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS weather_stations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    elevation REAL,
                    province VARCHAR(50),
                    source VARCHAR(50) NOT NULL DEFAULT 'noaa_cdo',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
                
                CREATE TABLE IF NOT EXISTS daily_weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id VARCHAR(50) NOT NULL,
                    date DATE NOT NULL,
                    temperature_max REAL,
                    temperature_min REAL,
                    temperature_avg REAL,
                    precipitation REAL,
                    snow REAL,
                    snow_depth REAL,
                    wind_speed_avg REAL,
                    wind_speed_max REAL,
                    wind_direction REAL,
                    sunshine_percent REAL,
                    sunshine_minutes REAL,
                    weather_types TEXT,  -- JSON string of weather type codes
                    source VARCHAR(50) NOT NULL DEFAULT 'noaa_cdo',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (station_id) REFERENCES weather_stations(station_id),
                    UNIQUE (station_id, date)
                );
            """)
            
            # Store stations
            stations_data = collection_result.get('data', [])
            stations_added = 0
            
            for record in stations_data:
                station_info = record.get('station_info', {})
                station_id = station_info.get('id')
                
                if station_id:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO weather_stations 
                            (station_id, name, latitude, longitude, elevation, source, updated_at)
                            VALUES (?, ?, ?, ?, ?, 'noaa_cdo', CURRENT_TIMESTAMP)
                        """, (
                            station_id,
                            station_info.get('name', 'Unknown'),
                            station_info.get('latitude'),
                            station_info.get('longitude'),
                            station_info.get('elevation')
                        ))
                        stations_added += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Could not store station {station_id}: {e}")
            
            # Store weather data
            weather_records_added = 0
            
            for record in stations_data:
                station_info = record.get('station_info', {})
                station_id = station_info.get('id')
                date = record.get('date')
                
                if station_id and date:
                    try:
                        # Extract weather parameters
                        weather_types = []
                        for key, value in record.items():
                            if key.startswith('WT') and value:
                                weather_types.append(f"{key}:{value}")
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO daily_weather_data 
                            (station_id, date, temperature_max, temperature_min, temperature_avg,
                             precipitation, snow, snow_depth, wind_speed_avg, wind_speed_max,
                             wind_direction, sunshine_percent, sunshine_minutes, weather_types,
                             source, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'noaa_cdo', CURRENT_TIMESTAMP)
                        """, (
                            station_id,
                            date,
                            record.get('TMAX'),
                            record.get('TMIN'),
                            record.get('TAVG'),
                            record.get('PRCP'),
                            record.get('SNOW'),
                            record.get('SNWD'),
                            record.get('AWND'),
                            record.get('WSF2'),
                            record.get('WDF2'),
                            record.get('PSUN'),
                            record.get('TSUN'),
                            ','.join(weather_types) if weather_types else None
                        ))
                        weather_records_added += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Could not store weather record for {station_id} on {date}: {e}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Database storage complete:")
            logger.info(f"   Stations stored: {stations_added}")
            logger.info(f"   Weather records stored: {weather_records_added}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing data in database: {e}")
            return False

async def main():
    """Main function to collect Canada weather data"""
    print("🇨🇦 Canada NOAA Weather Data Collector")
    print("=" * 50)
    
    # Test with 30 days of data
    days_back = 30
    print(f"📅 Collecting data for the last {days_back} days")
    
    async with CanadaNOAACollector() as collector:
        # Collect the data
        result = await collector.collect_canada_weather_data(days_back)
        
        if 'error' in result:
            print(f"❌ Collection failed: {result['error']}")
            return
        
        # Store in database
        success = collector.store_data_in_database(result)
        
        if success:
            print("🎉 Data collection and storage complete!")
            print(f"   Weather records collected: {result['weather_records']}")
            print(f"   Stations processed: {result['stations']['successful']}/{result['stations']['total']}")
        else:
            print("❌ Data collection succeeded but storage failed")

if __name__ == "__main__":
    asyncio.run(main())

