#!/usr/bin/env python3
"""
Check and fix database schema issues
"""

import sqlite3
import logging
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_and_fix_schema():
    """Check and fix database schema issues"""
    db_path = settings.DATABASE_PATH
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔍 Checking weather_stations table schema...")
        cursor.execute("PRAGMA table_info(weather_stations)")
        columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"weather_stations columns: {columns}")
        
        # Check if updated_at column exists
        if 'updated_at' not in columns:
            logger.info("Adding updated_at column to weather_stations...")
            cursor.execute("ALTER TABLE weather_stations ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # Check if created_at column exists
        if 'created_at' not in columns:
            logger.info("Adding created_at column to weather_stations...")
            cursor.execute("ALTER TABLE weather_stations ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # Check if is_active column exists
        if 'is_active' not in columns:
            logger.info("Adding is_active column to weather_stations...")
            cursor.execute("ALTER TABLE weather_stations ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(weather_stations)")
        final_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Final weather_stations columns: {final_columns}")
        
        logger.info("🔍 Checking daily_weather_data table schema...")
        cursor.execute("PRAGMA table_info(daily_weather_data)")
        daily_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"daily_weather_data columns: {daily_columns}")
        
        # Check if updated_at column exists
        if 'updated_at' not in daily_columns:
            logger.info("Adding updated_at column to daily_weather_data...")
            cursor.execute("ALTER TABLE daily_weather_data ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(daily_weather_data)")
        final_daily_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Final daily_weather_data columns: {final_daily_columns}")
        
        logger.info("🎉 Schema check and fix complete!")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_and_fix_schema()
