#!/usr/bin/env python3
"""
Weather Database Operations

This module handles all operations related to the weather database,
including data storage, retrieval, and management of weather records.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

# Database path
DATABASE_PATH = Path(__file__).parent / "data" / "weather_pool.db"

def store_station_data(station_id: str, station_data: Dict[str, List[Dict]]) -> None:
    """
    Store weather data from get_station_data_year() into the weather database.
    
    This function processes the station data dictionary, extracts weather parameters,
    and stores them in the daily_weather_data table with proper data validation.
    
    Args:
        station_id: NOAA station ID (e.g., 'GHCND:CA006158355')
        station_data: Dictionary from get_station_data_year() with dataset IDs as keys
                     and lists of weather records as values
    """
    print(f"🗄️  Storing weather data for station: {station_id}")
    
    # Process each dataset
    total_records = 0
    for dataset_id, records in station_data.items():
        if not records:
            print(f"  ⚠️  No data available from {dataset_id}")
            continue
            
        print(f"  📊 Processing {dataset_id}: {len(records)} records")
        
        # Process records based on dataset type
        if dataset_id == 'GHCND':
            processed_records = _process_ghcnd_records(station_id, records)
        elif dataset_id == 'PRECIP_HLY':
            processed_records = _process_precip_hly_records(station_id, records)
        elif dataset_id == 'NORMAL_DLY':
            processed_records = _process_normal_dly_records(station_id, records)
        else:
            print(f"  ⚠️  Unknown dataset type: {dataset_id}")
            continue
        
        # Store processed records
        if processed_records:
            _store_daily_records(processed_records)
            total_records += len(processed_records)
            print(f"    ✅ Stored {len(processed_records)} daily records")
        else:
            print(f"    ⚠️  No valid records to store from {dataset_id}")
    
    print(f"✅ Total records stored for {station_id}: {total_records}")

def _process_ghcnd_records(station_id: str, records: List[Dict]) -> List[Dict]:
    """
    Process GHCND (Daily Summaries) records into daily weather data format.
    
    Args:
        station_id: NOAA station ID
        records: List of GHCND records from NOAA API
        
    Returns:
        List of processed daily weather records
    """
    # Group records by date
    daily_data = {}
    
    for record in records:
        # Extract date from ISO format
        date_str = record['date'][:10]  # '2024-12-31T00:00:00' -> '2024-12-31'
        datatype = record['datatype']
        value = record['value']
        
        # Initialize daily record if not exists
        if date_str not in daily_data:
            daily_data[date_str] = {
                'station_id': station_id,
                'date': date_str,
                'source': 'noaa_ghcnd'
            }
        
        # Map NOAA datatypes to our database columns
        if datatype == 'TMAX':
            daily_data[date_str]['temperature_max'] = value / 10.0  # Convert from tenths of degrees
        elif datatype == 'TMIN':
            daily_data[date_str]['temperature_min'] = value / 10.0
        elif datatype == 'TAVG':
            daily_data[date_str]['temperature_avg'] = value / 10.0
        elif datatype == 'PRCP':
            daily_data[date_str]['precipitation'] = value / 10.0  # Convert from tenths of mm
        elif datatype == 'SNOW':
            daily_data[date_str]['snowfall'] = value / 10.0  # Convert from tenths of mm
        elif datatype == 'SNWD':
            daily_data[date_str]['snow_depth'] = value / 10.0  # Convert from tenths of mm
        elif datatype == 'WSFG':
            daily_data[date_str]['wind_speed_max'] = value / 10.0  # Convert from tenths of m/s
        elif datatype == 'WSF2':
            daily_data[date_str]['wind_speed_avg'] = value / 10.0
        elif datatype == 'WDFG':
            daily_data[date_str]['wind_direction'] = value
        elif datatype == 'PRES':
            daily_data[date_str]['pressure_mean'] = value / 10.0  # Convert from tenths of hPa
        elif datatype == 'RHUM':
            daily_data[date_str]['humidity_mean'] = value / 10.0  # Convert from tenths of %
        elif datatype == 'VISN':
            daily_data[date_str]['visibility'] = value / 10.0  # Convert from tenths of km
        elif datatype == 'CLDD':
            daily_data[date_str]['cloud_cover'] = value / 10.0  # Convert from tenths of %
        elif datatype == 'SUN':
            daily_data[date_str]['sunshine_minutes'] = value / 10.0  # Convert from tenths of hours
    
    return list(daily_data.values())

def _process_precip_hly_records(station_id: str, records: List[Dict]) -> List[Dict]:
    """
    Process PRECIP_HLY (Hourly Precipitation) records into daily weather data format.
    
    Args:
        station_id: NOAA station ID
        records: List of PRECIP_HLY records from NOAA API
        
    Returns:
        List of processed daily weather records
    """
    # Group records by date and sum hourly precipitation
    daily_data = {}
    
    for record in records:
        # Extract date from ISO format
        date_str = record['date'][:10]  # '2024-12-31T00:00:00' -> '2024-12-31'
        value = record['value']
        
        # Initialize daily record if not exists
        if date_str not in daily_data:
            daily_data[date_str] = {
                'station_id': station_id,
                'date': date_str,
                'source': 'noaa_precip_hly',
                'precipitation': 0.0
            }
        
        # Sum hourly precipitation (convert from tenths of mm)
        if value is not None:
            daily_data[date_str]['precipitation'] += value / 10.0
    
    return list(daily_data.values())

def _process_normal_dly_records(station_id: str, records: List[Dict]) -> List[Dict]:
    """
    Process NORMAL_DLY (Daily Normals) records into daily weather data format.
    
    Args:
        station_id: NOAA station ID
        records: List of NORMAL_DLY records from NOAA API
        
    Returns:
        List of processed daily weather records
    """
    # Group records by date
    daily_data = {}
    
    for record in records:
        # Extract date from ISO format
        date_str = record['date'][:10]  # '2024-12-31T00:00:00' -> '2024-12-31'
        datatype = record['datatype']
        value = record['value']
        
        # Initialize daily record if not exists
        if date_str not in daily_data:
            daily_data[date_str] = {
                'station_id': station_id,
                'date': date_str,
                'source': 'noaa_normal_dly'
            }
        
        # Map NOAA normals datatypes to our database columns
        if datatype == 'DLY-TMAX-NORMAL':
            daily_data[date_str]['temperature_max'] = value / 10.0
        elif datatype == 'DLY-TMIN-NORMAL':
            daily_data[date_str]['temperature_min'] = value / 10.0
        elif datatype == 'DLY-TAVG-NORMAL':
            daily_data[date_str]['temperature_avg'] = value / 10.0
        elif datatype == 'DLY-PRCP-NORMAL':
            daily_data[date_str]['precipitation'] = value / 10.0
        elif datatype == 'DLY-SNOW-NORMAL':
            daily_data[date_str]['snowfall'] = value / 10.0
        elif datatype == 'DLY-SNWD-NORMAL':
            daily_data[date_str]['snow_depth'] = value / 10.0
        elif datatype == 'DLY-WSFG-NORMAL':
            daily_data[date_str]['wind_speed_max'] = value / 10.0
        elif datatype == 'DLY-WSF2-NORMAL':
            daily_data[date_str]['wind_speed_avg'] = value / 10.0
        elif datatype == 'DLY-WDFG-NORMAL':
            daily_data[date_str]['wind_direction'] = value
        elif datatype == 'DLY-PRES-NORMAL':
            daily_data[date_str]['pressure_mean'] = value / 10.0
        elif datatype == 'DLY-RHUM-NORMAL':
            daily_data[date_str]['humidity_mean'] = value / 10.0
        elif datatype == 'DLY-VISN-NORMAL':
            daily_data[date_str]['visibility'] = value / 10.0
        elif datatype == 'DLY-CLDD-NORMAL':
            daily_data[date_str]['cloud_cover'] = value / 10.0
        elif datatype == 'DLY-SUN-NORMAL':
            daily_data[date_str]['sunshine_minutes'] = value / 10.0
    
    return list(daily_data.values())

def _store_daily_records(records: List[Dict]) -> None:
    """
    Store daily weather records in the database.
    
    Args:
        records: List of daily weather records to store
    """
    if not records:
        return
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Prepare insert statement
            columns = list(records[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"""
                INSERT OR REPLACE INTO daily_weather_data 
                ({', '.join(columns)}) 
                VALUES ({placeholders})
            """
            
            # Insert records
            for record in records:
                values = [record.get(col) for col in columns]
                cursor.execute(insert_sql, values)
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error storing daily records: {e}")

def get_weather_data_summary(year: Optional[int] = None, station_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get summary statistics of weather data in the database.
    
    Args:
        year: Optional year to filter by
        station_id: Optional station ID to filter by
    
    Returns:
        Dictionary with summary statistics
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if year:
                where_conditions.append("strftime('%Y', date) = ?")
                params.append(str(year))
            
            if station_id:
                where_conditions.append("station_id = ?")
                params.append(station_id)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Get total records
            cursor.execute(f"SELECT COUNT(*) FROM daily_weather_data {where_clause}", params)
            total_records = cursor.fetchone()[0]
            
            # Get number of stations with data
            cursor.execute(f"SELECT COUNT(DISTINCT station_id) FROM daily_weather_data {where_clause}", params)
            stations_with_data = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute(f"SELECT MIN(date), MAX(date) FROM daily_weather_data {where_clause}", params)
            date_range = cursor.fetchone()
            min_date, max_date = date_range if date_range[0] else (None, None)
            
            # Get sample records
            cursor.execute(f"""
                SELECT station_id, date, temperature_avg, precipitation, wind_speed_avg
                FROM daily_weather_data 
                {where_clause}
                ORDER BY date DESC 
                LIMIT 5
            """, params)
            sample_records = [
                {
                    "station_id": row[0],
                    "date": row[1],
                    "temperature_avg": row[2],
                    "precipitation": row[3],
                    "wind_speed_avg": row[4]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                "total_records": total_records,
                "stations_with_data": stations_with_data,
                "date_range": {
                    "min_date": min_date,
                    "max_date": max_date
                },
                "sample_records": sample_records
            }
            
    except Exception as e:
        print(f"❌ Error getting weather data summary: {e}")
        return {
            "total_records": 0,
            "stations_with_data": 0,
            "date_range": {"min_date": None, "max_date": None},
            "sample_records": []
        }

# TODO: Implement additional weather database operations
# - Weather data retrieval and querying
# - Data validation and quality checks
# - Database schema management
# - Query optimization and indexing
