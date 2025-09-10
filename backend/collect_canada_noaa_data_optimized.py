#!/usr/bin/env python3
"""
Optimized Canada NOAA Weather Data Collector
Fast, efficient collection of weather data from NOAA CDO API for Canada
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
import json

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedCanadaNOAACollector:
    """Optimized collector for Canada weather data from NOAA CDO API"""
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or settings.DATABASE_PATH
        self.noaa_client = None
        
        # Canada's boundaries (more precise)
        self.canada_extent = Extent(
            latitude_min=41.7,   # Southern border
            longitude_min=-141.0, # Western border  
            latitude_max=83.1,   # Northern border
            longitude_max=-52.6  # Eastern border
        )
        
        # Initialize NOAA client
        token = os.getenv('NOAA_CDO_TOKEN')
        if token:
            try:
                self.noaa_client = NOAAClient(token=token)
                logger.info("✅ NOAA CDO API client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize NOAA CDO client: {e}")
        else:
            logger.error("❌ No NOAA CDO token found")
            raise ValueError("NOAA CDO token is required")
    
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.noaa_client:
            try:
                self.noaa_client.close()
            except Exception as e:
                logger.warning(f"Error closing NOAA client: {e}")
    
    async def get_canada_stations_batch(self, limit: int = 1000) -> List[Dict]:
        """Get weather stations in Canada with better error handling"""
        if not self.noaa_client:
            return []
        
        try:
            logger.info(f"🔍 Discovering weather stations in Canada (limit: {limit})...")
            
            # Get stations in Canada with better parameters
            stations_response = await self.noaa_client.get_stations(
                extent=self.canada_extent,
                datasetid='GHCND',
                limit=limit
            )
            
            stations = stations_response.get('results', [])
            logger.info(f"✅ Found {len(stations)} weather stations in Canada")
            
            # Filter for stations with recent data (last 2 years)
            recent_cutoff = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
            recent_stations = [
                station for station in stations 
                if station.get('maxdate', '') > recent_cutoff
            ]
            
            logger.info(f"✅ {len(recent_stations)} stations have data from the last 2 years")
            
            # Sort by most recent data first, then by data coverage
            recent_stations.sort(key=lambda x: (x.get('maxdate', ''), x.get('datacoverage', 0)), reverse=True)
            
            return recent_stations[:100]  # Limit to top 100 stations for testing
            
        except Exception as e:
            logger.error(f"❌ Error getting Canada stations: {e}")
            return []
    
    async def get_station_weather_data_batch(self, station_ids: List[str], start_date: str, end_date: str) -> Dict[str, List[Dict]]:
        """Get weather data for multiple stations in parallel"""
        if not self.noaa_client or not station_ids:
            return {}
        
        logger.info(f"🔄 Collecting weather data for {len(station_ids)} stations...")
        
        # Create tasks for parallel execution
        tasks = []
        for station_id in station_ids:
            task = self._get_single_station_data(station_id, start_date, end_date)
            tasks.append(task)
        
        # Execute all tasks in parallel with limited concurrency
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(*[bounded_task(task) for task in tasks], return_exceptions=True)
        
        # Process results
        station_data = {}
        successful = 0
        failed = 0
        
        for i, result in enumerate(results):
            station_id = station_ids[i]
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Station {station_id}: {result}")
                failed += 1
            elif result:
                station_data[station_id] = result
                successful += 1
            else:
                failed += 1
        
        logger.info(f"📊 Batch collection: {successful} successful, {failed} failed")
        return station_data
    
    async def _get_single_station_data(self, station_id: str, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """Get weather data for a single station"""
        try:
            # Get weather data for the station
            data_response = await self.noaa_client.get_data(
                datasetid='GHCND',
                stationid=station_id,
                startdate=start_date,
                enddate=end_date,
                limit=1000
            )
            
            data = data_response.get('results', [])
            return data if data else None
            
        except Exception as e:
            logger.debug(f"⚠️ Could not get data for station {station_id}: {e}")
            return None
    
    async def collect_canada_weather_data_optimized(self, days_back: int = 30, max_stations: int = 50) -> Dict[str, Any]:
        """Optimized collection of weather data for Canada"""
        logger.info(f"🌍 Starting optimized Canada weather data collection")
        logger.info(f"📅 Last {days_back} days, max {max_stations} stations")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"📅 Date range: {start_date_str} to {end_date_str}")
        
        # Get stations
        stations = await self.get_canada_stations_batch(limit=1000)
        if not stations:
            logger.error("❌ No stations found")
            return {'error': 'No stations found'}
        
        # Limit stations for testing
        stations = stations[:max_stations]
        station_ids = [station.get('id') for station in stations if station.get('id')]
        
        logger.info(f"🎯 Processing {len(station_ids)} stations")
        
        # Collect data in batches
        all_weather_data = []
        station_info = {station['id']: station for station in stations}
        
        # Process in smaller batches to avoid overwhelming the API
        batch_size = 10
        for i in range(0, len(station_ids), batch_size):
            batch_station_ids = station_ids[i:i + batch_size]
            logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(station_ids) + batch_size - 1)//batch_size}")
            
            batch_data = await self.get_station_weather_data_batch(
                batch_station_ids, start_date_str, end_date_str
            )
            
            # Add station info to weather records
            for station_id, weather_records in batch_data.items():
                station = station_info.get(station_id, {})
                for record in weather_records:
                    record['station_info'] = {
                        'id': station_id,
                        'name': station.get('name', 'Unknown'),
                        'latitude': station.get('latitude'),
                        'longitude': station.get('longitude'),
                        'elevation': station.get('elevation'),
                        'elevation_unit': station.get('elevationUnit'),
                        'datacoverage': station.get('datacoverage')
                    }
                
                all_weather_data.extend(weather_records)
            
            # Rate limiting between batches
            if i + batch_size < len(station_ids):
                await asyncio.sleep(1)  # 1 second delay between batches
        
        # Summary
        total_records = len(all_weather_data)
        successful_stations = len([sid for sid in station_ids if sid in batch_data])
        
        logger.info(f"📊 Collection Summary:")
        logger.info(f"   Total stations processed: {len(station_ids)}")
        logger.info(f"   Successful stations: {successful_stations}")
        logger.info(f"   Total weather records: {total_records}")
        
        return {
            'date_range': {
                'start': start_date_str,
                'end': end_date_str,
                'days': days_back
            },
            'stations': {
                'total': len(station_ids),
                'successful': successful_stations,
                'failed': len(station_ids) - successful_stations
            },
            'weather_records': total_records,
            'data': all_weather_data
        }
    
    def store_data_in_database_optimized(self, collection_result: Dict[str, Any]) -> bool:
        """Optimized database storage with batch operations"""
        try:
            logger.info("💾 Storing data in database (optimized)...")
            
            # Connect to database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Ensure tables exist
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
                    weather_types TEXT,
                    source VARCHAR(50) NOT NULL DEFAULT 'noaa_cdo',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (station_id) REFERENCES weather_stations(station_id),
                    UNIQUE (station_id, date)
                );
            """)
            
            # Prepare data for batch insertion
            stations_data = collection_result.get('data', [])
            
            # Batch insert stations
            stations_to_insert = []
            weather_records_to_insert = []
            
            # Group weather data by station and date
            daily_records = {}
            station_info_map = {}
            
            for record in stations_data:
                station_info = record.get('station_info', {})
                station_id = station_info.get('id')
                
                if station_id:
                    # Store station info
                    station_info_map[station_id] = station_info
                    
                    # Prepare station data
                    station_data = (
                        station_id,
                        station_info.get('name', 'Unknown'),
                        station_info.get('latitude'),
                        station_info.get('longitude'),
                        station_info.get('elevation')
                    )
                    stations_to_insert.append(station_data)
                    
                    # Group weather data by date
                    date = record.get('date', '').split('T')[0]  # Get just the date part
                    if date:
                        if station_id not in daily_records:
                            daily_records[station_id] = {}
                        if date not in daily_records[station_id]:
                            daily_records[station_id][date] = {
                                'station_id': station_id,
                                'date': date,
                                'weather_types': []
                            }
                        
                        # Map NOAA data types to our database fields
                        datatype = record.get('datatype')
                        value = record.get('value')
                        
                        # Convert temperature from tenths of degrees C to degrees C
                        if datatype in ['TMAX', 'TMIN', 'TAVG'] and value is not None:
                            value = value / 10.0
                        
                        # Store the value in the appropriate field
                        if datatype == 'TMAX':
                            daily_records[station_id][date]['temperature_max'] = value
                        elif datatype == 'TMIN':
                            daily_records[station_id][date]['temperature_min'] = value
                        elif datatype == 'TAVG':
                            daily_records[station_id][date]['temperature_avg'] = value
                        elif datatype == 'PRCP':
                            daily_records[station_id][date]['precipitation'] = value
                        elif datatype == 'SNWD':
                            daily_records[station_id][date]['snow_depth'] = value
                        elif datatype == 'AWND':
                            daily_records[station_id][date]['wind_speed_avg'] = value
                        elif datatype == 'WSF2':
                            daily_records[station_id][date]['wind_speed_max'] = value
                        elif datatype == 'WDF2':
                            daily_records[station_id][date]['wind_direction'] = value
                        elif datatype == 'PSUN':
                            daily_records[station_id][date]['sunshine_percent'] = value
                        elif datatype == 'TSUN':
                            daily_records[station_id][date]['sunshine_minutes'] = value
                        elif datatype.startswith('WT'):
                            daily_records[station_id][date]['weather_types'].append(f"{datatype}:{value}")
            
            # Convert grouped data to list for database insertion
            for station_id, dates in daily_records.items():
                for date, record in dates.items():
                    weather_data = (
                        record['station_id'],
                        record['date'],
                        record.get('temperature_max'),
                        record.get('temperature_min'),
                        record.get('temperature_avg'),
                        record.get('precipitation'),
                        record.get('snow_depth'),
                        record.get('wind_speed_avg'),
                        record.get('wind_speed_max'),
                        record.get('wind_direction'),
                        record.get('sunshine_percent'),
                        record.get('sunshine_minutes'),
                        ','.join(record['weather_types']) if record['weather_types'] else None
                    )
                    weather_records_to_insert.append(weather_data)
            
            # Batch insert stations
            if stations_to_insert:
                cursor.executemany("""
                    INSERT OR REPLACE INTO weather_stations 
                    (station_id, name, latitude, longitude, elevation, source, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'noaa_cdo', CURRENT_TIMESTAMP)
                """, stations_to_insert)
                logger.info(f"✅ Stored {len(stations_to_insert)} stations")
            
            # Batch insert weather data
            if weather_records_to_insert:
                cursor.executemany("""
                    INSERT OR REPLACE INTO daily_weather_data 
                    (station_id, date, temperature_max, temperature_min, temperature_avg,
                     precipitation, snow_depth, wind_speed_avg, wind_speed_max,
                     wind_direction, sunshine_percent, sunshine_minutes, weather_types,
                     source, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'noaa_cdo', CURRENT_TIMESTAMP)
                """, weather_records_to_insert)
                logger.info(f"✅ Stored {len(weather_records_to_insert)} weather records")
            
            conn.commit()
            conn.close()
            
            logger.info("🎉 Database storage complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing data in database: {e}")
            return False

async def main():
    """Main function to collect Canada weather data"""
    print("🇨🇦 Optimized Canada NOAA Weather Data Collector")
    print("=" * 60)
    
    # Test with 30 days of data, 20 stations
    days_back = 30
    max_stations = 20
    print(f"📅 Collecting data for the last {days_back} days")
    print(f"🎯 Processing up to {max_stations} stations")
    
    async with OptimizedCanadaNOAACollector() as collector:
        # Collect the data
        result = await collector.collect_canada_weather_data_optimized(days_back, max_stations)
        
        if 'error' in result:
            print(f"❌ Collection failed: {result['error']}")
            return
        
        # Store in database
        success = collector.store_data_in_database_optimized(result)
        
        if success:
            print("🎉 Data collection and storage complete!")
            print(f"   Weather records collected: {result['weather_records']}")
            print(f"   Stations processed: {result['stations']['successful']}/{result['stations']['total']}")
        else:
            print("❌ Data collection succeeded but storage failed")

if __name__ == "__main__":
    asyncio.run(main())
