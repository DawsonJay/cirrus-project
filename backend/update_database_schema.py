#!/usr/bin/env python3
"""
Update database schema to include all required columns
"""

import sqlite3
import logging
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database_schema():
    """Update the database schema to include all required columns"""
    db_path = settings.DATABASE_PATH
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔍 Checking current database schema...")
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Existing tables: {tables}")
        
        # Create weather_stations table if it doesn't exist
        cursor.execute("""
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
            )
        """)
        
        # Create daily_weather_data table with all required columns
        cursor.execute("""
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
            )
        """)
        
        # Check current columns in daily_weather_data
        cursor.execute("PRAGMA table_info(daily_weather_data)")
        columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Current daily_weather_data columns: {columns}")
        
        # Add missing columns if they don't exist
        missing_columns = {
            "temperature_avg": "REAL",
            "snow_depth": "REAL", 
            "wind_speed_avg": "REAL",
            "wind_speed_max": "REAL",
            "wind_direction": "REAL",
            "sunshine_percent": "REAL",
            "sunshine_minutes": "REAL",
            "weather_types": "TEXT"
        }
        
        for col_name, col_type in missing_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE daily_weather_data ADD COLUMN {col_name} {col_type}")
                    logger.info(f"✅ Added column: {col_name}")
                except sqlite3.Error as e:
                    logger.error(f"❌ Error adding column {col_name}: {e}")
            else:
                logger.info(f"✅ Column {col_name} already exists")
        
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(daily_weather_data)")
        final_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Final daily_weather_data columns: {final_columns}")
        
        logger.info("🎉 Database schema update complete!")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_database_schema()

