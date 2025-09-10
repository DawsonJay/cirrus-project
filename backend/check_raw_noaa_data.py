#!/usr/bin/env python3
"""
Check what raw data types NOAA API is actually returning
"""

import asyncio
import logging
from app.config import settings
from noaa_cdo_api import NOAAClient, Extent
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_raw_noaa_data():
    """Check what raw data types NOAA API is actually returning"""
    
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        logger.error("❌ No NOAA CDO token found")
        return
    
    try:
        client = NOAAClient(token=token)
        logger.info("✅ NOAA CDO API client initialized")
        
        # Get a station with recent data
        logger.info("🔍 Getting station with recent data...")
        canada_extent = Extent(41.7, -141.0, 83.1, -52.6)
        
        # Get stations with recent data
        stations_response = await client.get_stations(
            extent=canada_extent,
            datasetid='GHCND',
            limit=10
        )
        
        stations = stations_response.get('results', [])
        recent_cutoff = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
        recent_stations = [s for s in stations if s.get('maxdate', '') > recent_cutoff]
        
        if not recent_stations:
            logger.error("❌ No recent stations found")
            return
        
        # Use the most recent station
        station = recent_stations[0]
        station_id = station['id']
        station_name = station['name']
        maxdate = station.get('maxdate')
        
        logger.info(f"📍 Using station: {station_id} - {station_name}")
        logger.info(f"   Latest data: {maxdate}")
        
        # Get data from the last week of available data
        max_date_obj = datetime.strptime(maxdate, '%Y-%m-%d')
        start_date = max_date_obj - timedelta(days=7)
        
        logger.info(f"🔍 Getting data from {start_date.strftime('%Y-%m-%d')} to {maxdate}")
        
        data_response = await client.get_data(
            datasetid='GHCND',
            stationid=station_id,
            startdate=start_date.strftime('%Y-%m-%d'),
            enddate=maxdate,
            limit=100  # Get more records to see all data types
        )
        
        data = data_response.get('results', [])
        logger.info(f"📊 Found {len(data)} raw records")
        
        if data:
            # Analyze all data types found
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
            
            logger.info(f"📋 Found {len(data_types)} different data types:")
            logger.info("")
            
            # Show each data type with sample values
            for datatype in sorted(data_types.keys()):
                records = data_types[datatype]
                logger.info(f"🌡️  {datatype}: {len(records)} records")
                
                # Show sample values
                for i, record in enumerate(records[:3]):
                    value = record['value']
                    date = record['date']
                    attrs = record['attributes']
                    
                    # Convert temperature values
                    if datatype in ['TMAX', 'TMIN', 'TAVG'] and value is not None:
                        converted_value = value / 10.0
                        logger.info(f"   {date}: {value} (raw) = {converted_value}°C {attrs}")
                    else:
                        logger.info(f"   {date}: {value} {attrs}")
                
                if len(records) > 3:
                    logger.info(f"   ... and {len(records) - 3} more records")
                logger.info("")
            
            # Check what we're currently storing vs what's available
            logger.info("🔍 Data Type Coverage Analysis:")
            logger.info("")
            
            # Data types we're currently collecting
            our_data_types = {
                'TMAX': 'temperature_max',
                'TMIN': 'temperature_min', 
                'TAVG': 'temperature_avg',
                'PRCP': 'precipitation',
                'SNWD': 'snow_depth',
                'AWND': 'wind_speed_avg',
                'WSF2': 'wind_speed_max',
                'WDF2': 'wind_direction',
                'PSUN': 'sunshine_percent',
                'TSUN': 'sunshine_minutes'
            }
            
            # Check what we're missing
            available_types = set(data_types.keys())
            our_types = set(our_data_types.keys())
            
            logger.info("✅ Data types we're collecting:")
            for dt in sorted(our_types & available_types):
                logger.info(f"   {dt} -> {our_data_types[dt]}")
            
            logger.info("")
            logger.info("❌ Data types we're NOT collecting:")
            missing_types = available_types - our_types
            for dt in sorted(missing_types):
                logger.info(f"   {dt} (available but not stored)")
            
            logger.info("")
            logger.info("⚠️  Data types we're collecting but not available:")
            unavailable_types = our_types - available_types
            for dt in sorted(unavailable_types):
                logger.info(f"   {dt} -> {our_data_types[dt]} (not available for this station)")
            
            # Check for weather types (WT codes)
            weather_types = [dt for dt in available_types if dt.startswith('WT')]
            if weather_types:
                logger.info("")
                logger.info("🌤️  Weather Types (WT codes) found:")
                for wt in sorted(weather_types):
                    logger.info(f"   {wt}")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_raw_noaa_data())

