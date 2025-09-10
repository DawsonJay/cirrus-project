#!/usr/bin/env python3
"""
Investigate why we're missing weather stations in eastern Canadian cities
"""

import asyncio
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from noaa_cdo_api import NOAAClient, Extent

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def investigate_eastern_coverage():
    """Investigate weather station coverage in eastern Canada"""
    
    token = os.getenv('NOAA_CDO_TOKEN')
    if not token:
        logger.error("❌ No NOAA CDO token found")
        return
    
    try:
        client = NOAAClient(token=token)
        logger.info("✅ NOAA CDO API client initialized")
        
        # Test different geographic extents
        test_extents = {
            'Full Canada': Extent(41.7, -141.0, 83.1, -52.6),
            'Eastern Canada': Extent(41.7, -95.0, 83.1, -52.6),  # East of -95°W
            'Ontario/Quebec': Extent(41.7, -95.0, 62.0, -52.6),  # Focus on ON/QC
            'Maritime Provinces': Extent(43.0, -70.0, 52.0, -52.6),  # Atlantic Canada
            'Toronto Area': Extent(43.0, -80.0, 44.0, -79.0),  # Toronto region
            'Montreal Area': Extent(45.0, -74.0, 46.0, -73.0),  # Montreal region
        }
        
        for name, extent in test_extents.items():
            logger.info(f"\n🔍 Testing {name} extent...")
            logger.info(f"   Bounds: {extent.latitude_min}°N to {extent.latitude_max}°N, {extent.longitude_min}°W to {extent.longitude_max}°W")
            
            try:
                stations_response = await client.get_stations(
                    extent=extent,
                    datasetid='GHCND',
                    limit=100
                )
                
                stations = stations_response.get('results', [])
                logger.info(f"   Found {len(stations)} stations")
                
                if stations:
                    # Show sample stations
                    for i, station in enumerate(stations[:3]):
                        name = station.get('name', 'Unknown')
                        lat = station.get('latitude', 0)
                        lon = station.get('longitude', 0)
                        maxdate = station.get('maxdate', 'Unknown')
                        coverage = station.get('datacoverage', 0)
                        logger.info(f"     {i+1}. {name} at ({lat}, {lon}) - Latest: {maxdate}, Coverage: {coverage:.3f}")
                
                # Check for recent data
                recent_cutoff = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                recent_stations = [s for s in stations if s.get('maxdate', '') > recent_cutoff]
                logger.info(f"   Recent stations (last year): {len(recent_stations)}")
                
            except Exception as e:
                logger.error(f"   Error: {e}")
            
            # Rate limiting
            await asyncio.sleep(1)
        
        # Test specific major cities with broader search
        major_cities = {
            'Toronto': (43.6532, -79.3832),
            'Montreal': (45.5017, -73.5673),
            'Ottawa': (45.4215, -75.6972),
            'Quebec City': (46.8139, -71.2080),
            'Halifax': (44.6488, -63.5752),
            'St. John\'s': (47.5615, -52.7126)
        }
        
        logger.info(f"\n🏙️  Testing major cities with broader search...")
        
        for city, (lat, lon) in major_cities.items():
            logger.info(f"\n📍 {city} ({lat}, {lon}):")
            
            # Create a 2-degree radius around the city
            city_extent = Extent(
                latitude_min=lat - 1.0,
                latitude_max=lat + 1.0,
                longitude_min=lon - 1.0,
                longitude_max=lon + 1.0
            )
            
            try:
                stations_response = await client.get_stations(
                    extent=city_extent,
                    datasetid='GHCND',
                    limit=50
                )
                
                stations = stations_response.get('results', [])
                logger.info(f"   Found {len(stations)} stations within 2° radius")
                
                if stations:
                    # Show closest stations
                    for i, station in enumerate(stations[:3]):
                        name = station.get('name', 'Unknown')
                        station_lat = station.get('latitude', 0)
                        station_lon = station.get('longitude', 0)
                        maxdate = station.get('maxdate', 'Unknown')
                        
                        # Calculate approximate distance
                        lat_diff = abs(station_lat - lat)
                        lon_diff = abs(station_lon - lon)
                        distance_approx = ((lat_diff ** 2) + (lon_diff ** 2)) ** 0.5 * 111  # Rough km
                        
                        logger.info(f"     {i+1}. {name} at ({station_lat}, {station_lon}) - ~{distance_approx:.0f}km, Latest: {maxdate}")
                else:
                    logger.warning(f"   ⚠️  No stations found near {city}")
                
            except Exception as e:
                logger.error(f"   Error searching near {city}: {e}")
            
            await asyncio.sleep(0.5)
        
        # Test different datasets
        logger.info(f"\n📊 Testing different NOAA datasets...")
        
        datasets = ['GHCND', 'GSOM', 'GSOY']
        
        for dataset in datasets:
            logger.info(f"\n🔍 Testing dataset: {dataset}")
            
            try:
                # Test with a small extent around Toronto
                toronto_extent = Extent(43.0, -80.0, 44.0, -79.0)
                
                stations_response = await client.get_stations(
                    extent=toronto_extent,
                    datasetid=dataset,
                    limit=20
                )
                
                stations = stations_response.get('results', [])
                logger.info(f"   Found {len(stations)} stations")
                
                if stations:
                    for station in stations[:2]:
                        name = station.get('name', 'Unknown')
                        lat = station.get('latitude', 0)
                        lon = station.get('longitude', 0)
                        logger.info(f"     {name} at ({lat}, {lon})")
                
            except Exception as e:
                logger.error(f"   Error with dataset {dataset}: {e}")
            
            await asyncio.sleep(0.5)
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(investigate_eastern_coverage())
