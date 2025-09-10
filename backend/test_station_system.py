#!/usr/bin/env python3
"""
Test the complete station database system
This script tests building the station database and using it for data collection
"""

import asyncio
from datetime import date, timedelta
from build_station_database import StationDatabaseBuilder
from station_lookup import StationLookup
from collect_data_using_station_db import EfficientDataCollector

async def test_complete_system():
    """Test the complete station database system"""
    print("🧪 Testing Complete Station Database System")
    print("=" * 50)
    
    # Step 1: Build the station database
    print("\n1️⃣ Building Station Database...")
    async with StationDatabaseBuilder() as builder:
        await builder.build_station_database()
    
    # Step 2: Test station lookup
    print("\n2️⃣ Testing Station Lookup...")
    lookup = StationLookup()
    
    # Get database statistics
    stats = lookup.get_database_stats()
    print(f"📊 Database Statistics:")
    print(f"  Total stations: {stats['total_stations']}")
    print(f"  Active stations: {stats['active_stations']}")
    print(f"  Stations with recent data: {stats['recent_data_stations']}")
    print(f"  High quality stations: {stats['high_quality_stations']}")
    print(f"  Date range: {stats['date_range']['first_year']} - {stats['date_range']['last_year']}")
    
    # Test getting active stations for last month
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n🔍 Active stations for last month ({start_date} to {end_date}):")
    active_stations = lookup.get_active_stations_for_period(start_date, end_date)
    print(f"  Found {len(active_stations)} active stations")
    
    if active_stations:
        print("  Top 5 stations by data count:")
        for i, station in enumerate(active_stations[:5]):
            print(f"    {i+1}. {station['name']} ({station['station_id']}) - {station['data_count']} records")
    
    # Test getting stations near major cities
    cities = [
        {"name": "Toronto", "lat": 43.6532, "lon": -79.3832},
        {"name": "Vancouver", "lat": 49.2827, "lon": -125.1208},
        {"name": "Montreal", "lat": 45.5017, "lon": -73.5673}
    ]
    
    for city in cities:
        print(f"\n📍 Stations near {city['name']} (within 100km):")
        nearby_stations = lookup.get_stations_near_location(city['lat'], city['lon'], 100)
        print(f"  Found {len(nearby_stations)} stations")
        
        if nearby_stations:
            print("  Top 3 stations:")
            for i, station in enumerate(nearby_stations[:3]):
                print(f"    {i+1}. {station['name']} ({station['station_id']}) - {station['data_count']} records")
    
    lookup.close()
    
    # Step 3: Test efficient data collection
    print("\n3️⃣ Testing Efficient Data Collection...")
    async with EfficientDataCollector() as collector:
        # Test with a small number of stations
        result = await collector.collect_data_for_period(start_date, end_date, max_stations=5)
        
        if result['success']:
            print(f"✅ Data collection test completed!")
            print(f"  Total records: {result['total_records']}")
            print(f"  Successful stations: {result['successful_stations']}")
            print(f"  Failed stations: {result['failed_stations']}")
        else:
            print(f"❌ Data collection test failed: {result.get('error', 'Unknown error')}")
    
    print("\n🎉 Complete system test finished!")

async def main():
    """Main function"""
    await test_complete_system()

if __name__ == "__main__":
    asyncio.run(main())
