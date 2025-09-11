#!/usr/bin/env python3
"""
Startup script to load Canadian stations into the database if it's empty.
This ensures the database is populated before starting data collection.
"""

import json
import os
from database_config import get_database_connection

def check_database_status():
    """Check if the stations database has any data"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if stations table exists and has data
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'all_canadian_stations'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            print("❌ Stations table doesn't exist")
            conn.close()
            return False, 0
        
        cursor.execute("SELECT COUNT(*) FROM all_canadian_stations")
        station_count = cursor.fetchone()[0]
        
        conn.close()
        return True, station_count
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False, 0

def load_canadian_stations():
    """Load Canadian stations from JSON file into the database"""
    try:
        # Check if JSON file exists
        if not os.path.exists('canadian_stations.json'):
            print("❌ canadian_stations.json not found")
            return False
        
        # Load stations from JSON
        with open('canadian_stations.json', 'r') as f:
            stations = json.load(f)
        
        print(f"📖 Loaded {len(stations)} stations from JSON file")
        
        # Connect to database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Clear existing stations (in case we're reloading)
        print("🗑️  Clearing existing stations...")
        cursor.execute("DELETE FROM all_canadian_stations")
        
        # Insert stations
        print("💾 Loading stations into database...")
        for i, station in enumerate(stations):
            if i % 1000 == 0:
                print(f"  📊 Processed {i}/{len(stations)} stations...")
            
            try:
                # Map NOAA API fields to our database schema
                station_data = (
                    station['id'],  # NOAA uses 'id' not 'station_id'
                    station['name'],
                    station['latitude'],
                    station['longitude'],
                    station.get('elevation', None),  # May not be present
                    station.get('state', None),  # May not be present
                    station.get('country', 'CA'),  # Default to CA for Canadian stations
                    station.get('wmo_id', None),  # May not be present
                    station.get('gsn_flag', None),  # May not be present
                    station.get('hcn_flag', None),  # May not be present
                    station.get('mindate', '').split('-')[0] if station.get('mindate') else None,  # Extract year from mindate
                    station.get('maxdate', '').split('-')[0] if station.get('maxdate') else None,  # Extract year from maxdate
                    '[]'  # Default empty active_periods array
                )
            except KeyError as e:
                print(f"❌ Missing field {e} in station {i}: {station.get('name', 'Unknown')}")
                print(f"   Available fields: {list(station.keys())}")
                raise
            
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
            ''', station_data)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully loaded {len(stations)} stations into database")
        return True
        
    except Exception as e:
        print(f"❌ Error loading stations: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Weather Data Service Startup")
    print("=" * 50)
    
    # Check database status
    print("🔍 Checking database status...")
    table_exists, station_count = check_database_status()
    
    if not table_exists:
        print("❌ Database table doesn't exist. Please run init_database.py first.")
        return False
    
    if station_count == 0:
        print("📊 Database is empty, loading Canadian stations...")
        success = load_canadian_stations()
        if success:
            print("✅ Database populated successfully!")
        else:
            print("❌ Failed to populate database")
            return False
    elif station_count < 8000:
        print(f"📊 Database has only {station_count} stations (expected ~8,922), reloading...")
        success = load_canadian_stations()
        if success:
            print("✅ Database reloaded successfully!")
        else:
            print("❌ Failed to reload database")
            return False
    else:
        print(f"✅ Database already has {station_count} stations")
    
    # Final verification
    table_exists, final_count = check_database_status()
    if table_exists and final_count > 0:
        print(f"🎉 Ready! Database contains {final_count} Canadian weather stations")
        return True
    else:
        print("❌ Database verification failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
