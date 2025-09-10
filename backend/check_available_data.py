#!/usr/bin/env python3
"""
Check what data is actually available from NOAA stations
"""

import asyncio
import logging
from app.config import settings
from noaa_cdo_api import NOAAClient, Extent
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_available_data():
    """Check what data is actually available"""
    
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        logger.error("❌ No NOAA CDO token found")
        return
    
    try:
        client = NOAAClient(token=token)
        logger.info("✅ NOAA CDO API client initialized")
        
        # Get stations with recent data
        logger.info("🔍 Getting stations with recent data...")
        canada_extent = Extent(41.7, -141.0, 83.1, -52.6)
        stations_response = await client.get_stations(
            extent=canada_extent,
            datasetid='GHCND',
            limit=5
        )
        
        stations = stations_response.get('results', [])
        logger.info(f"📊 Found {len(stations)} stations")
        
        for station in stations:
            station_id = station['id']
            name = station['name']
            maxdate = station.get('maxdate', 'Unknown')
            mindate = station.get('mindate', 'Unknown')
            datacoverage = station.get('datacoverage', 0)
            
            logger.info(f"📍 {station_id}: {name}")
            logger.info(f"   Date range: {mindate} to {maxdate}")
            logger.info(f"   Data coverage: {datacoverage}")
            
            # Try to get data from the most recent available date
            if maxdate and maxdate != 'Unknown':
                try:
                    # Parse the maxdate and go back a few days
                    max_date_obj = datetime.strptime(maxdate, '%Y-%m-%d')
                    start_date = max_date_obj - timedelta(days=7)
                    
                    logger.info(f"   🔍 Checking data from {start_date.strftime('%Y-%m-%d')} to {maxdate}")
                    
                    data_response = await client.get_data(
                        datasetid='GHCND',
                        stationid=station_id,
                        startdate=start_date.strftime('%Y-%m-%d'),
                        enddate=maxdate,
                        limit=20
                    )
                    
                    data = data_response.get('results', [])
                    logger.info(f"   📊 Found {len(data)} records")
                    
                    if data:
                        # Show what data types are available
                        data_types = set()
                        for record in data:
                            data_types.add(record.get('datatype'))
                        
                        logger.info(f"   📋 Available data types: {sorted(data_types)}")
                        
                        # Show sample data
                        logger.info("   🌡️  Sample data:")
                        for record in data[:3]:
                            logger.info(f"      {record.get('date')}: {record.get('datatype')} = {record.get('value')}")
                    
                except Exception as e:
                    logger.warning(f"   ⚠️  Error getting data: {e}")
            
            logger.info("")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_available_data())

