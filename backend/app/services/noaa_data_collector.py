"""
NOAA and Environment Canada Data Collector
Free weather data collection without API keys
"""

import asyncio
import aiohttp
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class NOAADataCollector:
    """Collect weather data from free public APIs"""
    
    def __init__(self, batch_size: int = None):
        self.batch_size = batch_size or settings.BATCH_SIZE
        self.session = None
        
        # API endpoints
        self.us_weather_url = "https://api.weather.gov"
        self.ec_weather_url = "https://api.weather.gc.ca"
        
        # NOAA CDO API token (optional)
        self.noaa_token = settings.NOAA_CDO_TOKEN
        
        # Initialize NOAA CDO client if token is available
        self.noaa_client = None
        if self.noaa_token:
            try:
                from noaa_cdo_api import NOAAClient
                self.noaa_client = NOAAClient(token=self.noaa_token)
                logger.info("✅ NOAA CDO API client initialized with token")
            except ImportError:
                logger.warning("⚠️ NOAA CDO API library not available")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize NOAA CDO client: {e}")
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.noaa_client:
            try:
                if hasattr(self.noaa_client, 'close') and callable(self.noaa_client.close):
                    self.noaa_client.close()  # This is synchronous, not async
            except Exception as e:
                logger.warning(f"Error closing NOAA client: {e}")
    
    async def get_us_weather_stations(self, lat: float, lon: float, radius_km: float = 50) -> List[Dict]:
        """Get US weather stations near a location"""
        try:
            # Get stations from US Weather Service
            url = f"{self.us_weather_url}/stations"
            params = {
                "limit": 50,
                "state": "CA"  # Focus on California for now
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    stations = data.get('features', [])
                    
                    # Filter by distance (simple bounding box for now)
                    filtered_stations = []
                    for station in stations:
                        coords = station.get('geometry', {}).get('coordinates', [])
                        if len(coords) >= 2:
                            station_lon, station_lat = coords[0], coords[1]
                            # Simple distance check (not precise but fast)
                            if abs(station_lat - lat) < 1.0 and abs(station_lon - lon) < 1.0:
                                filtered_stations.append({
                                    'id': station.get('properties', {}).get('stationIdentifier'),
                                    'name': station.get('properties', {}).get('name'),
                                    'latitude': station_lat,
                                    'longitude': station_lon,
                                    'source': 'us_weather'
                                })
                    
                    return filtered_stations
                else:
                    logger.error(f"US Weather API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting US weather stations: {e}")
            return []
    
    async def get_ec_weather_stations(self, lat: float, lon: float) -> List[Dict]:
        """Get Environment Canada weather stations near a location"""
        try:
            # Get stations from Environment Canada
            url = f"{self.ec_weather_url}/collections/climate-daily/items"
            params = {
                "limit": 100,
                "f": "json"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    features = data.get('features', [])
                    
                    # Filter by distance
                    filtered_stations = []
                    for feature in features:
                        coords = feature.get('geometry', {}).get('coordinates', [])
                        if len(coords) >= 2:
                            station_lon, station_lat = coords[0], coords[1]
                            # Simple distance check
                            if abs(station_lat - lat) < 2.0 and abs(station_lon - lon) < 2.0:
                                props = feature.get('properties', {})
                                filtered_stations.append({
                                    'id': props.get('CLIMATE_IDENTIFIER'),
                                    'name': props.get('STATION_NAME'),
                                    'latitude': station_lat,
                                    'longitude': station_lon,
                                    'source': 'environment_canada'
                                })
                    
                    return filtered_stations
                else:
                    logger.error(f"Environment Canada API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting EC weather stations: {e}")
            return []
    
    async def get_current_weather_us(self, station_id: str) -> Optional[Dict]:
        """Get current weather from US Weather Service"""
        try:
            # Get current observations
            url = f"{self.us_weather_url}/stations/{station_id}/observations/current"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    props = data.get('properties', {})
                    
                    return {
                        'temperature': props.get('temperature', {}).get('value'),
                        'humidity': props.get('relativeHumidity', {}).get('value'),
                        'wind_speed': props.get('windSpeed', {}).get('value'),
                        'wind_direction': props.get('windDirection', {}).get('value'),
                        'pressure': props.get('barometricPressure', {}).get('value'),
                        'precipitation': props.get('precipitationLastHour', {}).get('value'),
                        'timestamp': props.get('timestamp'),
                        'source': 'us_weather'
                    }
                else:
                    logger.warning(f"US Weather current data error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting US current weather: {e}")
            return None
    
    async def get_historical_weather_ec(self, station_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get historical weather from Environment Canada"""
        try:
            # Environment Canada historical data
            url = f"{self.ec_weather_url}/collections/climate-daily/items"
            params = {
                "CLIMATE_IDENTIFIER": station_id,
                "PROVINCE_CODE": "BC",  # Focus on BC for now
                "f": "json",
                "limit": 1000
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    features = data.get('features', [])
                    
                    weather_data = []
                    for feature in features:
                        props = feature.get('properties', {})
                        weather_data.append({
                            'date': props.get('LOCAL_DATE'),
                            'temperature_max': props.get('MAX_TEMPERATURE'),
                            'temperature_min': props.get('MIN_TEMPERATURE'),
                            'precipitation': props.get('TOTAL_PRECIPITATION'),
                            'snow': props.get('SNOW_ON_GROUND'),
                            'wind_speed': props.get('WIND_SPEED'),
                            'source': 'environment_canada'
                        })
                    
                    return weather_data
                else:
                    logger.warning(f"EC historical data error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting EC historical weather: {e}")
            return []
    
    async def get_noaa_cdo_data(self, lat: float, lon: float, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get enhanced weather data from NOAA CDO API (requires token)"""
        if not self.noaa_client:
            logger.warning("⚠️ NOAA CDO client not available - no token provided")
            return []
        
        try:
            # First, get available datasets
            datasets_response = await self.noaa_client.get_datasets(limit=5)
            datasets = datasets_response.get('results', [])
            logger.info(f"Found {len(datasets)} NOAA CDO datasets")
            
            # Get stations near the location
            try:
                from noaa_cdo_api import Extent
                extent = Extent(lat - 0.5, lon - 0.5, lat + 0.5, lon + 0.5)
                stations_response = await self.noaa_client.get_stations(
                    extent=extent,
                    datasetid="GHCND",  # Global Historical Climatology Network Daily
                    limit=5
                )
                stations = stations_response.get('results', [])
                logger.info(f"Found {len(stations)} NOAA CDO stations")
                
                # Return station info
                return stations[:3] if stations else []
                
            except Exception as e:
                logger.warning(f"Could not get stations (API might be down): {e}")
                # Return dataset info instead
                return datasets[:3] if datasets else []
            
        except Exception as e:
            logger.error(f"Error getting NOAA CDO data: {e}")
            return []
    
    async def collect_weather_for_location(self, lat: float, lon: float) -> Dict[str, Any]:
        """Collect weather data for a specific location"""
        logger.info(f"🌍 Collecting weather data for {lat}, {lon}")
        
        # Get stations from both sources
        us_stations = await self.get_us_weather_stations(lat, lon)
        ec_stations = await self.get_ec_weather_stations(lat, lon)
        
        logger.info(f"   Found {len(us_stations)} US stations, {len(ec_stations)} EC stations")
        
        # Try to get current weather from US stations
        current_weather = None
        for station in us_stations[:3]:  # Try first 3 stations
            current_weather = await self.get_current_weather_us(station['id'])
            if current_weather:
                break
        
        # Try to get historical weather from EC stations
        historical_weather = []
        for station in ec_stations[:2]:  # Try first 2 stations
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days
            hist_data = await self.get_historical_weather_ec(station['id'], start_date, end_date)
            historical_weather.extend(hist_data)
            if len(historical_weather) > 50:  # Limit to avoid too much data
                break
        
        # Try to get enhanced data from NOAA CDO (if token available)
        noaa_cdo_data = []
        if self.noaa_client:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days
            noaa_cdo_data = await self.get_noaa_cdo_data(lat, lon, start_date, end_date)
        
        return {
            'location': {'latitude': lat, 'longitude': lon},
            'current_weather': current_weather,
            'historical_weather': historical_weather[:50],  # Limit to 50 records
            'noaa_cdo_data': noaa_cdo_data[:50],  # Limit to 50 records
            'stations_found': len(us_stations) + len(ec_stations),
            'noaa_cdo_available': self.noaa_client is not None
        }

async def test_noaa_collector():
    """Test the NOAA data collector"""
    print("🧪 Testing NOAA Data Collector...")
    
    async with NOAADataCollector() as collector:
        # Test with Vancouver coordinates
        lat, lon = 49.2827, -123.1207
        
        result = await collector.collect_weather_for_location(lat, lon)
        
        print(f"✅ Collection complete!")
        print(f"   Location: {result['location']}")
        print(f"   Stations found: {result['stations_found']}")
        print(f"   Current weather: {result['current_weather'] is not None}")
        print(f"   Historical records: {len(result['historical_weather'])}")
        print(f"   NOAA CDO available: {result['noaa_cdo_available']}")
        print(f"   NOAA CDO records: {len(result['noaa_cdo_data'])}")
        
        if result['current_weather']:
            print(f"   Current temp: {result['current_weather'].get('temperature')}°C")
        
        if result['historical_weather']:
            print(f"   Latest historical: {result['historical_weather'][0]}")
        
        if result['noaa_cdo_data']:
            print(f"   Latest NOAA CDO: {result['noaa_cdo_data'][0]}")

if __name__ == "__main__":
    asyncio.run(test_noaa_collector())
