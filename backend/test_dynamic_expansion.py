#!/usr/bin/env python3
"""
Test the dynamic schema expansion with a station that has comprehensive data
"""

import asyncio
import logging
from app.config import settings
from noaa_cdo_api import NOAAClient, Extent
import os
from datetime import datetime, timedelta
from dynamic_schema_manager import DynamicSchemaManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_dynamic_expansion():
    """Test dynamic schema expansion with comprehensive data"""
    
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        logger.error("❌ No NOAA CDO token found")
        return
    
    try:
        client = NOAAClient(token=token)
        logger.info("✅ NOAA CDO API client initialized")
        
        # Get a station with comprehensive data
        logger.info("🔍 Finding station with comprehensive data...")
        canada_extent = Extent(41.7, -141.0, 83.1, -52.6)
        
        stations_response = await client.get_stations(
            extent=canada_extent,
            datasetid='GHCND',
            limit=50
        )
        
        stations = stations_response.get('results', [])
        recent_cutoff = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
        recent_stations = [s for s in stations if s.get('maxdate', '') > recent_cutoff]
        
        # Sort by data coverage (highest first)
        recent_stations.sort(key=lambda x: x.get('datacoverage', 0), reverse=True)
        
        if not recent_stations:
            logger.error("❌ No recent stations found")
            return
        
        # Use the station with highest data coverage
        station = recent_stations[0]
        station_id = station['id']
        station_name = station['name']
        maxdate = station.get('maxdate')
        datacoverage = station.get('datacoverage', 0)
        
        logger.info(f"📍 Using station: {station_id} - {station_name}")
        logger.info(f"   Latest data: {maxdate}")
        logger.info(f"   Data coverage: {datacoverage}")
        
        # Get data from the last week of available data
        max_date_obj = datetime.strptime(maxdate, '%Y-%m-%d')
        start_date = max_date_obj - timedelta(days=7)
        
        logger.info(f"🔍 Getting data from {start_date.strftime('%Y-%m-%d')} to {maxdate}")
        
        data_response = await client.get_data(
            datasetid='GHCND',
            stationid=station_id,
            startdate=start_date.strftime('%Y-%m-%d'),
            enddate=maxdate,
            limit=200
        )
        
        data = data_response.get('results', [])
        logger.info(f"📊 Found {len(data)} raw records")
        
        if data:
            # Analyze all data types found
            data_types = set()
            for record in data:
                datatype = record.get('datatype')
                if datatype:
                    data_types.add(datatype)
            
            logger.info(f"📋 Found {len(data_types)} different data types: {sorted(data_types)}")
            
            # Test dynamic schema expansion
            logger.info("🔧 Testing dynamic schema expansion...")
            schema_manager = DynamicSchemaManager()
            
            # Check what columns exist before
            schema_before = schema_manager.get_current_schema()
            logger.info(f"📊 Schema before: {len(schema_before)} columns")
            
            # Ensure columns exist for all data types
            added_columns = schema_manager.ensure_columns_for_data_types(data_types)
            
            if added_columns:
                logger.info(f"✅ Added {len(added_columns)} new columns: {added_columns}")
            else:
                logger.info("✅ No new columns needed - all data types already supported")
            
            # Check what columns exist after
            schema_after = schema_manager.get_current_schema()
            logger.info(f"📊 Schema after: {len(schema_after)} columns")
            
            # Show data usage analysis
            usage = schema_manager.analyze_data_types_in_database()
            logger.info("📈 Data usage analysis:")
            for column, count in usage.items():
                if count > 0:
                    logger.info(f"   {column}: {count} records")
            
            # Test with a new data type that doesn't exist yet
            logger.info("🧪 Testing with a hypothetical new data type...")
            test_data_types = {'NEWTYPE', 'ANOTHERTYPE'}
            added_test_columns = schema_manager.ensure_columns_for_data_types(test_data_types)
            
            if added_test_columns:
                logger.info(f"✅ Successfully added columns for new data types: {added_test_columns}")
            else:
                logger.info("✅ New data types already supported")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_dynamic_expansion())

