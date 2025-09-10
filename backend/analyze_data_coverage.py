#!/usr/bin/env python3
"""
Analyze what data types we're collecting and storing from NOAA stations
"""

import sqlite3
import logging
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_data_coverage():
    """Analyze what data types we're collecting and storing"""
    db_path = settings.DATABASE_PATH
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔍 Analyzing Data Coverage from NOAA Stations")
        logger.info("=" * 60)
        
        # Check what data types are actually stored in our database
        logger.info("📊 Data Types Currently Stored in Database:")
        
        # Check each field for non-null values
        fields_to_check = [
            ('temperature_max', 'TMAX'),
            ('temperature_min', 'TMIN'), 
            ('temperature_avg', 'TAVG'),
            ('precipitation', 'PRCP'),
            ('snow_depth', 'SNWD'),
            ('wind_speed_avg', 'AWND'),
            ('wind_speed_max', 'WSF2'),
            ('wind_direction', 'WDF2'),
            ('sunshine_percent', 'PSUN'),
            ('sunshine_minutes', 'TSUN'),
            ('weather_types', 'WT*')
        ]
        
        cursor.execute("SELECT COUNT(*) FROM daily_weather_data")
        total_records = cursor.fetchone()[0]
        
        logger.info(f"📈 Total Records: {total_records}")
        logger.info("")
        
        for field_name, noaa_code in fields_to_check:
            if field_name == 'weather_types':
                cursor.execute(f"SELECT COUNT(*) FROM daily_weather_data WHERE {field_name} IS NOT NULL AND {field_name} != ''")
            else:
                cursor.execute(f"SELECT COUNT(*) FROM daily_weather_data WHERE {field_name} IS NOT NULL")
            
            count = cursor.fetchone()[0]
            percentage = (count / total_records * 100) if total_records > 0 else 0
            
            logger.info(f"   {noaa_code:6} ({field_name:20}): {count:3} records ({percentage:5.1f}%)")
        
        # Check for any other data types that might be in weather_types
        logger.info("\n🌤️  Weather Types Found:")
        cursor.execute("SELECT weather_types FROM daily_weather_data WHERE weather_types IS NOT NULL AND weather_types != ''")
        weather_types = cursor.fetchall()
        
        all_weather_types = set()
        for (wt_string,) in weather_types:
            if wt_string:
                types = wt_string.split(',')
                for wt in types:
                    all_weather_types.add(wt.strip())
        
        if all_weather_types:
            for wt in sorted(all_weather_types):
                logger.info(f"   {wt}")
        else:
            logger.info("   No weather types found")
        
        # Check what data is available per station
        logger.info("\n📍 Data Availability by Station:")
        cursor.execute("""
            SELECT 
                ws.station_id,
                ws.name,
                ws.latitude,
                ws.longitude,
                COUNT(dwd.id) as total_records,
                COUNT(dwd.temperature_max) as tmax_count,
                COUNT(dwd.temperature_min) as tmin_count,
                COUNT(dwd.precipitation) as precip_count,
                COUNT(dwd.snow_depth) as snow_count,
                COUNT(dwd.wind_speed_avg) as wind_count
            FROM weather_stations ws
            LEFT JOIN daily_weather_data dwd ON ws.station_id = dwd.station_id
            GROUP BY ws.station_id, ws.name, ws.latitude, ws.longitude
            ORDER BY total_records DESC
        """)
        
        station_data = cursor.fetchall()
        for station in station_data:
            station_id, name, lat, lon, total, tmax, tmin, precip, snow, wind = station
            logger.info(f"   {station_id}: {name}")
            logger.info(f"      Location: ({lat}, {lon})")
            logger.info(f"      Records: {total} total")
            logger.info(f"      Data: Tmax={tmax}, Tmin={tmin}, Precip={precip}, Snow={snow}, Wind={wind}")
            logger.info("")
        
        # Check for any data types we might be missing
        logger.info("🔍 Checking for Missing Data Types:")
        logger.info("   (This would require checking the raw NOAA API responses)")
        logger.info("   Common NOAA data types we might be missing:")
        logger.info("   - TAVG (Average Temperature)")
        logger.info("   - SNOW (Snowfall)")
        logger.info("   - WSF5 (5-minute wind speed)")
        logger.info("   - WDF5 (5-minute wind direction)")
        logger.info("   - WT01-WT22 (Weather types)")
        logger.info("   - PRCP (Precipitation)")
        logger.info("   - SNWD (Snow depth)")
        logger.info("   - AWND (Average wind speed)")
        logger.info("   - WSF2 (2-minute wind speed)")
        logger.info("   - WDF2 (2-minute wind direction)")
        logger.info("   - PSUN (Percent sunshine)")
        logger.info("   - TSUN (Total sunshine minutes)")
        
        # Check if we're storing all available data types
        logger.info("\n⚠️  Potential Issues:")
        logger.info("   1. We might be missing some data types that NOAA provides")
        logger.info("   2. Some stations might have data types we're not collecting")
        logger.info("   3. We should check the raw API responses to see what's available")
        
        logger.info("\n🎉 Data coverage analysis complete!")
        
    except sqlite3.Error as e:
        logger.error(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    analyze_data_coverage()

