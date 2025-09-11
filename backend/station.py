#!/usr/bin/env python3
"""
station.py - Get data from a single weather station

This script will handle retrieving weather data from a single NOAA station.
It will be the foundation for our data collection system.
"""

import asyncio
import aiohttp
import random
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from app.config import settings

async def make_api_call_with_retry(session: aiohttp.ClientSession, url: str, params: dict, headers: dict, max_retries: int = 5) -> Optional[aiohttp.ClientResponse]:
    """
    Make an API call with exponential backoff retry logic for rate limiting.
    
    Args:
        session: aiohttp ClientSession
        url: API endpoint URL
        params: Query parameters
        headers: Request headers
        max_retries: Maximum number of retry attempts
    
    Returns:
        aiohttp ClientResponse or None if all retries failed
    """
    for attempt in range(max_retries + 1):
        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return response
                elif response.status == 429:  # Rate limit exceeded
                    if attempt < max_retries:
                        # Exponential backoff with jitter: 2^attempt + random(0, 1)
                        base_delay = 2 ** attempt
                        jitter = random.uniform(0, 1)
                        delay = min(base_delay + jitter, 600)  # Cap at 10 minutes
                        
                        print(f"  ⚠️  Rate limit exceeded (429), retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"  ❌ Rate limit exceeded, max retries ({max_retries}) reached")
                        return response
                elif response.status == 503:  # Service unavailable
                    if attempt < max_retries:
                        # Shorter delay for 503 errors
                        delay = min(30 + (attempt * 10), 300)  # 30s to 5min max
                        print(f"  ⚠️  Service unavailable (503), retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"  ❌ Service unavailable, max retries ({max_retries}) reached")
                        return response
                else:
                    # Other errors (400, 404, etc.) - don't retry
                    print(f"  ❌ API error {response.status}")
                    return response
                    
        except asyncio.TimeoutError:
            if attempt < max_retries:
                delay = min(30 + (attempt * 10), 300)  # 30s to 5min max
                print(f"  ⚠️  Request timeout, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(delay)
                continue
            else:
                print(f"  ❌ Request timeout, max retries ({max_retries}) reached")
                return None
        except Exception as e:
            if attempt < max_retries:
                delay = min(30 + (attempt * 10), 300)  # 30s to 5min max
                print(f"  ⚠️  Request error: {e}, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(delay)
                continue
            else:
                print(f"  ❌ Request error: {e}, max retries ({max_retries}) reached")
                return None
    
    return None

async def get_station_data_year_by_dataset(station_id: str, year: int, dataset_id: str) -> List[Dict]:
    """
    Get all weather data for a station for a specific year and dataset type
    
    Args:
        station_id: NOAA station ID (e.g., 'GHCND:CA006158350')
        year: Year to get data for (e.g., 2024)
        dataset_id: NOAA dataset ID (e.g., 'GHCND', 'PRECIP_HLY', 'NORMAL_DLY')
    
    Returns:
        List of all weather data records for that year and dataset
    """
    try:
        print(f"🔍 Getting all data for station {station_id} for year {year}")
        
        all_records = []
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # If requesting current year, use today as end date
        if year == datetime.now().year:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        current_end_date = end_date
        
        while True:
            print(f"  📡 Getting records from {start_date} to {current_end_date}")
            
            # Make API call for current date range
            url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
            params = {
                'datasetid': dataset_id,
                'stationid': station_id,
                'startdate': start_date,
                'enddate': current_end_date,
                'limit': 1000,
                'sortfield': 'date',
                'sortorder': 'desc'
            }
            headers = {'token': settings.NOAA_CDO_TOKEN}
            
            # Add timeout to prevent hanging
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout per request
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                response = await make_api_call_with_retry(session, url, params, headers)
                
                if response is None:
                    print(f"  ❌ Failed to get response after retries")
                    break
                
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    if not results:
                        print(f"  ✅ No more data found")
                        break
                    
                    print(f"  ✅ Got {len(results)} records")
                    all_records.extend(results)
                    
                    # Check if we hit the 1000 record limit
                    metadata = data.get('metadata', {})
                    resultset = metadata.get('resultset', {})
                    total_count = resultset.get('count', 0)
                    
                    if len(results) < 1000 or len(results) >= total_count:
                        print(f"  ✅ Got all available records ({total_count} total)")
                        break
                    
                    # We hit the limit, need to get older data
                    # Find the oldest date in current results
                    oldest_date = results[-1]['date'][:10]  # Get YYYY-MM-DD part
                    print(f"  ⚠️  Hit 1000 record limit, oldest date: {oldest_date}")
                    
                    # Calculate next end date (day before oldest date)
                    oldest_dt = datetime.strptime(oldest_date, '%Y-%m-%d')
                    next_end_dt = oldest_dt - timedelta(days=1)
                    current_end_date = next_end_dt.strftime('%Y-%m-%d')
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                else:
                    print(f"  ❌ API error {response.status}")
                    break
        
        print(f"✅ Retrieved {len(all_records)} total records for {year} from {dataset_id}")
        return all_records
        
    except Exception as e:
        print(f"❌ Error getting data for station '{station_id}' year {year} dataset {dataset_id}: {e}")
        return []

async def get_station_data_year(station_id: str, year: int) -> Dict[str, List[Dict]]:
    """
    Get all weather data for a station for a specific year from all relevant datasets
    
    Args:
        station_id: NOAA station ID (e.g., 'GHCND:CA006158350')
        year: Year to get data for (e.g., 2024)
    
    Returns:
        Dictionary with dataset IDs as keys and lists of records as values
        {
            'GHCND': [...],      # Daily summaries
            'PRECIP_HLY': [...], # Hourly precipitation
            'NORMAL_DLY': [...]  # Daily normals
        }
    """
    try:
        print(f"🔍 Getting comprehensive data for station {station_id} for year {year}")
        
        # Define the datasets we want to collect
        datasets = {
            'GHCND': 'Daily Summaries',
            'PRECIP_HLY': 'Hourly Precipitation', 
            'NORMAL_DLY': 'Daily Normals'
        }
        
        all_data = {}
        
        for dataset_id, description in datasets.items():
            print(f"  📊 Collecting {description} ({dataset_id})...")
            
            try:
                data = await get_station_data_year_by_dataset(station_id, year, dataset_id)
                all_data[dataset_id] = data
                
                if data:
                    print(f"    ✅ Got {len(data)} records from {dataset_id}")
                else:
                    print(f"    ⚠️  No data available from {dataset_id}")
                    
            except Exception as e:
                print(f"    ❌ Error collecting {dataset_id}: {e}")
                all_data[dataset_id] = []
            
            # Rate limiting between datasets
            await asyncio.sleep(1)
        
        total_records = sum(len(records) for records in all_data.values())
        print(f"✅ Retrieved {total_records} total records across all datasets for {year}")
        
        return all_data
        
    except Exception as e:
        print(f"❌ Error getting comprehensive data for station '{station_id}' year {year}: {e}")
        return {}

async def collect_station_data_year(station_id: str, year: int) -> Dict[str, List[Dict]]:
    """
    Complete workflow to collect, process, and store weather data for a station for a specific year.
    
    This function orchestrates the entire data collection process:
    1. Gets weather data from NOAA API
    2. Updates active periods in the station database
    3. Stores weather data in the weather database
    
    Args:
        station_id: NOAA station ID (e.g., 'GHCND:CA006158350')
        year: Year to collect data for (e.g., 2024)
    
    Returns:
        Dictionary with dataset IDs as keys and lists of records as values
        {
            'GHCND': [...],      # Daily summaries
            'PRECIP_HLY': [...], # Hourly precipitation
            'NORMAL_DLY': [...]  # Daily normals
        }
    """
    try:
        print(f"🚀 Starting complete data collection for station {station_id} for year {year}")
        
        # Step 1: Get weather data from NOAA API
        print(f"\\n📡 Step 1: Collecting weather data from NOAA API...")
        station_data = await get_station_data_year(station_id, year)
        
        if not station_data or not any(station_data.values()):
            print(f"⚠️  No data available for station {station_id} for year {year}")
            return station_data
        
        # Step 2: Update active periods in station database
        print(f"\\n🔄 Step 2: Updating active periods...")
        try:
            from stations_database import update_active_periods
            update_active_periods(station_id, station_data)
        except Exception as e:
            print(f"❌ Error updating active periods: {e}")
        
        # Step 3: Store weather data in weather database
        print(f"\\n🗄️  Step 3: Storing weather data...")
        try:
            from weather_database import store_station_data
            store_station_data(station_id, station_data)
        except Exception as e:
            print(f"❌ Error storing weather data: {e}")
        
        # Summary
        total_records = sum(len(records) for records in station_data.values())
        print(f"\\n✅ Complete data collection finished for {station_id}")
        print(f"📊 Total records processed: {total_records}")
        
        return station_data
        
    except Exception as e:
        print(f"❌ Error in complete data collection for station '{station_id}' year {year}: {e}")
        return {}

if __name__ == "__main__":
    print("station.py - Single station data retrieval")
    print("TODO: Test the collect_station_data_year function")
