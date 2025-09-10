#!/usr/bin/env python3
"""
Reset the grid to 10,000 points for the new API limits
"""

import asyncio
import logging
from app.services.grid_generator import GridGenerator
from app.database.connection import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_grid():
    """Reset the grid to 10,000 points"""
    logger.info("Resetting grid to 10,000 points...")
    
    try:
        with db_manager as conn:
            # Clear all existing data
            logger.info("Clearing existing grid data...")
            conn.execute("DELETE FROM current_weather")
            conn.execute("DELETE FROM forecast_data")
            conn.execute("DELETE FROM grid_points")
            
            logger.info("Existing data cleared")
        
        # Generate new grid with 10,000 points
        grid_generator = GridGenerator(spacing_km=70.0)  # 70km spacing for ~10K points
        success = grid_generator.populate_database()
        
        if success:
            # Get stats
            stats = grid_generator.get_grid_stats()
            logger.info(f"✅ Grid reset successful!")
            logger.info(f"Total points: {stats.get('total_points', 0)}")
            logger.info(f"Regions: {stats.get('regions', 0)}")
            logger.info(f"Latitude range: {stats.get('min_lat', 0)} to {stats.get('max_lat', 0)}")
            logger.info(f"Longitude range: {stats.get('min_lon', 0)} to {stats.get('max_lon', 0)}")
            
            # Show region breakdown
            region_breakdown = stats.get('region_breakdown', {})
            logger.info("Region breakdown:")
            for region, count in region_breakdown.items():
                logger.info(f"  {region}: {count} points")
                
        else:
            logger.error("❌ Failed to populate new grid")
            return False
            
    except Exception as e:
        logger.error(f"❌ Grid reset failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = reset_grid()
    if success:
        print("\n🎉 Grid reset complete! Ready for 10,000 point system.")
    else:
        print("\n💥 Grid reset failed!")

