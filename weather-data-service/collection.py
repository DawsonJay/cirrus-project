#!/usr/bin/env python3
"""
collection.py - Bulk data collection for all Canadian weather stations

This script handles bulk data collection across all stations in the database.
It provides functions to collect data for specific years, stations, or date ranges.
"""

import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from station import collect_station_data_year
from stations_database import update_active_periods
from weather_database import store_station_data
from app.config import settings

# Database path
DATABASE_PATH = Path(__file__).parent / "data" / "weather_pool.db"

async def collect_year(year: int, limit: Optional[int] = None) -> Dict[str, any]:
    """
    Collect weather data for all Canadian stations for a specific year.
    
    Args:
        year: Year to collect data for (e.g., 2024)
        limit: Optional limit on number of stations to process (for testing)
    
    Returns:
        Dictionary with collection statistics and results
    """
    print(f"🚀 Starting bulk data collection for year {year}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get all Canadian stations from database
    stations = get_all_stations(limit)
    
    if not stations:
        print("❌ No stations found in database!")
        return {
            "success": False,
            "error": "No stations found in database",
            "year": year,
            "stations_processed": 0,
            "total_stations": 0
        }
    
    print(f"📊 Found {len(stations)} stations to process")
    if limit:
        print(f"🔢 Limited to {limit} stations for testing")
    
    # Collection statistics
    stats = {
        "year": year,
        "total_stations": len(stations),
        "stations_processed": 0,
        "stations_successful": 0,
        "stations_failed": 0,
        "total_records_collected": 0,
        "total_records_stored": 0,
        "errors": [],
        "start_time": datetime.now(),
        "end_time": None,
        "success": True
    }
    
    # Process stations in parallel batches
    batch_size = 5  # Process 5 stations simultaneously (reduced to avoid rate limits)
    semaphore = asyncio.Semaphore(batch_size)  # Limit concurrent requests
    
    async def process_station(station, station_index):
        """Process a single station with semaphore limiting"""
        async with semaphore:
            station_id = station['station_id']
            station_name = station['name']
            
            try:
                # Collect data for this station and year
                result = await collect_station_data_year(station_id, year)
                
                if result and any(result.values()):
                    # Count records collected
                    records_collected = sum(len(records) for records in result.values())
                    return {
                        "success": True,
                        "station_id": station_id,
                        "station_name": station_name,
                        "records_collected": records_collected,
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "station_id": station_id,
                        "station_name": station_name,
                        "records_collected": 0,
                        "error": f"No data available for {year}"
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "station_id": station_id,
                    "station_name": station_name,
                    "records_collected": 0,
                    "error": str(e)
                }
    
    # Process stations in batches
    total_stations = len(stations)
    for batch_start in range(0, total_stations, batch_size):
        batch_end = min(batch_start + batch_size, total_stations)
        batch_stations = stations[batch_start:batch_end]
        
        # Calculate progress
        progress_pct = (batch_start / total_stations) * 100
        elapsed_time = datetime.now() - stats["start_time"]
        
        print(f"\n🔄 Processing batch {batch_start//batch_size + 1}: stations {batch_start+1:,}-{batch_end:,}")
        print(f"    📊 Progress: {batch_start:,}/{total_stations:,} ({progress_pct:.1f}%)")
        print(f"    ⏱️  Elapsed: {str(elapsed_time).split('.')[0]}")
        print(f"    📈 Current Stats: {stats['stations_successful']} successful, {stats['stations_failed']} failed, {stats['total_records_collected']:,} records")
        
        # Process batch in parallel
        tasks = [process_station(station, i) for i, station in enumerate(batch_stations, batch_start + 1)]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                stats["stations_failed"] += 1
                stats["errors"].append(f"Batch processing error: {str(result)}")
                print(f"    ❌ Batch error: {str(result)}")
            else:
                stats["stations_processed"] += 1
                
                if result["success"]:
                    stats["stations_successful"] += 1
                    stats["total_records_collected"] += result["records_collected"]
                    print(f"    ✅ {result['station_name']}: {result['records_collected']:,} records")
                else:
                    stats["stations_failed"] += 1
                    stats["errors"].append(f"{result['station_id']}: {result['error']}")
                    print(f"    ⚠️  {result['station_name']}: {result['error']}")
        
        # Rate limiting between batches
        await asyncio.sleep(2.0)  # 2 seconds between batches to respect rate limits
        
        # Show progress every 10 batches
        if (batch_start // batch_size + 1) % 10 == 0:
            print(f"\n🔄 Progress Update: {batch_end:,}/{total_stations:,} stations processed ({progress_pct:.1f}%)")
            print(f"    📊 Current Stats: {stats['stations_successful']} successful, {stats['stations_failed']} failed, {stats['total_records_collected']:,} records")
    
    # Final statistics
    stats["end_time"] = datetime.now()
    duration = stats["end_time"] - stats["start_time"]
    stats["duration_seconds"] = duration.total_seconds()
    
    # Get final record count from database
    stats["total_records_stored"] = get_total_records_count(year)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 COLLECTION SUMMARY FOR {year}")
    print("=" * 60)
    print(f"⏱️  Duration: {duration}")
    print(f"📡 Stations processed: {stats['stations_processed']}/{stats['total_stations']}")
    print(f"✅ Successful: {stats['stations_successful']}")
    print(f"❌ Failed: {stats['stations_failed']}")
    print(f"📊 Records collected: {stats['total_records_collected']}")
    print(f"💾 Records stored: {stats['total_records_stored']}")
    
    if stats["errors"]:
        print(f"\n❌ Errors encountered:")
        for error in stats["errors"][:10]:  # Show first 10 errors
            print(f"  • {error}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")
    
    print(f"\n🎯 Collection completed at: {stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    return stats

async def collect_years(start_year: int, end_year: int, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Collect weather data for all Canadian stations across multiple years.
    
    Args:
        start_year: First year to collect data for (inclusive)
        end_year: Last year to collect data for (inclusive)
        limit: Optional limit on number of stations to process per year
    
    Returns:
        Dictionary with collection statistics for all years
    """
    print(f"🌤️  Multi-Year Weather Data Collection Service")
    print(f"📅 Years: {start_year} to {end_year}")
    print(f"🔢 Limit: {limit if limit else 'All stations'}")
    print("=" * 60)
    
    # Validate year range
    if start_year > end_year:
        raise ValueError("Start year must be less than or equal to end year")
    
    current_year = datetime.now().year
    if end_year > current_year:
        print(f"⚠️  Warning: End year {end_year} is in the future, limiting to {current_year}")
        end_year = current_year
    
    if start_year < 1800:
        raise ValueError("Start year must be 1800 or later")
    
    # Collection statistics across all years
    multi_year_stats = {
        "start_year": start_year,
        "end_year": end_year,
        "total_years": end_year - start_year + 1,
        "years_processed": 0,
        "years_successful": 0,
        "years_failed": 0,
        "total_stations_processed": 0,
        "total_stations_successful": 0,
        "total_stations_failed": 0,
        "total_records_collected": 0,
        "total_records_stored": 0,
        "year_results": {},
        "start_time": datetime.now(),
        "end_time": None,
        "success": True
    }
    
    print(f"🚀 Starting multi-year collection for {multi_year_stats['total_years']} years")
    print(f"⏰ Started at: {multi_year_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Process each year
    for year in range(start_year, end_year + 1):
        print(f"\n📅 Processing year {year} ({year - start_year + 1}/{multi_year_stats['total_years']})")
        print("-" * 40)
        
        try:
            # Collect data for this year
            year_stats = await collect_year(year, limit)
            
            # Update multi-year statistics
            multi_year_stats["years_processed"] += 1
            multi_year_stats["year_results"][year] = year_stats
            
            if year_stats.get("success", False):
                multi_year_stats["years_successful"] += 1
                multi_year_stats["total_stations_processed"] += year_stats.get("stations_processed", 0)
                multi_year_stats["total_stations_successful"] += year_stats.get("stations_successful", 0)
                multi_year_stats["total_stations_failed"] += year_stats.get("stations_failed", 0)
                multi_year_stats["total_records_collected"] += year_stats.get("total_records_collected", 0)
                multi_year_stats["total_records_stored"] += year_stats.get("total_records_stored", 0)
                
                print(f"✅ Year {year} completed successfully")
                print(f"   📊 Stations: {year_stats.get('stations_successful', 0)} successful, {year_stats.get('stations_failed', 0)} failed")
                print(f"   📈 Records: {year_stats.get('total_records_collected', 0):,} collected, {year_stats.get('total_records_stored', 0):,} stored")
            else:
                multi_year_stats["years_failed"] += 1
                print(f"❌ Year {year} failed: {year_stats.get('error', 'Unknown error')}")
            
        except Exception as e:
            multi_year_stats["years_failed"] += 1
            multi_year_stats["year_results"][year] = {
                "success": False,
                "error": str(e),
                "stations_processed": 0,
                "stations_successful": 0,
                "stations_failed": 0,
                "total_records_collected": 0,
                "total_records_stored": 0
            }
            print(f"❌ Year {year} failed with exception: {str(e)}")
        
        # Add delay between years to be respectful to the API
        if year < end_year:
            print(f"⏳ Waiting 5 seconds before processing next year...")
            await asyncio.sleep(5)
    
    # Final statistics
    multi_year_stats["end_time"] = datetime.now()
    duration = multi_year_stats["end_time"] - multi_year_stats["start_time"]
    multi_year_stats["duration_seconds"] = duration.total_seconds()
    
    # Print final summary
    print("\n" + "=" * 60)
    print(f"📊 MULTI-YEAR COLLECTION SUMMARY")
    print("=" * 60)
    print(f"📅 Years: {start_year} to {end_year}")
    print(f"⏱️  Duration: {duration}")
    print(f"📊 Years processed: {multi_year_stats['years_processed']}/{multi_year_stats['total_years']}")
    print(f"✅ Years successful: {multi_year_stats['years_successful']}")
    print(f"❌ Years failed: {multi_year_stats['years_failed']}")
    print(f"📡 Total stations processed: {multi_year_stats['total_stations_processed']:,}")
    print(f"✅ Total stations successful: {multi_year_stats['total_stations_successful']:,}")
    print(f"❌ Total stations failed: {multi_year_stats['total_stations_failed']:,}")
    print(f"📊 Total records collected: {multi_year_stats['total_records_collected']:,}")
    print(f"💾 Total records stored: {multi_year_stats['total_records_stored']:,}")
    
    # Show per-year breakdown
    print(f"\n📅 Per-Year Breakdown:")
    for year, year_stats in multi_year_stats["year_results"].items():
        if year_stats.get("success", False):
            print(f"  ✅ {year}: {year_stats.get('stations_successful', 0)} stations, {year_stats.get('total_records_collected', 0):,} records")
        else:
            print(f"  ❌ {year}: Failed - {year_stats.get('error', 'Unknown error')}")
    
    print(f"\n🎯 Multi-year collection completed at: {multi_year_stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎉 Multi-year collection completed successfully!")
    
    return multi_year_stats

def get_all_stations(limit: Optional[int] = None) -> List[Dict]:
    """
    Get all Canadian weather stations from the database.
    
    Args:
        limit: Optional limit on number of stations to return
    
    Returns:
        List of station dictionaries
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            query = "SELECT station_id, name, latitude, longitude, elevation, active_periods FROM all_canadian_stations ORDER BY name"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            stations = []
            
            for row in cursor.fetchall():
                station = dict(zip(columns, row))
                # Parse active_periods JSON
                if station.get('active_periods'):
                    try:
                        station['active_periods'] = json.loads(station['active_periods'])
                    except json.JSONDecodeError:
                        station['active_periods'] = []
                else:
                    station['active_periods'] = []
                stations.append(station)
            
            return stations
            
    except Exception as e:
        print(f"❌ Error getting stations from database: {e}")
        return []

def get_total_records_count(year: int) -> int:
    """
    Get total number of weather records stored for a specific year.
    
    Args:
        year: Year to count records for
    
    Returns:
        Total number of records
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM daily_weather_data WHERE strftime('%Y', date) = ?",
                (str(year),)
            )
            return cursor.fetchone()[0]
    except Exception as e:
        print(f"❌ Error counting records: {e}")
        return 0

async def collect_station_range(station_ids: List[str], year: int) -> Dict[str, any]:
    """
    Collect data for a specific list of stations for a given year.
    
    Args:
        station_ids: List of station IDs to collect data for
        year: Year to collect data for
    
    Returns:
        Dictionary with collection statistics
    """
    print(f"🚀 Starting data collection for {len(station_ids)} stations in {year}")
    
    stats = {
        "year": year,
        "stations_requested": len(station_ids),
        "stations_processed": 0,
        "stations_successful": 0,
        "stations_failed": 0,
        "total_records_collected": 0,
        "errors": [],
        "start_time": datetime.now()
    }
    
    for i, station_id in enumerate(station_ids, 1):
        print(f"\n📡 [{i}/{len(station_ids)}] Processing: {station_id}")
        
        try:
            result = await collect_station_data_year(station_id, year)
            
            if result and any(result.values()):
                records_collected = sum(len(records) for records in result.values())
                stats["total_records_collected"] += records_collected
                stats["stations_successful"] += 1
                print(f"  ✅ Success: {records_collected} records collected")
            else:
                stats["stations_failed"] += 1
                stats["errors"].append(f"{station_id}: No data available")
                print(f"  ⚠️  No data available")
            
            stats["stations_processed"] += 1
            await asyncio.sleep(0.2)  # Rate limiting
            
        except Exception as e:
            stats["stations_failed"] += 1
            stats["errors"].append(f"{station_id}: {str(e)}")
            print(f"  ❌ Error: {str(e)}")
            stats["stations_processed"] += 1
    
    stats["end_time"] = datetime.now()
    stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
    
    return stats

async def collect_recent_data(days: int = 30) -> Dict[str, any]:
    """
    Collect recent data for all stations (last N days).
    
    Args:
        days: Number of days to look back
    
    Returns:
        Dictionary with collection statistics
    """
    from datetime import timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"🚀 Collecting recent data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # This would require modifying the station.py functions to accept date ranges
    # For now, we'll collect the current year
    current_year = datetime.now().year
    return await collect_year(current_year)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python collection.py <year> [limit]           # Collect single year")
        print("  python collection.py <start_year> <end_year> [limit]  # Collect year range")
        print(f"Examples:")
        print(f"  python collection.py 2024                    # Collect 2024 data")
        print(f"  python collection.py 2024 10                 # Collect 2024 data, limit to 10 stations")
        print(f"  python collection.py 2020 2024               # Collect 2020-2024 data")
        print(f"  python collection.py 2020 2024 100           # Collect 2020-2024 data, limit to 100 stations per year")
        sys.exit(1)
    
    try:
        if len(sys.argv) == 2:
            # Single year collection
            year_to_collect = int(sys.argv[1])
            print(f"🌤️  Weather Data Collection Service")
            print(f"📅 Year: {year_to_collect}")
            print(f"🔢 Limit: All stations")
            print("==================================================")
            asyncio.run(collect_year(year_to_collect))
            
        elif len(sys.argv) == 3:
            # Check if second argument is a year or limit
            try:
                second_arg = int(sys.argv[2])
                if second_arg > 1000:  # Likely a year
                    # Year range collection
                    start_year = int(sys.argv[1])
                    end_year = second_arg
                    print(f"🌤️  Multi-Year Weather Data Collection Service")
                    print(f"📅 Years: {start_year} to {end_year}")
                    print(f"🔢 Limit: All stations")
                    print("==================================================")
                    asyncio.run(collect_years(start_year, end_year))
                else:
                    # Single year with limit
                    year_to_collect = int(sys.argv[1])
                    limit_stations = second_arg
                    print(f"🌤️  Weather Data Collection Service")
                    print(f"📅 Year: {year_to_collect}")
                    print(f"🔢 Limit: {limit_stations} stations")
                    print("==================================================")
                    asyncio.run(collect_year(year_to_collect, limit_stations))
            except ValueError:
                print("❌ Invalid arguments. Please provide valid years and numbers.")
                sys.exit(1)
                
        elif len(sys.argv) == 4:
            # Year range with limit
            start_year = int(sys.argv[1])
            end_year = int(sys.argv[2])
            limit_stations = int(sys.argv[3])
            print(f"🌤️  Multi-Year Weather Data Collection Service")
            print(f"📅 Years: {start_year} to {end_year}")
            print(f"🔢 Limit: {limit_stations} stations per year")
            print("==================================================")
            asyncio.run(collect_years(start_year, end_year, limit_stations))
            
        else:
            print("❌ Too many arguments provided.")
            sys.exit(1)
            
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Collection interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
