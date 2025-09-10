#!/usr/bin/env python3
"""
Debug NOAA API response to understand data structure
"""

import asyncio
import logging
from app.config import settings
from noaa_cdo_api import NOAAClient, Extent
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_noaa_api_response():
    """Debug what the NOAA API actually returns"""
    
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        logger.error("❌ No NOAA CDO token found")
        return
    
    try:
        client = NOAAClient(token=token)
        logger.info("✅ NOAA CDO API client initialized")
        
        # Get a sample station
        logger.info("🔍 Getting sample station...")
        canada_extent = Extent(41.7, -141.0, 83.1, -52.6)
        stations_response = await client.get_stations(
            extent=canada_extent,
            datasetid='GHCND',
            limit=1
        )
        
        stations = stations_response.get('results', [])
        if not stations:
            logger.error("❌ No stations found")
            return
        
        station = stations[0]
        station_id = station['id']
        logger.info(f"📍 Sample Station: {station_id} - {station['name']}")
        logger.info(f"   Location: ({station['latitude']}, {station['longitude']})")
        logger.info(f"   Elevation: {station.get('elevation')}m")
        
        # Get weather data for this station
        logger.info("🌤️  Getting weather data...")
        data_response = await client.get_data(
            datasetid='GHCND',
            stationid=station_id,
            startdate='2025-08-11',
            enddate='2025-08-15',
            limit=50
        )
        
        data = data_response.get('results', [])
        logger.info(f"📊 Found {len(data)} weather records")
        
        if data:
            logger.info("🔍 Sample weather records:")
            for i, record in enumerate(data[:5]):
                logger.info(f"   Record {i+1}:")
                logger.info(f"      Station: {record.get('station')}")
                logger.info(f"      Date: {record.get('date')}")
                logger.info(f"      Data Type: {record.get('datatype')}")
                logger.info(f"      Value: {record.get('value')}")
                logger.info(f"      Attributes: {record.get('attributes')}")
                logger.info(f"      All keys: {list(record.keys())}")
                logger.info("")
            
            # Group by date to see what data types we get
            logger.info("📅 Data types by date:")
            date_groups = {}
            for record in data:
                date = record.get('date', '').split('T')[0]
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append({
                    'datatype': record.get('datatype'),
                    'value': record.get('value')
                })
            
            for date, records in list(date_groups.items())[:3]:
                logger.info(f"   {date}:")
                for record in records:
                    logger.info(f"      {record['datatype']}: {record['value']}")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_noaa_api_response())

