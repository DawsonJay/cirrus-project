#!/usr/bin/env python3
"""
Debug weather data storage
"""

import sqlite3
import logging
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_weather_data():
    """Debug what's actually stored in the weather data"""
    db_path = settings.DATABASE_PATH
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔍 Debugging Weather Data Storage")
        logger.info("=" * 50)
        
        # Check raw data in daily_weather_data
        cursor.execute("SELECT * FROM daily_weather_data LIMIT 3")
        raw_data = cursor.fetchall()
        
        logger.info("📊 Raw Weather Data (first 3 records):")
        for i, record in enumerate(raw_data):
            logger.info(f"   Record {i+1}: {record}")
        
        # Check column names and their positions
        cursor.execute("PRAGMA table_info(daily_weather_data)")
        columns = cursor.fetchall()
        logger.info("\n📋 Column Information:")
        for col in columns:
            logger.info(f"   {col[0]}: {col[1]} ({col[2]})")
        
        # Check specific fields
        cursor.execute("""
            SELECT 
                station_id, 
                date,
                temperature_max,
                temperature_min,
                precipitation,
                snow_depth,
                wind_speed_avg
            FROM daily_weather_data 
            LIMIT 5
        """)
        specific_data = cursor.fetchall()
        
        logger.info("\n🌡️  Specific Weather Fields:")
        for record in specific_data:
            logger.info(f"   {record[0]} on {record[1]}:")
            logger.info(f"      Tmax: {record[2]} (type: {type(record[2])})")
            logger.info(f"      Tmin: {record[3]} (type: {type(record[3])})")
            logger.info(f"      Precip: {record[4]} (type: {type(record[4])})")
            logger.info(f"      Snow: {record[5]} (type: {type(record[5])})")
            logger.info(f"      Wind: {record[6]} (type: {type(record[6])})")
        
        # Check for NULL vs 0 values
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN temperature_max IS NULL THEN 1 END) as tmax_null,
                COUNT(CASE WHEN temperature_max = 0 THEN 1 END) as tmax_zero,
                COUNT(CASE WHEN temperature_max > 0 THEN 1 END) as tmax_positive
            FROM daily_weather_data
        """)
        null_check = cursor.fetchone()
        logger.info(f"\n🔍 Temperature Max Analysis:")
        logger.info(f"   Total records: {null_check[0]}")
        logger.info(f"   NULL values: {null_check[1]}")
        logger.info(f"   Zero values: {null_check[2]}")
        logger.info(f"   Positive values: {null_check[3]}")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    debug_weather_data()

