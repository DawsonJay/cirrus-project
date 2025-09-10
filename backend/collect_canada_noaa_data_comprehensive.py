#!/usr/bin/env python3
"""
Comprehensive Canada NOAA Weather Data Collector
Uses dynamic schema management to handle all available data types
"""

import asyncio
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import logging
import os
from dotenv import load_dotenv
from noaa_cdo_api import NOAAClient, Extent
from app.config import settings
from dynamic_schema_manager import DynamicSchemaManager
import json

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveCanadaNOAACollector:
    """Comprehensive collector for Canada weather data with dynamic schema support"""
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or settings.DATABASE_PATH
        self.noaa_client = None
        self.schema_manager = DynamicSchemaManager(self.database_path)
        
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
    
    async def collect_canada_weather_data_comprehensive(self, days_back: int = 30, max_stations: int = 20) -> Dict[str, Any]:
        """Comprehensive collection of weather data for Canada"""
        logger.info(f"🌍 Starting comprehensive Canada weather data collection")
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
        all_data_types = set()  # Track all data types encountered
        
        # Process in smaller batches to avoid overwhelming the API
        batch_size = 10
        for i in range(0, len(station_ids), batch_size):
            batch_station_ids = station_ids[i:i + batch_size]
            logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(station_ids) + batch_size - 1)//batch_size}")
            
            batch_data = await self.get_station_weather_data_batch(
                batch_station_ids, start_date_str, end_date_str
            )
            
            # Add station info to weather records and track data types
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
                    
                    # Track data types
                    datatype = record.get('datatype')
                    if datatype:
                        all_data_types.add(datatype)
                
                all_weather_data.extend(weather_records)
            
            # Rate limiting between batches
            if i + batch_size < len(station_ids):
                await asyncio.sleep(1)  # 1 second delay between batches
        
        # Ensure database schema supports all encountered data types
        logger.info(f"🔧 Ensuring database schema supports {len(all_data_types)} data types...")
        added_columns = self.schema_manager.ensure_columns_for_data_types(all_data_types)
        if added_columns:
            logger.info(f"✅ Added {len(added_columns)} new columns: {added_columns}")
        
        # Summary
        total_records = len(all_weather_data)
        successful_stations = len([sid for sid in station_ids if sid in batch_data])
        
        logger.info(f"📊 Collection Summary:")
        logger.info(f"   Total stations processed: {len(station_ids)}")
        logger.info(f"   Successful stations: {successful_stations}")
        logger.info(f"   Total weather records: {total_records}")
        logger.info(f"   Data types encountered: {sorted(all_data_types)}")
        
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
            'data_types': sorted(all_data_types),
            'added_columns': added_columns,
            'data': all_weather_data
        }
    
    def store_data_in_database_comprehensive(self, collection_result: Dict[str, Any]) -> bool:
        """Comprehensive database storage with dynamic schema support"""
        try:
            logger.info("💾 Storing data in database (comprehensive)...")
            
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
                                'date': date
                            }
                        
                        # Map NOAA data types to our database fields
                        datatype = record.get('datatype')
                        value = record.get('value')
                        
                        # Convert temperature from tenths of degrees C to degrees C
                        if datatype in ['TMAX', 'TMIN', 'TAVG'] and value is not None:
                            value = value / 10.0
                        
                        # Get the column name for this data type
                        column_name = self.schema_manager.get_column_name(datatype)
                        
                        # Store the value in the appropriate field
                        if datatype.startswith('WT'):
                            # Weather types are boolean flags
                            daily_records[station_id][date][column_name] = 1 if value else 0
                        else:
                            # Regular numeric values
                            daily_records[station_id][date][column_name] = value
            
            # Convert grouped data to list for database insertion
            for station_id, dates in daily_records.items():
                for date, record in dates.items():
                    # Create a comprehensive record with all possible fields
                    weather_data = [record['station_id'], record['date']]
                    
                    # Add all known data type fields
                    for data_type, column_name in self.schema_manager.known_data_types.items():
                        weather_data.append(record.get(column_name))
                    
                    weather_records_to_insert.append(tuple(weather_data))
            
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
                # Create dynamic INSERT statement
                column_names = ['station_id', 'date'] + list(self.schema_manager.known_data_types.values())
                placeholders = ', '.join(['?' for _ in column_names])
                insert_sql = f"""
                    INSERT OR REPLACE INTO daily_weather_data 
                    ({', '.join(column_names)}, source, updated_at)
                    VALUES ({placeholders}, 'noaa_cdo', CURRENT_TIMESTAMP)
                """
                
                cursor.executemany(insert_sql, weather_records_to_insert)
                logger.info(f"✅ Stored {len(weather_records_to_insert)} weather records")
            
            conn.commit()
            conn.close()
            
            logger.info("🎉 Comprehensive database storage complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing data in database: {e}")
            return False

async def main():
    """Main function to collect comprehensive Canada weather data"""
    print("🇨🇦 Comprehensive Canada NOAA Weather Data Collector")
    print("=" * 60)
    
    # Test with 30 days of data, 10 stations
    days_back = 30
    max_stations = 10
    print(f"📅 Collecting data for the last {days_back} days")
    print(f"🎯 Processing up to {max_stations} stations")
    
    async with ComprehensiveCanadaNOAACollector() as collector:
        # Collect the data
        result = await collector.collect_canada_weather_data_comprehensive(days_back, max_stations)
        
        if 'error' in result:
            print(f"❌ Collection failed: {result['error']}")
            return
        
        # Store in database
        success = collector.store_data_in_database_comprehensive(result)
        
        if success:
            print("🎉 Comprehensive data collection and storage complete!")
            print(f"   Weather records collected: {result['weather_records']}")
            print(f"   Stations processed: {result['stations']['successful']}/{result['stations']['total']}")
            print(f"   Data types encountered: {len(result['data_types'])}")
            print(f"   New columns added: {len(result.get('added_columns', []))}")
        else:
            print("❌ Data collection succeeded but storage failed")

if __name__ == "__main__":
    asyncio.run(main())

