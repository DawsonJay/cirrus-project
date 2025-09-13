#!/usr/bin/env python3
"""
Populate SQLite database with Canadian NOAA weather data and metadata
"""

import sqlite3
import os
from pathlib import Path
import logging
from datetime import datetime
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database and data paths
DB_PATH = "data/weather_data.db"
RAW_DATA_DIR = "data/raw"
STATIONS_FILE = RAW_DATA_DIR + "/ghcnd-stations.txt"
INVENTORY_FILE = RAW_DATA_DIR + "/ghcnd-inventory.txt"
CANADIAN_STATIONS_DIR = RAW_DATA_DIR + "/canadian_stations"

def parse_stations_file():
    """Parse ghcnd-stations.txt and return Canadian stations"""
    logger.info("Parsing station metadata...")
    
    canadian_stations = []
    
    with open(STATIONS_FILE, 'r') as f:
        for line in f:
            if line.startswith('CA'):  # Only Canadian stations
                # Parse fixed-width format
                station_id = line[0:11].strip()
                latitude = float(line[12:20].strip())
                longitude = float(line[21:30].strip())
                elevation = float(line[31:37].strip()) if line[31:37].strip() != '-999.9' else None
                name = line[41:71].strip()
                country = 'CA'
                
                # Extract state/province from name (usually at the end)
                state = None
                if ' BC ' in name:
                    state = 'BC'
                elif ' AB ' in name:
                    state = 'AB'
                elif ' SK ' in name:
                    state = 'SK'
                elif ' MB ' in name:
                    state = 'MB'
                elif ' ON ' in name:
                    state = 'ON'
                elif ' QC ' in name:
                    state = 'QC'
                elif ' NB ' in name:
                    state = 'NB'
                elif ' NS ' in name:
                    state = 'NS'
                elif ' PE ' in name:
                    state = 'PE'
                elif ' NL ' in name:
                    state = 'NL'
                elif ' YT ' in name:
                    state = 'YT'
                elif ' NT ' in name:
                    state = 'NT'
                elif ' NU ' in name:
                    state = 'NU'
                
                canadian_stations.append({
                    'station_id': station_id,
                    'name': name,
                    'latitude': latitude,
                    'longitude': longitude,
                    'elevation': elevation,
                    'country': country,
                    'state': state
                })
    
    logger.info(f"Found {len(canadian_stations)} Canadian stations")
    return canadian_stations

def parse_inventory_file():
    """Parse ghcnd-inventory.txt and return Canadian station inventory"""
    logger.info("Parsing station inventory...")
    
    canadian_inventory = []
    
    with open(INVENTORY_FILE, 'r') as f:
        for line in f:
            if line.startswith('CA'):  # Only Canadian stations
                # Parse fixed-width format
                station_id = line[0:11].strip()
                latitude = float(line[12:20].strip())
                longitude = float(line[21:30].strip())
                parameter = line[31:35].strip()
                start_year = int(line[36:40].strip())
                end_year = int(line[41:45].strip())
                
                canadian_inventory.append({
                    'station_id': station_id,
                    'parameter': parameter,
                    'start_year': start_year,
                    'end_year': end_year,
                    'latitude': latitude,
                    'longitude': longitude
                })
    
    logger.info(f"Found {len(canadian_inventory)} inventory records for Canadian stations")
    return canadian_inventory

def parse_dly_file(file_path):
    """Parse a single .dly file and return weather records"""
    records = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if len(line) >= 35:  # Minimum line length
                    # Parse fixed-width format
                    station_id = line[0:11].strip()
                    year = int(line[11:15])
                    month = int(line[15:17])
                    parameter = line[17:21].strip()
                    
                    # Parse daily values (31 days max)
                    for day in range(1, 32):
                        start_pos = 21 + (day - 1) * 8
                        if start_pos + 7 < len(line):
                            value_str = line[start_pos:start_pos+5].strip()
                            quality_flag = line[start_pos+5:start_pos+6]
                            measurement_flag = line[start_pos+6:start_pos+7]
                            source_flag = line[start_pos+7:start_pos+8]
                            
                            if value_str and value_str != '-9999':
                                try:
                                    # Create date
                                    date_str = f"{year:04d}-{month:02d}-{day:02d}"
                                    
                                    # Validate date
                                    datetime.strptime(date_str, '%Y-%m-%d')
                                    
                                    # Parse value
                                    value = float(value_str)
                                    
                                    records.append({
                                        'station_id': station_id,
                                        'date': date_str,
                                        'parameter': parameter,
                                        'value': value,
                                        'quality_flag': quality_flag,
                                        'measurement_flag': measurement_flag,
                                        'source_flag': source_flag
                                    })
                                    
                                except (ValueError, TypeError):
                                    # Invalid date or value, skip
                                    continue
    
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    
    return records

def populate_database():
    """Main function to populate the database"""
    logger.info("Starting database population...")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Parse and insert station metadata
        logger.info("Step 1: Inserting station metadata...")
        stations = parse_stations_file()
        
        cursor.executemany("""
            INSERT OR REPLACE INTO stations 
            (station_id, name, latitude, longitude, elevation, country, state)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            (s['station_id'], s['name'], s['latitude'], s['longitude'], 
             s['elevation'], s['country'], s['state']) 
            for s in stations
        ])
        
        logger.info(f"Inserted {len(stations)} stations")
        
        # 2. Parse and insert station inventory
        logger.info("Step 2: Inserting station inventory...")
        inventory = parse_inventory_file()
        
        cursor.executemany("""
            INSERT OR REPLACE INTO station_inventory 
            (station_id, parameter, start_year, end_year, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (i['station_id'], i['parameter'], i['start_year'], i['end_year'],
             i['latitude'], i['longitude'])
            for i in inventory
        ])
        
        logger.info(f"Inserted {len(inventory)} inventory records")
        
        # 3. Parse and insert weather data
        logger.info("Step 3: Inserting weather data...")
        
        canadian_stations_dir = Path(CANADIAN_STATIONS_DIR)
        dly_files = list(canadian_stations_dir.glob("*.dly"))
        
        total_records = 0
        files_processed = 0
        
        for dly_file in dly_files:
            records = parse_dly_file(dly_file)
            
            if records:
                cursor.executemany("""
                    INSERT OR REPLACE INTO weather_data 
                    (station_id, date, parameter, value, quality_flag, measurement_flag, source_flag)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [
                    (r['station_id'], r['date'], r['parameter'], r['value'],
                     r['quality_flag'], r['measurement_flag'], r['source_flag'])
                    for r in records
                ])
                
                total_records += len(records)
            
            files_processed += 1
            
            if files_processed % 1000 == 0:
                logger.info(f"Processed {files_processed}/{len(dly_files)} files, {total_records:,} records")
                conn.commit()  # Commit every 1000 files
        
        logger.info(f"Inserted {total_records:,} weather records from {files_processed} files")
        
        # Final commit
        conn.commit()
        
        # 4. Verify data
        logger.info("Step 4: Verifying data...")
        
        cursor.execute("SELECT COUNT(*) FROM stations")
        station_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM station_inventory")
        inventory_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM weather_data")
        weather_count = cursor.fetchone()[0]
        
        logger.info(f"Verification complete:")
        logger.info(f"  Stations: {station_count:,}")
        logger.info(f"  Inventory records: {inventory_count:,}")
        logger.info(f"  Weather records: {weather_count:,}")
        
        # Show data quality summary
        cursor.execute("SELECT * FROM data_quality_summary LIMIT 10")
        quality_data = cursor.fetchall()
        
        logger.info("Data quality summary (top 10 parameters):")
        for row in quality_data:
            logger.info(f"  {row[0]}: {row[1]:,} records, {row[2]:,} non-null, {row[3]:,} null")
        
    except Exception as e:
        logger.error(f"Error during database population: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    logger.info("Database population complete!")

if __name__ == "__main__":
    populate_database()
