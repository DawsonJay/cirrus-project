#!/usr/bin/env python3
"""
Analyze weather station coverage in Canada to identify gaps and ensure comprehensive discovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
import os
from noaa_cdo_api import NOAAClient, Extent
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StationCoverageAnalyzer:
    """Analyze weather station coverage across Canada"""
    
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
        
        # Major Canadian cities for coverage analysis
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
    
    async def get_all_canada_stations(self, max_limit: int = 10000) -> List[Dict]:
        """Get ALL weather stations in Canada using pagination"""
        if not self.noaa_client:
            return []
        
        all_stations = []
        offset = 0
        limit = 1000  # NOAA API limit per request
        
        try:
            logger.info(f"🔍 Discovering ALL weather stations in Canada (max: {max_limit})...")
            
            while len(all_stations) < max_limit:
                logger.info(f"   Fetching batch {offset//limit + 1} (offset: {offset})...")
                
                stations_response = await self.noaa_client.get_stations(
                    extent=self.canada_extent,
                    datasetid='GHCND',
                    limit=limit,
                    offset=offset
                )
                
                batch_stations = stations_response.get('results', [])
                if not batch_stations:
                    logger.info("   No more stations found - reached end of data")
                    break
                
                all_stations.extend(batch_stations)
                logger.info(f"   Found {len(batch_stations)} stations in this batch (total: {len(all_stations)})")
                
                # If we got fewer than the limit, we've reached the end
                if len(batch_stations) < limit:
                    logger.info("   Reached end of available stations")
                    break
                
                offset += limit
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            logger.info(f"✅ Total stations discovered: {len(all_stations)}")
            return all_stations
            
        except Exception as e:
            logger.error(f"❌ Error getting all Canada stations: {e}")
            return all_stations  # Return what we have so far
    
    def analyze_station_coverage(self, stations: List[Dict]) -> Dict:
        """Analyze the coverage of discovered stations"""
        if not stations:
            return {}
        
        logger.info("📊 Analyzing station coverage...")
        
        # Basic statistics
        total_stations = len(stations)
        
        # Geographic distribution
        latitudes = [s.get('latitude', 0) for s in stations if s.get('latitude')]
        longitudes = [s.get('longitude', 0) for s in stations if s.get('longitude')]
        
        lat_range = (min(latitudes), max(latitudes)) if latitudes else (0, 0)
        lon_range = (min(longitudes), max(longitudes)) if longitudes else (0, 0)
        
        # Temporal analysis
        maxdates = [s.get('maxdate', '') for s in stations if s.get('maxdate')]
        mindates = [s.get('mindate', '') for s in stations if s.get('mindate')]
        
        # Filter by recency
        recent_cutoffs = {
            '1_year': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            '2_years': (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d'),
            '5_years': (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d'),
            '10_years': (datetime.now() - timedelta(days=10*365)).strftime('%Y-%m-%d')
        }
        
        recent_counts = {}
        for period, cutoff in recent_cutoffs.items():
            count = len([s for s in stations if s.get('maxdate', '') > cutoff])
            recent_counts[period] = count
        
        # Data coverage analysis
        datacoverages = [s.get('datacoverage', 0) for s in stations if s.get('datacoverage') is not None]
        avg_coverage = sum(datacoverages) / len(datacoverages) if datacoverages else 0
        
        # High coverage stations
        high_coverage_stations = [s for s in stations if s.get('datacoverage', 0) > 0.8]
        
        # Geographic gaps analysis
        city_coverage = {}
        for city, (city_lat, city_lon) in self.major_cities.items():
            # Find stations within 100km of each major city
            nearby_stations = []
            for station in stations:
                station_lat = station.get('latitude', 0)
                station_lon = station.get('longitude', 0)
                if station_lat and station_lon:
                    # Simple distance calculation (approximate)
                    lat_diff = abs(station_lat - city_lat)
                    lon_diff = abs(station_lon - city_lon)
                    distance_approx = ((lat_diff ** 2) + (lon_diff ** 2)) ** 0.5 * 111  # Rough km
                    
                    if distance_approx < 100:  # Within 100km
                        nearby_stations.append(station)
            
            city_coverage[city] = {
                'nearby_stations': len(nearby_stations),
                'stations': nearby_stations[:3]  # Top 3 closest
            }
        
        return {
            'total_stations': total_stations,
            'geographic_range': {
                'latitude': lat_range,
                'longitude': lon_range
            },
            'temporal_coverage': {
                'earliest_date': min(mindates) if mindates else None,
                'latest_date': max(maxdates) if maxdates else None,
                'recent_stations': recent_counts
            },
            'data_quality': {
                'average_coverage': avg_coverage,
                'high_coverage_stations': len(high_coverage_stations),
                'high_coverage_list': high_coverage_stations[:10]  # Top 10
            },
            'city_coverage': city_coverage
        }
    
    def identify_coverage_gaps(self, analysis: Dict) -> List[str]:
        """Identify potential coverage gaps"""
        gaps = []
        
        # Check major cities without nearby stations
        for city, coverage in analysis.get('city_coverage', {}).items():
            if coverage['nearby_stations'] == 0:
                gaps.append(f"No stations within 100km of {city}")
            elif coverage['nearby_stations'] < 2:
                gaps.append(f"Only {coverage['nearby_stations']} station(s) near {city}")
        
        # Check for recent data gaps
        recent_1yr = analysis.get('temporal_coverage', {}).get('recent_stations', {}).get('1_year', 0)
        total = analysis.get('total_stations', 0)
        
        if recent_1yr < total * 0.5:
            gaps.append(f"Only {recent_1yr}/{total} stations have data from last year")
        
        # Check geographic coverage
        lat_range = analysis.get('geographic_range', {}).get('latitude', (0, 0))
        if lat_range[1] < 80:  # Not reaching far north
            gaps.append("Limited coverage in far northern regions")
        
        return gaps
    
    async def comprehensive_station_discovery(self) -> Dict:
        """Perform comprehensive station discovery and analysis"""
        logger.info("🇨🇦 Starting comprehensive Canada weather station discovery...")
        
        # Get all stations
        all_stations = await self.get_all_canada_stations(max_limit=5000)
        
        if not all_stations:
            logger.error("❌ No stations found")
            return {}
        
        # Analyze coverage
        analysis = self.analyze_station_coverage(all_stations)
        
        # Identify gaps
        gaps = self.identify_coverage_gaps(analysis)
        
        # Print comprehensive report
        self.print_coverage_report(analysis, gaps)
        
        return {
            'stations': all_stations,
            'analysis': analysis,
            'gaps': gaps
        }
    
    def print_coverage_report(self, analysis: Dict, gaps: List[str]):
        """Print a comprehensive coverage report"""
        print("\n" + "="*80)
        print("🇨🇦 CANADA WEATHER STATION COVERAGE ANALYSIS")
        print("="*80)
        
        # Basic stats
        total = analysis.get('total_stations', 0)
        print(f"\n📊 BASIC STATISTICS:")
        print(f"   Total stations discovered: {total}")
        
        # Geographic coverage
        lat_range = analysis.get('geographic_range', {}).get('latitude', (0, 0))
        lon_range = analysis.get('geographic_range', {}).get('longitude', (0, 0))
        print(f"\n🗺️  GEOGRAPHIC COVERAGE:")
        print(f"   Latitude range: {lat_range[0]:.2f}°N to {lat_range[1]:.2f}°N")
        print(f"   Longitude range: {lon_range[0]:.2f}°W to {lon_range[1]:.2f}°W")
        
        # Temporal coverage
        temporal = analysis.get('temporal_coverage', {})
        print(f"\n📅 TEMPORAL COVERAGE:")
        print(f"   Earliest data: {temporal.get('earliest_date', 'Unknown')}")
        print(f"   Latest data: {temporal.get('latest_date', 'Unknown')}")
        
        recent = temporal.get('recent_stations', {})
        print(f"   Recent stations:")
        for period, count in recent.items():
            percentage = (count / total * 100) if total > 0 else 0
            print(f"     {period.replace('_', ' ')}: {count} ({percentage:.1f}%)")
        
        # Data quality
        quality = analysis.get('data_quality', {})
        print(f"\n📈 DATA QUALITY:")
        print(f"   Average data coverage: {quality.get('average_coverage', 0):.3f}")
        print(f"   High coverage stations (>80%): {quality.get('high_coverage_stations', 0)}")
        
        # City coverage
        print(f"\n🏙️  MAJOR CITY COVERAGE:")
        city_coverage = analysis.get('city_coverage', {})
        for city, coverage in city_coverage.items():
            count = coverage['nearby_stations']
            status = "✅" if count >= 2 else "⚠️" if count == 1 else "❌"
            print(f"   {status} {city}: {count} stations within 100km")
        
        # Coverage gaps
        if gaps:
            print(f"\n⚠️  COVERAGE GAPS IDENTIFIED:")
            for gap in gaps:
                print(f"   • {gap}")
        else:
            print(f"\n✅ NO MAJOR COVERAGE GAPS IDENTIFIED")
        
        print("\n" + "="*80)

async def main():
    """Main function to run comprehensive station discovery"""
    analyzer = StationCoverageAnalyzer()
    result = await analyzer.comprehensive_station_discovery()
    
    if result:
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"   1. Use all {result['analysis']['total_stations']} discovered stations for comprehensive coverage")
        print(f"   2. Prioritize stations with recent data (last 1-2 years)")
        print(f"   3. Focus on high data coverage stations for reliable data")
        print(f"   4. Consider multiple data sources for gap areas")

if __name__ == "__main__":
    asyncio.run(main())

