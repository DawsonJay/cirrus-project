#!/usr/bin/env python3
"""
Test script for the production data pool system
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.batch_updater import BatchUpdater
from app.database.connection import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_data_pool_system():
    """Test the production data pool system"""
    print("=== TESTING PRODUCTION DATA POOL SYSTEM ===\n")
    
    try:
        # 1. Initialize database
        print("1. Initializing database...")
        db_manager.initialize_database()
        print("✅ Database initialized successfully\n")
        
        # 2. Create batch updater
        print("2. Creating batch updater (batch size: 200)...")
        updater = BatchUpdater(batch_size=200)
        print("✅ Batch updater created\n")
        
        # 3. Test current weather update
        print("3. Testing current weather update...")
        print("   Using fixed batch size of 200 (reliable and efficient)\n")
        
        weather_result = await updater.update_current_weather()
        
        if weather_result.get("success"):
            print(f"✅ Current weather update successful!")
            print(f"   Updated: {weather_result['updated']} points")
            print(f"   Failed: {weather_result['failed']} points")
            print(f"   Total: {weather_result['total']} points")
            print(f"   Batches processed: {weather_result['batches_processed']}/{weather_result['total_batches']}")
        else:
            print(f"❌ Current weather update failed: {weather_result.get('error')}")
        
        print()
        
        # 4. Test forecast update
        print("4. Testing forecast update...")
        print("   Using same batch size for consistency\n")
        
        forecast_result = await updater.update_forecasts()
        
        if forecast_result.get("success"):
            print(f"✅ Forecast update successful!")
            print(f"   Updated: {forecast_result['updated']} points")
            print(f"   Failed: {forecast_result['failed']} points")
            print(f"   Total: {forecast_result['total']} points")
            print(f"   Batches processed: {forecast_result['batches_processed']}/{forecast_result['total_batches']}")
        else:
            print(f"❌ Forecast update failed: {forecast_result.get('error')}")
        
        print()
        
        # 5. Test data retrieval
        print("5. Testing data retrieval...")
        await test_data_retrieval()
        
        print("\n=== DATA POOL SYSTEM TEST COMPLETE ===")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")

async def test_data_retrieval():
    """Test retrieving data from the populated database"""
    try:
        with db_manager as conn:
            # Test current weather data
            cursor = conn.execute("""
                SELECT COUNT(*) as count 
                FROM current_weather 
                WHERE updated_at > datetime('now', '-1 hour')
            """)
            recent_weather = cursor.fetchone()["count"]
            
            # Test forecast data
            cursor = conn.execute("""
                SELECT COUNT(*) as count 
                FROM forecast_data 
                WHERE updated_at > datetime('now', '-1 hour')
            """)
            recent_forecasts = cursor.fetchone()["count"]
            
            # Test sample data
            cursor = conn.execute("""
                SELECT cw.temperature, cw.humidity, cw.weather_description,
                       gp.latitude, gp.longitude, gp.region_name
                FROM current_weather cw
                JOIN grid_points gp ON cw.grid_point_id = gp.id
                WHERE cw.updated_at > datetime('now', '-1 hour')
                LIMIT 5
            """)
            sample_data = cursor.fetchall()
            
            print(f"✅ Data retrieval successful!")
            print(f"   Recent weather records: {recent_weather}")
            print(f"   Recent forecast records: {recent_forecasts}")
            print(f"   Sample data:")
            
            for row in sample_data:
                print(f"     {row['latitude']:.2f}°N, {row['longitude']:.2f}°W ({row['region_name']}):")
                print(f"       {row['temperature']}°C, {row['humidity']}% humidity, {row['weather_description']}")
            
    except Exception as e:
        logger.error(f"Data retrieval test failed: {e}")
        print(f"❌ Data retrieval test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_data_pool_system())
