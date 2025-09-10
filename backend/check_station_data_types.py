#!/usr/bin/env python3
"""
Check what data types are available for stations we have in our database
"""

import asyncio
import sqlite3
import logging
from app.config import settings
from noaa_cdo_api import NOAAClient
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_station_data_types():
    """Check what data types are available for stations in our database"""
    
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        logger.error("❌ No NOAA CDO token found")
        return
    
    try:
        client = NOAAClient(token=token)
        logger.info("✅ NOAA CDO API client initialized")
        
        # Get stations from our database
        db_path = settings.DATABASE_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT station_id, name FROM weather_stations LIMIT 3")
        stations = cursor.fetchall()
        conn.close()
        
        if not stations:
            logger.error("❌ No stations in database")
            return
        
        logger.info(f"🔍 Checking data types for {len(stations)} stations from our database")
        logger.info("")
        
        for station_id, station_name in stations:
            logger.info(f"📍 Station: {station_id} - {station_name}")
            
            try:
                # Get data from the last month
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                logger.info(f"   🔍 Getting data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                
                data_response = await client.get_data(
                    datasetid='GHCND',
                    stationid=station_id,
                    startdate=start_date.strftime('%Y-%m-%d'),
                    enddate=end_date.strftime('%Y-%m-%d'),
                    limit=100
                )
                
                data = data_response.get('results', [])
                logger.info(f"   📊 Found {len(data)} raw records")
                
                if data:
                    # Analyze data types
                    data_types = {}
                    for record in data:
                        datatype = record.get('datatype')
                        value = record.get('value')
                        date = record.get('date', '').split('T')[0]
                        
                        if datatype not in data_types:
                            data_types[datatype] = []
                        
                        data_types[datatype].append({
                            'date': date,
                            'value': value,
                            'attributes': record.get('attributes', '')
                        })
                    
                    logger.info(f"   📋 Found {len(data_types)} different data types:")
                    
                    # Show each data type
                    for datatype in sorted(data_types.keys()):
                        records = data_types[datatype]
                        logger.info(f"      {datatype}: {len(records)} records")
                        
                        # Show sample values
                        for i, record in enumerate(records[:2]):
                            value = record['value']
                            date = record['date']
                            attrs = record['attributes']
                            
                            # Convert temperature values
                            if datatype in ['TMAX', 'TMIN', 'TAVG'] and value is not None:
                                converted_value = value / 10.0
                                logger.info(f"         {date}: {value} (raw) = {converted_value}°C {attrs}")
                            else:
                                logger.info(f"         {date}: {value} {attrs}")
                        
                        if len(records) > 2:
                            logger.info(f"         ... and {len(records) - 2} more records")
                    
                    # Check what we're missing
                    available_types = set(data_types.keys())
                    our_types = {'TMAX', 'TMIN', 'TAVG', 'PRCP', 'SNWD', 'AWND', 'WSF2', 'WDF2', 'PSUN', 'TSUN'}
                    
                    missing_types = available_types - our_types
                    if missing_types:
                        logger.info(f"   ❌ Missing data types: {sorted(missing_types)}")
                    
                    # Check for weather types
                    weather_types = [dt for dt in available_types if dt.startswith('WT')]
                    if weather_types:
                        logger.info(f"   🌤️  Weather types: {sorted(weather_types)}")
                
                else:
                    logger.info("   ⚠️  No data found for this date range")
                
            except Exception as e:
                logger.warning(f"   ⚠️  Error getting data: {e}")
            
            logger.info("")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_station_data_types())

