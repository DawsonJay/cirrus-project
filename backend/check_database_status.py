#!/usr/bin/env python3
"""
Check database status and data storage
"""

import sqlite3
import logging
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_status():
    """Check the current state of the database"""
    db_path = settings.DATABASE_PATH
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔍 Database Status Check")
        logger.info("=" * 50)
        
        # Check weather_stations table
        cursor.execute("SELECT COUNT(*) FROM weather_stations")
        station_count = cursor.fetchone()[0]
        logger.info(f"📊 Weather Stations: {station_count}")
        
        if station_count > 0:
            cursor.execute("SELECT station_id, name, latitude, longitude, elevation, source FROM weather_stations LIMIT 5")
            stations = cursor.fetchall()
            logger.info("📍 Sample Stations:")
            for station in stations:
                logger.info(f"   {station[0]}: {station[1]} at ({station[2]}, {station[3]}) elev:{station[4]}m source:{station[5]}")
        
        # Check daily_weather_data table
        cursor.execute("SELECT COUNT(*) FROM daily_weather_data")
        weather_count = cursor.fetchone()[0]
        logger.info(f"🌤️  Weather Records: {weather_count}")
        
        if weather_count > 0:
            # Check date range
            cursor.execute("SELECT MIN(date), MAX(date) FROM daily_weather_data")
            date_range = cursor.fetchone()
            logger.info(f"📅 Date Range: {date_range[0]} to {date_range[1]}")
            
            # Check unique stations with data
            cursor.execute("SELECT COUNT(DISTINCT station_id) FROM daily_weather_data")
            unique_stations = cursor.fetchone()[0]
            logger.info(f"🎯 Unique Stations with Data: {unique_stations}")
            
            # Check data completeness
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(temperature_max) as temp_max_count,
                    COUNT(temperature_min) as temp_min_count,
                    COUNT(precipitation) as precip_count,
                    COUNT(snow_depth) as snow_count,
                    COUNT(wind_speed_avg) as wind_count
                FROM daily_weather_data
            """)
            completeness = cursor.fetchone()
            logger.info("📈 Data Completeness:")
            logger.info(f"   Total Records: {completeness[0]}")
            logger.info(f"   Temperature Max: {completeness[1]} ({completeness[1]/completeness[0]*100:.1f}%)")
            logger.info(f"   Temperature Min: {completeness[2]} ({completeness[2]/completeness[0]*100:.1f}%)")
            logger.info(f"   Precipitation: {completeness[3]} ({completeness[3]/completeness[0]*100:.1f}%)")
            logger.info(f"   Snow Depth: {completeness[4]} ({completeness[4]/completeness[0]*100:.1f}%)")
            logger.info(f"   Wind Speed: {completeness[5]} ({completeness[5]/completeness[0]*100:.1f}%)")
            
            # Sample weather data
            cursor.execute("""
                SELECT station_id, date, temperature_max, temperature_min, precipitation, snow_depth, wind_speed_avg
                FROM daily_weather_data 
                WHERE temperature_max IS NOT NULL 
                LIMIT 3
            """)
            sample_data = cursor.fetchall()
            logger.info("🌡️  Sample Weather Data:")
            for record in sample_data:
                logger.info(f"   {record[0]} on {record[1]}: Tmax={record[2]}°C, Tmin={record[3]}°C, Precip={record[4]}mm, Snow={record[5]}mm, Wind={record[6]}m/s")
        
        # Check table schemas
        logger.info("\n🗄️  Table Schemas:")
        cursor.execute("PRAGMA table_info(weather_stations)")
        station_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"   weather_stations: {', '.join(station_columns)}")
        
        cursor.execute("PRAGMA table_info(daily_weather_data)")
        weather_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"   daily_weather_data: {', '.join(weather_columns)}")
        
        # Check for potential issues
        logger.info("\n⚠️  Potential Issues:")
        
        # Check for stations without coordinates
        cursor.execute("SELECT COUNT(*) FROM weather_stations WHERE latitude IS NULL OR longitude IS NULL")
        missing_coords = cursor.fetchone()[0]
        if missing_coords > 0:
            logger.warning(f"   {missing_coords} stations missing coordinates")
        else:
            logger.info("   ✅ All stations have coordinates")
        
        # Check for duplicate station entries
        cursor.execute("SELECT station_id, COUNT(*) FROM weather_stations GROUP BY station_id HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        if duplicates:
            logger.warning(f"   {len(duplicates)} duplicate station entries found")
        else:
            logger.info("   ✅ No duplicate station entries")
        
        # Check for duplicate weather records
        cursor.execute("SELECT station_id, date, COUNT(*) FROM daily_weather_data GROUP BY station_id, date HAVING COUNT(*) > 1")
        duplicate_weather = cursor.fetchall()
        if duplicate_weather:
            logger.warning(f"   {len(duplicate_weather)} duplicate weather records found")
        else:
            logger.info("   ✅ No duplicate weather records")
        
        logger.info("\n🎉 Database status check complete!")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database_status()

