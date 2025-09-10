#!/usr/bin/env python3
"""
Show the current database schema and structure
"""

import sqlite3
from app.config import settings

def show_database_schema():
    """Display the current database schema"""
    try:
        conn = sqlite3.connect(settings.DATABASE_PATH)
        cursor = conn.cursor()
        
        print("🗄️  DATABASE SCHEMA OVERVIEW")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table_name, in tables:
            print(f"\n📋 Table: {table_name}")
            print("-" * 40)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, name, data_type, not_null, default_val, pk = col
                pk_marker = " (PRIMARY KEY)" if pk else ""
                not_null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default_val}" if default_val else ""
                print(f"   {name}: {data_type}{not_null_marker}{default_marker}{pk_marker}")
        
        # Show sample data
        print(f"\n📊 SAMPLE DATA")
        print("-" * 40)
        
        # Weather stations sample
        cursor.execute("SELECT COUNT(*) FROM weather_stations")
        station_count = cursor.fetchone()[0]
        print(f"🌍 Weather Stations: {station_count} total")
        
        if station_count > 0:
            cursor.execute("SELECT station_id, name, latitude, longitude FROM weather_stations LIMIT 3")
            stations = cursor.fetchall()
            for station in stations:
                print(f"   {station[0]}: {station[1]} at ({station[2]}, {station[3]})")
        
        # Weather data sample
        cursor.execute("SELECT COUNT(*) FROM daily_weather_data")
        data_count = cursor.fetchone()[0]
        print(f"🌤️  Weather Records: {data_count} total")
        
        if data_count > 0:
            cursor.execute("SELECT station_id, date, temperature_max, temperature_min, precipitation FROM daily_weather_data LIMIT 3")
            records = cursor.fetchall()
            for record in records:
                print(f"   {record[0]} on {record[1]}: Tmax={record[2]}°C, Tmin={record[3]}°C, Precip={record[4]}mm")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    show_database_schema()

