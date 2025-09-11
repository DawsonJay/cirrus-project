#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the weather data database with:
1. Station database (all_canadian_stations table)
2. Weather data table (daily_weather_data table)
3. Sample data for testing

Can be run locally or in Docker containers.
"""

import asyncio
import sqlite3
import os
from pathlib import Path
from typing import Dict, Any
from app.config import settings

def create_database_tables():
    """Create all required database tables"""
    print("🗄️  Creating database tables...")
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "weather_pool.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create all_canadian_stations table (used by current codebase)
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
            active_periods TEXT,  -- JSON array of active periods
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create daily_weather_data table (used by current codebase)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            temperature_max REAL,
            temperature_min REAL,
            temperature_mean REAL,
            precipitation REAL,
            snow_depth REAL,
            snow_fall REAL,
            wind_speed_max REAL,
            wind_speed_mean REAL,
            wind_direction REAL,
            pressure_max REAL,
            pressure_min REAL,
            pressure_mean REAL,
            humidity_max REAL,
            humidity_min REAL,
            humidity_mean REAL,
            visibility REAL,
            cloud_cover REAL,
            sunshine_duration REAL,
            source VARCHAR(50) DEFAULT 'noaa',
            data_quality VARCHAR(20) DEFAULT 'good',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(station_id, date)
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stations_location ON all_canadian_stations(latitude, longitude)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stations_active ON all_canadian_stations(first_year, last_year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_weather_station_date ON daily_weather_data(station_id, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_weather_date ON daily_weather_data(date)')
    
    conn.commit()
    conn.close()
    print("✅ Database tables created successfully")

def add_sample_stations():
    """Add some sample Canadian weather stations for testing"""
    print("📡 Adding sample Canadian weather stations...")
    
    db_path = Path("data") / "weather_pool.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Sample Canadian weather stations
    sample_stations = [
        {
            'station_id': 'GHCND:CA001165793',
            'name': '100 MILE HOUSE 6 NE',
            'latitude': 51.65,
            'longitude': -121.30,
            'elevation': 940.0,
            'state': 'BC',
            'country': 'CA',
            'wmo_id': '71845',
            'gsn_flag': None,
            'hcn_flag': None,
            'first_year': 2019,
            'last_year': 2024,
            'active_periods': '[{"start": "2019-01-01", "end": "2024-12-31", "days": 2191}]'
        },
        {
            'station_id': 'GHCND:CA001095790',
            'name': '100 MILE HOUSE',
            'latitude': 51.65,
            'longitude': -121.30,
            'elevation': 940.0,
            'state': 'BC',
            'country': 'CA',
            'wmo_id': '71845',
            'gsn_flag': None,
            'hcn_flag': None,
            'first_year': 2015,
            'last_year': 2020,
            'active_periods': '[{"start": "2015-01-01", "end": "2020-12-31", "days": 2191}]'
        },
        {
            'station_id': 'GHCND:CA006158355',
            'name': 'VANCOUVER INTL A',
            'latitude': 49.20,
            'longitude': -123.18,
            'elevation': 4.0,
            'state': 'BC',
            'country': 'CA',
            'wmo_id': '71892',
            'gsn_flag': None,
            'hcn_flag': None,
            'first_year': 2010,
            'last_year': 2024,
            'active_periods': '[{"start": "2010-01-01", "end": "2024-12-31", "days": 5479}]'
        },
        {
            'station_id': 'GHCND:CA001064390',
            'name': 'TORONTO PEARSON INTL A',
            'latitude': 43.68,
            'longitude': -79.63,
            'elevation': 173.0,
            'state': 'ON',
            'country': 'CA',
            'wmo_id': '71624',
            'gsn_flag': None,
            'hcn_flag': None,
            'first_year': 2010,
            'last_year': 2024,
            'active_periods': '[{"start": "2010-01-01", "end": "2024-12-31", "days": 5479}]'
        },
        {
            'station_id': 'GHCND:CA001064390',
            'name': 'MONTREAL PIERRE ELLIOTT TRUDEAU INTL A',
            'latitude': 45.47,
            'longitude': -73.75,
            'elevation': 36.0,
            'state': 'QC',
            'country': 'CA',
            'wmo_id': '71627',
            'gsn_flag': None,
            'hcn_flag': None,
            'first_year': 2010,
            'last_year': 2024,
            'active_periods': '[{"start": "2010-01-01", "end": "2024-12-31", "days": 5479}]'
        }
    ]
    
    for station in sample_stations:
        cursor.execute('''
            INSERT OR REPLACE INTO all_canadian_stations (
                station_id, name, latitude, longitude, elevation, state, country,
                wmo_id, gsn_flag, hcn_flag, first_year, last_year, active_periods
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            station['station_id'],
            station['name'],
            station['latitude'],
            station['longitude'],
            station['elevation'],
            station['state'],
            station['country'],
            station['wmo_id'],
            station['gsn_flag'],
            station['hcn_flag'],
            station['first_year'],
            station['last_year'],
            station['active_periods']
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Added {len(sample_stations)} sample stations")

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    db_path = Path("data") / "weather_pool.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Count stations
    cursor.execute('SELECT COUNT(*) FROM all_canadian_stations')
    station_count = cursor.fetchone()[0]
    
    # Count weather records
    cursor.execute('SELECT COUNT(*) FROM daily_weather_data')
    weather_count = cursor.fetchone()[0]
    
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
        'stations': station_count,
        'weather_records': weather_count,
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

def main():
    """Initialize the database"""
    print("🌤️  Weather Data Service - Database Initialization")
    print("=" * 60)
    
    # Check for required environment variables
    if not os.getenv('NOAA_CDO_TOKEN'):
        print("⚠️  Warning: NOAA_CDO_TOKEN not set - some features may not work")
        print("   Set it with: export NOAA_CDO_TOKEN=your_token_here")
    
    # Create database tables
    create_database_tables()
    
    # Add sample stations
    add_sample_stations()
    
    # Show statistics
    stats = get_database_stats()
    print(f"\n📊 Database Statistics:")
    print(f"  Stations: {stats['stations']}")
    print(f"  Weather records: {stats['weather_records']}")
    print(f"  Date range: {stats['date_range']['first_year']} - {stats['date_range']['last_year']}")
    print(f"  Geographic coverage:")
    print(f"    Latitude: {stats['geographic_coverage']['min_lat']:.2f}° to {stats['geographic_coverage']['max_lat']:.2f}°")
    print(f"    Longitude: {stats['geographic_coverage']['min_lon']:.2f}° to {stats['geographic_coverage']['max_lon']:.2f}°")
    
    print(f"\n✅ Database initialization complete!")
    print(f"   Database location: {Path('data/weather_pool.db').absolute()}")
    print(f"   Ready for weather data collection!")

if __name__ == "__main__":
    main()
