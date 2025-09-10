#!/usr/bin/env python3
"""
Test script for the new data pool schema v2
This script tests the database structure without making any API calls
"""

import sqlite3
import os
from datetime import datetime, date

def test_schema():
    """Test the new schema by creating tables and inserting sample data"""
    
    # Create test database
    test_db = "test_weather_pool_v2.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    try:
        # Read and execute schema
        with open('app/database/schema_v2.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema (split by semicolon to handle multiple statements)
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        for statement in statements:
            if statement:
                cursor.execute(statement)
        
        print("✅ Schema created successfully")
        
        # Test inserting sample grid points
        sample_points = [
            (49.2827, -123.1207, 'southern'),  # Vancouver
            (43.6532, -79.3832, 'southern'),  # Toronto
            (45.5017, -73.5673, 'southern'),  # Montreal
            (51.0447, -114.0719, 'central'),  # Calgary
            (44.6488, -63.5752, 'southern'),  # Halifax
            (82.5008, -62.3481, 'arctic'),    # Alert
        ]
        
        for lat, lon, region in sample_points:
            cursor.execute("""
                INSERT INTO grid_points (latitude, longitude, region)
                VALUES (?, ?, ?)
            """, (lat, lon, region))
        
        print(f"✅ Inserted {len(sample_points)} sample grid points")
        
        # Test inserting sample weather data
        cursor.execute("SELECT id FROM grid_points LIMIT 1")
        grid_point_id = cursor.fetchone()[0]
        
        sample_weather = {
            'grid_point_id': grid_point_id,
            'date_slice': date.today(),
            'timestamp_utc': datetime.utcnow(),
            'temperature_2m': 15.5,
            'relative_humidity_2m': 65.0,
            'precipitation': 0.0,
            'wind_speed_10m': 5.2,
            'pressure_msl': 1013.25,
            'cape': 150.0,
            'cin': -25.0,
            'data_source': 'gem_api',
            'api_call_id': 'test_call_001'
        }
        
        # Insert sample weather data
        cursor.execute("""
            INSERT INTO weather_data_3d (
                grid_point_id, date_slice, timestamp_utc, temperature_2m,
                relative_humidity_2m, precipitation, wind_speed_10m,
                pressure_msl, cape, cin, data_source, api_call_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_weather['grid_point_id'],
            sample_weather['date_slice'],
            sample_weather['timestamp_utc'],
            sample_weather['temperature_2m'],
            sample_weather['relative_humidity_2m'],
            sample_weather['precipitation'],
            sample_weather['wind_speed_10m'],
            sample_weather['pressure_msl'],
            sample_weather['cape'],
            sample_weather['cin'],
            sample_weather['data_source'],
            sample_weather['api_call_id']
        ))
        
        print("✅ Inserted sample weather data")
        
        # Test the views
        cursor.execute("SELECT COUNT(*) FROM current_weather")
        current_count = cursor.fetchone()[0]
        print(f"✅ Current weather view: {current_count} records")
        
        cursor.execute("SELECT COUNT(*) FROM data_coverage")
        coverage_count = cursor.fetchone()[0]
        print(f"✅ Data coverage view: {coverage_count} records")
        
        # Test AI prediction tables
        cursor.execute("""
            INSERT INTO ai_models (model_name, model_version, model_type, is_active)
            VALUES (?, ?, ?, ?)
        """, ('test_model', '1.0', 'wildfire_prediction', True))
        
        model_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO weather_predictions_3d (
                grid_point_id, prediction_date, prediction_timestamp,
                model_id, temperature_2m, confidence_score, prediction_horizon_hours
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            grid_point_id,
            date.today(),
            datetime.utcnow(),
            model_id,
            16.0,
            0.85,
            24
        ))
        
        print("✅ Inserted sample AI prediction data")
        
        # Verify data integrity
        cursor.execute("SELECT COUNT(*) FROM grid_points")
        grid_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM weather_data_3d")
        weather_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM weather_predictions_3d")
        prediction_count = cursor.fetchone()[0]
        
        print(f"\n📊 Database Summary:")
        print(f"   Grid points: {grid_count}")
        print(f"   Weather data: {weather_count}")
        print(f"   Predictions: {prediction_count}")
        
        print("\n✅ All schema tests passed!")
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        raise
    finally:
        conn.close()
        # Clean up test database
        if os.path.exists(test_db):
            os.remove(test_db)

if __name__ == "__main__":
    test_schema()
