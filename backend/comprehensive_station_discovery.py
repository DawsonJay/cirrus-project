#!/usr/bin/env python3
"""
Comprehensive Weather Station Discovery for Canada
Ensures we get ALL active weather stations using multiple strategies
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
import os
from dotenv import load_dotenv
from noaa_cdo_api import NOAAClient, Extent
from app.config import settings

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveStationDiscovery:
    """Comprehensive weather station discovery with multiple strategies"""
    
    def __init__(self):
        self.noaa_client = None
        token = os.getenv('NOAA_CDO_TOKEN')
        if token:
            try:
                self.noaa_client = NOAAClient(token=token)
                logger.info("✅ NOAA CDO API client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize NOAA CDO client: {e}")
        
        # Canada's boundaries
        self.canada_extent = Extent(
            latitude_min=41.7,   # Southern border
            longitude_min=-141.0, # Western border  
            latitude_max=83.1,   # Northern border
            longitude_max=-52.6  # Eastern border
        )
        
        # Regional extents for better coverage
        self.regional_extents = {
            'Western Canada': Extent(41.7, -141.0, 62.0, -95.0),
            'Central Canada': Extent(41.7, -95.0, 62.0, -70.0),
            'Eastern Canada': Extent(41.7, -70.0, 62.0, -52.6),
            'Northern Canada': Extent(62.0, -141.0, 83.1, -52.6)
        }
        
        # Major cities for targeted discovery
        self.major_cities = {
            'Vancouver': (49.2827, -123.1207),
            'Calgary': (51.0447, -114.0719),
            'Edmonton': (53.5461, -113.4938),
            'Winnipeg': (49.8951, -97.1384),
            'Toronto': (43.6532, -79.3832),
            'Ottawa': (45.4215, -75.6972),
            'Montreal': (45.5017, -73.5673),
            'Quebec City': (46.8139, -71.2080),
            'Halifax': (44.6488, -63.5752),
            'St. John\'s': (47.5615, -52.7126),
            'Whitehorse': (60.7212, -135.0568),
            'Yellowknife': (62.4540, -114.3718),
            'Iqaluit': (63.7467, -68.5170)
        }
    
    async def discover_stations_strategy_1_regional(self) -> List[Dict]:
        """Strategy 1: Regional discovery with relaxed recency filters"""
        logger.info("🔍 Strategy 1: Regional discovery with relaxed filters...")
        
        all_stations = []
        
        for region_name, extent in self.regional_extents.items():
            logger.info(f"   Discovering stations in {region_name}...")
            
            try:
                # Get stations with relaxed recency (last 10 years instead of 2)
                stations_response = await self.noaa_client.get_stations(
                    extent=extent,
                    datasetid='GHCND',
                    limit=1000
                )
                
                stations = stations_response.get('results', [])
                logger.info(f"     Found {len(stations)} stations in {region_name}")
                
                # Filter for stations with data in last 10 years (more inclusive)
                recent_cutoff = (datetime.now() - timedelta(days=10*365)).strftime('%Y-%m-%d')
                recent_stations = [
                    station for station in stations 
                    if station.get('maxdate', '') > recent_cutoff
                ]
                
                logger.info(f"     {len(recent_stations)} stations have data from last 10 years")
                all_stations.extend(recent_stations)
                
            except Exception as e:
                logger.warning(f"     Error in {region_name}: {e}")
            
            # Rate limiting
            await asyncio.sleep(1)
        
        return all_stations
    
    async def discover_stations_strategy_2_city_focused(self) -> List[Dict]:
        """Strategy 2: City-focused discovery with broader radius"""
        logger.info("🔍 Strategy 2: City-focused discovery...")
        
        all_stations = []
        
        for city_name, (lat, lon) in self.major_cities.items():
            logger.info(f"   Searching near {city_name}...")
            
            try:
                # Create a 3-degree radius around each city (broader search)
                city_extent = Extent(
                    latitude_min=lat - 1.5,
                    latitude_max=lat + 1.5,
                    longitude_min=lon - 1.5,
                    longitude_max=lon + 1.5
                )
                
                stations_response = await self.noaa_client.get_stations(
                    extent=city_extent,
                    datasetid='GHCND',
                    limit=200
                )
                
                stations = stations_response.get('results', [])
                logger.info(f"     Found {len(stations)} stations near {city_name}")
                
                # Filter for stations with data in last 5 years
                recent_cutoff = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
                recent_stations = [
                    station for station in stations 
                    if station.get('maxdate', '') > recent_cutoff
                ]
                
                logger.info(f"     {len(recent_stations)} stations have recent data")
                all_stations.extend(recent_stations)
                
            except Exception as e:
                logger.warning(f"     Error near {city_name}: {e}")
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        return all_stations
    
    async def discover_stations_strategy_3_historical_active(self) -> List[Dict]:
        """Strategy 3: Find historically active stations that might still be active"""
        logger.info("🔍 Strategy 3: Historical stations with high data coverage...")
        
        all_stations = []
        
        try:
            # Get stations with high data coverage (likely to be well-maintained)
            stations_response = await self.noaa_client.get_stations(
                extent=self.canada_extent,
                datasetid='GHCND',
                limit=1000
            )
            
            stations = stations_response.get('results', [])
            logger.info(f"   Found {len(stations)} stations")
            
            # Filter for stations with high data coverage (>80%) and recent-ish data (last 15 years)
            recent_cutoff = (datetime.now() - timedelta(days=15*365)).strftime('%Y-%m-%d')
            high_quality_stations = [
                station for station in stations 
                if (station.get('datacoverage', 0) > 0.8 and 
                    station.get('maxdate', '') > recent_cutoff)
            ]
            
            logger.info(f"   {len(high_quality_stations)} stations have high coverage and recent-ish data")
            all_stations.extend(high_quality_stations)
            
        except Exception as e:
            logger.warning(f"   Error in historical discovery: {e}")
        
        return all_stations
    
    async def discover_stations_strategy_4_paginated(self) -> List[Dict]:
        """Strategy 4: Paginated discovery to get ALL stations"""
        logger.info("🔍 Strategy 4: Paginated discovery for complete coverage...")
        
        all_stations = []
        offset = 0
        limit = 1000
        max_attempts = 10  # Limit to avoid infinite loops
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"   Fetching batch {attempt + 1} (offset: {offset})...")
                
                stations_response = await self.noaa_client.get_stations(
                    extent=self.canada_extent,
                    datasetid='GHCND',
                    limit=limit,
                    offset=offset
                )
                
                batch_stations = stations_response.get('results', [])
                if not batch_stations:
                    logger.info("   No more stations found - reached end")
                    break
                
                logger.info(f"   Found {len(batch_stations)} stations in this batch")
                all_stations.extend(batch_stations)
                
                # If we got fewer than the limit, we've reached the end
                if len(batch_stations) < limit:
                    logger.info("   Reached end of available stations")
                    break
                
                offset += limit
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.warning(f"   Error in batch {attempt + 1}: {e}")
                break
        
        logger.info(f"   Total stations from pagination: {len(all_stations)}")
        return all_stations
    
    def deduplicate_stations(self, station_lists: List[List[Dict]]) -> List[Dict]:
        """Remove duplicate stations from multiple discovery strategies"""
        logger.info("🔄 Deduplicating stations from multiple strategies...")
        
        seen_station_ids = set()
        unique_stations = []
        
        for station_list in station_lists:
            for station in station_list:
                station_id = station.get('id')
                if station_id and station_id not in seen_station_ids:
                    seen_station_ids.add(station_id)
                    unique_stations.append(station)
        
        logger.info(f"✅ Found {len(unique_stations)} unique stations")
        return unique_stations
    
    def categorize_stations_by_recency(self, stations: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize stations by data recency"""
        logger.info("📊 Categorizing stations by data recency...")
        
        categories = {
            'very_recent': [],  # Last 1 year
            'recent': [],       # Last 2 years
            'moderate': [],     # Last 5 years
            'historical': []    # Last 15 years
        }
        
        cutoffs = {
            'very_recent': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            'recent': (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d'),
            'moderate': (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d'),
            'historical': (datetime.now() - timedelta(days=15*365)).strftime('%Y-%m-%d')
        }
        
        for station in stations:
            maxdate = station.get('maxdate', '')
            if maxdate > cutoffs['very_recent']:
                categories['very_recent'].append(station)
            elif maxdate > cutoffs['recent']:
                categories['recent'].append(station)
            elif maxdate > cutoffs['moderate']:
                categories['moderate'].append(station)
            elif maxdate > cutoffs['historical']:
                categories['historical'].append(station)
        
        # Log results
        for category, stations_list in categories.items():
            logger.info(f"   {category}: {len(stations_list)} stations")
        
        return categories
    
    async def comprehensive_discovery(self) -> Dict:
        """Run all discovery strategies and combine results"""
        logger.info("🇨🇦 Starting comprehensive weather station discovery...")
        
        # Run all strategies in parallel
        strategies = [
            self.discover_stations_strategy_1_regional(),
            self.discover_stations_strategy_2_city_focused(),
            self.discover_stations_strategy_3_historical_active(),
            self.discover_stations_strategy_4_paginated()
        ]
        
        results = await asyncio.gather(*strategies, return_exceptions=True)
        
        # Process results
        station_lists = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Strategy {i+1} failed: {result}")
            else:
                station_lists.append(result)
        
        # Deduplicate and categorize
        unique_stations = self.deduplicate_stations(station_lists)
        categorized = self.categorize_stations_by_recency(unique_stations)
        
        # Create comprehensive report
        report = {
            'total_stations': len(unique_stations),
            'categorized_stations': categorized,
            'all_stations': unique_stations,
            'discovery_strategies': len([r for r in results if not isinstance(r, Exception)])
        }
        
        self.print_discovery_report(report)
        
        return report
    
    def print_discovery_report(self, report: Dict):
        """Print comprehensive discovery report"""
        print("\n" + "="*80)
        print("🇨🇦 COMPREHENSIVE WEATHER STATION DISCOVERY REPORT")
        print("="*80)
        
        total = report['total_stations']
        print(f"\n📊 DISCOVERY SUMMARY:")
        print(f"   Total unique stations discovered: {total}")
        print(f"   Successful discovery strategies: {report['discovery_strategies']}/4")
        
        categorized = report['categorized_stations']
        print(f"\n📅 STATIONS BY DATA RECENCY:")
        print(f"   Very recent (last year): {len(categorized['very_recent'])}")
        print(f"   Recent (last 2 years): {len(categorized['recent'])}")
        print(f"   Moderate (last 5 years): {len(categorized['moderate'])}")
        print(f"   Historical (last 15 years): {len(categorized['historical'])}")
        
        # Show sample stations from each category
        for category, stations in categorized.items():
            if stations:
                print(f"\n📍 Sample {category} stations:")
                for i, station in enumerate(stations[:3]):
                    name = station.get('name', 'Unknown')
                    lat = station.get('latitude', 0)
                    lon = station.get('longitude', 0)
                    maxdate = station.get('maxdate', 'Unknown')
                    coverage = station.get('datacoverage', 0)
                    print(f"   {i+1}. {name} at ({lat}, {lon}) - Latest: {maxdate}, Coverage: {coverage:.3f}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"   1. Use {len(categorized['very_recent']) + len(categorized['recent'])} stations for current data")
        print(f"   2. Include {len(categorized['moderate'])} moderate stations for better coverage")
        print(f"   3. Consider {len(categorized['historical'])} historical stations for AI training")
        print(f"   4. Total recommended stations: {len(categorized['very_recent']) + len(categorized['recent']) + len(categorized['moderate'])}")
        
        print("\n" + "="*80)

async def main():
    """Main function to run comprehensive station discovery"""
    discovery = ComprehensiveStationDiscovery()
    result = await discovery.comprehensive_discovery()
    
    if result:
        # Save results for use in data collection
        recommended_stations = (
            result['categorized_stations']['very_recent'] +
            result['categorized_stations']['recent'] +
            result['categorized_stations']['moderate']
        )
        
        print(f"\n💾 RECOMMENDED STATIONS FOR DATA COLLECTION:")
        print(f"   Total recommended: {len(recommended_stations)}")
        print(f"   These stations provide the best balance of coverage and data recency")

if __name__ == "__main__":
    asyncio.run(main())

