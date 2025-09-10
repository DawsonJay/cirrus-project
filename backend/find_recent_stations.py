#!/usr/bin/env python3
"""
Find stations with recent data (last 2 years)
"""

import asyncio
import logging
from app.config import settings
from noaa_cdo_api import NOAAClient, Extent
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def find_recent_stations():
    """Find stations with recent data"""
    
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        logger.error("❌ No NOAA CDO token found")
        return
    
    try:
        client = NOAAClient(token=token)
        logger.info("✅ NOAA CDO API client initialized")
        
        # Get stations with recent data (last 2 years)
        logger.info("🔍 Finding stations with recent data...")
        canada_extent = Extent(41.7, -141.0, 83.1, -52.6)
        
        # Calculate cutoff date (2 years ago)
        cutoff_date = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
        logger.info(f"📅 Looking for stations with data after {cutoff_date}")
        
        stations_response = await client.get_stations(
            extent=canada_extent,
            datasetid='GHCND',
            limit=100  # Get more stations to find recent ones
        )
        
        stations = stations_response.get('results', [])
        logger.info(f"📊 Found {len(stations)} total stations")
        
        # Filter for stations with recent data
        recent_stations = []
        for station in stations:
            maxdate = station.get('maxdate', '')
            if maxdate and maxdate > cutoff_date:
                recent_stations.append(station)
        
        logger.info(f"🎯 Found {len(recent_stations)} stations with recent data")
        
        # Show the most recent stations
        recent_stations.sort(key=lambda x: x.get('maxdate', ''), reverse=True)
        
        logger.info("📍 Most recent stations:")
        for i, station in enumerate(recent_stations[:10]):
            station_id = station['id']
            name = station['name']
            maxdate = station.get('maxdate', 'Unknown')
            mindate = station.get('mindate', 'Unknown')
            datacoverage = station.get('datacoverage', 0)
            latitude = station.get('latitude')
            longitude = station.get('longitude')
            
            logger.info(f"   {i+1}. {station_id}: {name}")
            logger.info(f"      Location: ({latitude}, {longitude})")
            logger.info(f"      Date range: {mindate} to {maxdate}")
            logger.info(f"      Data coverage: {datacoverage}")
            
            # Test getting actual data from the most recent station
            if i == 0:  # Only test the first one
                logger.info(f"      🔍 Testing data collection...")
                try:
                    # Get data from the last week of available data
                    max_date_obj = datetime.strptime(maxdate, '%Y-%m-%d')
                    start_date = max_date_obj - timedelta(days=7)
                    
                    data_response = await client.get_data(
                        datasetid='GHCND',
                        stationid=station_id,
                        startdate=start_date.strftime('%Y-%m-%d'),
                        enddate=maxdate,
                        limit=50
                    )
                    
                    data = data_response.get('results', [])
                    logger.info(f"      📊 Found {len(data)} records")
                    
                    if data:
                        # Show what data types are available
                        data_types = set()
                        for record in data:
                            data_types.add(record.get('datatype'))
                        
                        logger.info(f"      📋 Available data types: {sorted(data_types)}")
                        
                        # Show sample data with actual values
                        logger.info("      🌡️  Sample data:")
                        for record in data[:5]:
                            datatype = record.get('datatype')
                            value = record.get('value')
                            date = record.get('date', '').split('T')[0]
                            
                            # Convert temperature from tenths of degrees C
                            if datatype in ['TMAX', 'TMIN', 'TAVG']:
                                value = value / 10.0 if value is not None else None
                                unit = "°C"
                            elif datatype in ['PRCP', 'SNOW', 'SNWD']:
                                unit = "mm"
                            else:
                                unit = ""
                            
                            logger.info(f"         {date}: {datatype} = {value}{unit}")
                
                except Exception as e:
                    logger.warning(f"      ⚠️  Error getting data: {e}")
            
            logger.info("")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(find_recent_stations())

