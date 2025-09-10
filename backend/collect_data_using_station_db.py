#!/usr/bin/env python3
"""
Collect weather data using the station database for efficient targeting
This script uses the pre-built station database to collect data only from relevant stations
"""

import asyncio
import aiohttp
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import time
from app.config import settings
from app.database.schema_noaa import get_database_connection
from dynamic_schema_manager import DynamicSchemaManager
from station_lookup import StationLookup

class EfficientDataCollector:
    def __init__(self):
        self.session = None
        self.schema_manager = DynamicSchemaManager()
        self.station_lookup = StationLookup()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self.station_lookup.close()
    
    async def collect_data_for_period(self, start_date: date, end_date: date, 
                                    max_stations: int = 50) -> Dict:
        """Collect data for a specific time period using the station database"""
        print(f"🚀 Collecting data from {start_date} to {end_date}")
        
        # Get active stations for the period
        print("🔍 Finding active stations...")
        active_stations = self.station_lookup.get_active_stations_for_period(
            start_date, end_date, min_data_points=100
        )
        
        if not active_stations:
            print("❌ No active stations found for the period")
            return {'success': False, 'error': 'No active stations found'}
        
        # Limit to top stations by data quality
        if len(active_stations) > max_stations:
            active_stations = active_stations[:max_stations]
            print(f"📊 Limited to top {max_stations} stations by data quality")
        
        print(f"✅ Found {len(active_stations)} active stations")
        
        # Collect data from each station
        total_records = 0
        successful_stations = 0
        failed_stations = 0
        
        for i, station in enumerate(active_stations):
            print(f"  📡 Collecting from {station['name']} ({station['station_id']}) - {i+1}/{len(active_stations)}")
            
            try:
                records = await self.collect_station_data(
                    station['station_id'], start_date, end_date
                )
                
                if records:
                    total_records += len(records)
                    successful_stations += 1
                    print(f"    ✅ Collected {len(records)} records")
                else:
                    failed_stations += 1
                    print(f"    ⚠️  No data found")
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_stations += 1
                print(f"    ❌ Error: {e}")
        
        print(f"\n📊 Collection Summary:")
        print(f"  Successful stations: {successful_stations}")
        print(f"  Failed stations: {failed_stations}")
        print(f"  Total records collected: {total_records}")
        
        return {
            'success': True,
            'total_records': total_records,
            'successful_stations': successful_stations,
            'failed_stations': failed_stations,
            'stations_processed': len(active_stations)
        }
    
    async def collect_station_data(self, station_id: str, start_date: date, 
                                 end_date: date) -> List[Dict]:
        """Collect data for a specific station and time period"""
        try:
            url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
            params = {
                'stationid': station_id,
                'startdate': start_date.strftime('%Y-%m-%d'),
                'enddate': end_date.strftime('%Y-%m-%d'),
                'limit': 1000,
                'sortfield': 'date',
                'sortorder': 'asc'
            }
            headers = {'token': settings.NOAA_CDO_TOKEN}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    if results:
                        # Process and store the data
                        processed_records = self.process_station_records(station_id, results)
                        return processed_records
                    else:
                        return []
                else:
                    print(f"    ⚠️  API error {response.status} for station {station_id}")
                    return []
        except Exception as e:
            print(f"    ❌ Exception for station {station_id}: {e}")
            return []
    
    def process_station_records(self, station_id: str, records: List[Dict]) -> List[Dict]:
        """Process raw NOAA records and store them in the database"""
        if not records:
            return []
        
        # Group records by date
        daily_data = {}
        for record in records:
            date_str = record.get('date')
            if not date_str:
                continue
            
            # Parse date
            try:
                record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue
            
            if record_date not in daily_data:
                daily_data[record_date] = {}
            
            # Store the data type and value
            data_type = record.get('datatype')
            value = record.get('value')
            
            if data_type and value is not None:
                daily_data[record_date][data_type] = value
        
        # Store processed data
        stored_records = []
        conn = get_database_connection()
        cursor = conn.cursor()
        
        for record_date, data_types in daily_data.items():
            try:
                # Ensure station exists in weather_stations table
                self.ensure_station_exists(cursor, station_id)
                
                # Prepare data for insertion
                insert_data = {
                    'station_id': station_id,
                    'date': record_date,
                    'source': 'NOAA'
                }
                
                # Map NOAA data types to database columns
                data_mapping = {
                    'TMAX': 'temperature_max',
                    'TMIN': 'temperature_min',
                    'TAVG': 'temperature_avg',
                    'PRCP': 'precipitation',
                    'SNOW': 'snow_depth',
                    'SNWD': 'snow_depth',
                    'AWND': 'wind_speed_avg',
                    'WSF2': 'wind_speed_max',
                    'WSF5': 'wind_speed_max',
                    'WSFG': 'wind_speed_max',
                    'WDF2': 'wind_direction',
                    'WDF5': 'wind_direction',
                    'WDFG': 'wind_direction',
                    'PSUN': 'sunshine_percent',
                    'TSUN': 'sunshine_minutes',
                    'WT01': 'weather_types',
                    'WT02': 'weather_types',
                    'WT03': 'weather_types',
                    'WT04': 'weather_types',
                    'WT05': 'weather_types',
                    'WT06': 'weather_types',
                    'WT07': 'weather_types',
                    'WT08': 'weather_types',
                    'WT09': 'weather_types',
                    'WT10': 'weather_types',
                    'WT11': 'weather_types',
                    'WT12': 'weather_types',
                    'WT13': 'weather_types',
                    'WT14': 'weather_types',
                    'WT15': 'weather_types',
                    'WT16': 'weather_types',
                    'WT17': 'weather_types',
                    'WT18': 'weather_types',
                    'WT19': 'weather_types',
                    'WT21': 'weather_types',
                    'WT22': 'weather_types'
                }
                
                # Map the data
                for noaa_type, db_column in data_mapping.items():
                    if noaa_type in data_types:
                        value = data_types[noaa_type]
                        
                        # Convert units if needed
                        if noaa_type in ['TMAX', 'TMIN', 'TAVG']:
                            # Convert from tenths of degrees C to degrees C
                            value = value / 10.0
                        elif noaa_type == 'PRCP':
                            # Convert from tenths of mm to mm
                            value = value / 10.0
                        elif noaa_type in ['SNOW', 'SNWD']:
                            # Convert from mm to mm (already in mm)
                            pass
                        elif noaa_type in ['AWND', 'WSF2', 'WSF5', 'WSFG']:
                            # Convert from tenths of m/s to m/s
                            value = value / 10.0
                        elif noaa_type in ['WDF2', 'WDF5', 'WDFG']:
                            # Wind direction in degrees
                            pass
                        elif noaa_type == 'PSUN':
                            # Sunshine percentage
                            pass
                        elif noaa_type == 'TSUN':
                            # Sunshine minutes
                            pass
                        elif noaa_type.startswith('WT'):
                            # Weather type codes
                            if db_column not in insert_data:
                                insert_data[db_column] = []
                            insert_data[db_column].append(noaa_type)
                            continue
                        
                        insert_data[db_column] = value
                
                # Ensure all required columns exist
                self.schema_manager.ensure_columns_exist(conn, insert_data.keys())
                
                # Build INSERT statement
                columns = list(insert_data.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = [insert_data[col] for col in columns]
                
                # Convert weather_types list to string
                if 'weather_types' in insert_data and isinstance(insert_data['weather_types'], list):
                    weather_types_idx = columns.index('weather_types')
                    values[weather_types_idx] = ','.join(insert_data['weather_types'])
                
                # Insert or replace data
                insert_sql = f'''
                    INSERT OR REPLACE INTO daily_weather_data 
                    ({', '.join(columns)}) 
                    VALUES ({placeholders})
                '''
                
                cursor.execute(insert_sql, values)
                stored_records.append(insert_data)
                
            except Exception as e:
                print(f"    ❌ Error storing data for {station_id} on {record_date}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return stored_records
    
    def ensure_station_exists(self, cursor, station_id: str):
        """Ensure the station exists in the weather_stations table"""
        # Check if station exists
        cursor.execute('SELECT COUNT(*) FROM weather_stations WHERE station_id = ?', (station_id,))
        if cursor.fetchone()[0] > 0:
            return
        
        # Get station info from audit table
        cursor.execute('''
            SELECT name, latitude, longitude, elevation, state, country
            FROM weather_stations_audit
            WHERE station_id = ?
        ''', (station_id,))
        
        result = cursor.fetchone()
        if result:
            # Insert into weather_stations table
            cursor.execute('''
                INSERT INTO weather_stations 
                (station_id, name, latitude, longitude, elevation, province, country, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (station_id, result[0], result[1], result[2], result[3], result[4], result[5], 'NOAA'))

async def main():
    """Test the efficient data collection"""
    # Test with last month of data
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    async with EfficientDataCollector() as collector:
        result = await collector.collect_data_for_period(start_date, end_date, max_stations=20)
        
        if result['success']:
            print(f"\n✅ Data collection completed successfully!")
            print(f"  Total records: {result['total_records']}")
            print(f"  Successful stations: {result['successful_stations']}")
            print(f"  Failed stations: {result['failed_stations']}")
        else:
            print(f"\n❌ Data collection failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
