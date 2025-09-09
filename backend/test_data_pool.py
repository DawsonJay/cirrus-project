#!/usr/bin/env python3
"""
Test script for the data pool system
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.database.connection import db_manager
from app.services.grid_generator import GridGenerator
from app.services.batch_updater import BatchUpdater

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_data_pool():
    """Test the complete data pool system"""
    
    print("=== TESTING DATA POOL SYSTEM ===\n")
    
    # 1. Initialize database
    print("1. Initializing database...")
    if db_manager.initialize_database():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
        return
    
    # 2. Generate grid
    print("\n2. Generating grid coordinates...")
    grid_generator = GridGenerator(spacing_km=100.0)  # Start with 100km for testing
    
    if grid_generator.populate_database():
        print("✅ Grid populated successfully")
        
        # Show grid stats
        stats = grid_generator.get_grid_stats()
        print(f"   Total points: {stats.get('total_points', 0)}")
        print(f"   Regions: {stats.get('regions', 0)}")
        print(f"   Coverage: {stats.get('min_lat', 0):.1f}°N to {stats.get('max_lat', 0):.1f}°N")
        print(f"   Longitude: {stats.get('min_lon', 0):.1f}°W to {stats.get('max_lon', 0):.1f}°W")
        
        if 'region_breakdown' in stats:
            print("   Region breakdown:")
            for region, count in list(stats['region_breakdown'].items())[:5]:
                print(f"     {region}: {count} points")
    else:
        print("❌ Grid population failed")
        return
    
    # 3. Test batch update (efficient large batches)
    print("\n3. Testing batch update...")
    batch_updater = BatchUpdater(batch_size=540)  # Optimal batch size found through testing
    
    # Test with all coordinates (now efficient with large batches)
    coordinates = grid_generator.get_coordinates_for_batch()
    print(f"   Testing with {len(coordinates)} coordinates in {len(coordinates)//540 + 1} batches")
    
    # Update current weather
    result = await batch_updater.update_all_current_weather()
    if result.get("success"):
        print(f"✅ Current weather update: {result['updated']} updated, {result['failed']} failed")
    else:
        print(f"❌ Current weather update failed: {result.get('error', 'Unknown error')}")
    
    # 4. Test data retrieval
    print("\n4. Testing data retrieval...")
    try:
        with db_manager as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM current_weather 
                WHERE updated_at > datetime('now', '-1 hour')
            """)
            recent_data = cursor.fetchone()["count"]
            print(f"✅ Found {recent_data} recent weather records")
            
            # Show sample data
            cursor = conn.execute("""
                SELECT cw.*, gp.latitude, gp.longitude, gp.region_name
                FROM current_weather cw
                JOIN grid_points gp ON cw.grid_point_id = gp.id
                LIMIT 3
            """)
            samples = cursor.fetchall()
            
            print("   Sample data:")
            for sample in samples:
                print(f"     {sample['region_name']} ({sample['latitude']:.1f}, {sample['longitude']:.1f}): "
                      f"{sample['temperature']:.1f}°C, {sample['humidity']:.1f}% humidity")
    
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")
    
    print("\n=== DATA POOL TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_data_pool())
