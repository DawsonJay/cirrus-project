#!/usr/bin/env python3
"""
main.py - Daily Weather Data Collection Service

This is the main entry point for the weather data collection system.
It runs daily collection for the current year and can be scheduled as a cron job.
"""

import asyncio
import sys
import os
from datetime import datetime, date
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from collection import collect_year
from app.config import settings
from automated_maintenance import AutomatedMaintenance
from startup_load_stations import main as load_stations

async def daily_collection():
    """
    Run daily collection for the current year.
    This function collects data for all Canadian weather stations for the current year.
    """
    current_year = datetime.now().year
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 80)
    print("🌤️  DAILY WEATHER DATA COLLECTION SERVICE")
    print("=" * 80)
    print(f"📅 Date: {current_date}")
    print(f"📊 Year: {current_year}")
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🗄️  Database: {settings.DATABASE_PATH}")
    print("=" * 80)
    
    try:
        # Run collection for current year
        print(f"🚀 Starting daily collection for year {current_year}...")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # Run maintenance check first
        print("🔧 Running maintenance check...")
        maintenance = AutomatedMaintenance()
        maintenance_check = maintenance.check_maintenance_needed()
        
        if maintenance_check.get("maintenance_required", False):
            urgency = maintenance_check.get("urgency", "low")
            print(f"⚠️  Maintenance required ({urgency}): {', '.join(maintenance_check.get('reasons', []))}")
            
            if urgency == "critical":
                print("🚨 Running emergency maintenance...")
                maintenance.run_emergency_maintenance()
            elif urgency == "high":
                print("🔧 Running daily maintenance...")
                maintenance.run_daily_maintenance()
        else:
            print("✅ System health check passed")
        
        print("-" * 60)
        
        # Collect data for current year (no limit - collect all stations)
        result = await collect_year(current_year)
        
        # Print results
        print("-" * 60)
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if result and result.get('success', False):
            print("✅ Daily collection completed successfully!")
            print(f"📊 Summary:")
            print(f"   📡 Stations processed: {result.get('stations_processed', 0):,}")
            print(f"   ✅ Successful: {result.get('stations_successful', 0):,}")
            print(f"   ❌ Failed: {result.get('stations_failed', 0):,}")
            print(f"   📈 Records collected: {result.get('total_records_collected', 0):,}")
            print(f"   💾 Records stored: {result.get('total_records_stored', 0):,}")
            print(f"   ⏱️  Duration: {result.get('duration_seconds', 0):.1f} seconds")
            
            # Log to file for monitoring
            log_daily_collection(current_year, result, success=True)
            
        else:
            print("❌ Daily collection failed!")
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"   Error: {error_msg}")
            
            # Log failure
            log_daily_collection(current_year, result, success=False, error=error_msg)
            
            # Return non-zero exit code for failure
            return 1
            
    except Exception as e:
        print(f"❌ Daily collection failed with exception: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        
        # Log exception
        log_daily_collection(current_year, None, success=False, error=f"Exception: {str(e)}")
        
        return 1
    
    print("=" * 80)
    return 0

def log_daily_collection(year: int, result: dict, success: bool, error: str = None):
    """
    Log daily collection results to a file for monitoring.
    
    Args:
        year: Year that was collected
        result: Collection result dictionary
        success: Whether collection was successful
        error: Error message if failed
    """
    try:
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"daily_collection_{year}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, "a", encoding="utf-8") as f:
            if success:
                f.write(f"{timestamp} - SUCCESS - Year {year} - "
                       f"Stations: {result.get('stations_processed', 0)} "
                       f"({result.get('stations_successful', 0)} successful, "
                       f"{result.get('stations_failed', 0)} failed) - "
                       f"Records: {result.get('total_records_collected', 0)} collected, "
                       f"{result.get('total_records_stored', 0)} stored - "
                       f"Duration: {result.get('duration_seconds', 0):.1f}s\n")
            else:
                f.write(f"{timestamp} - FAILED - Year {year} - Error: {error}\n")
                
    except Exception as e:
        print(f"⚠️  Warning: Could not write to log file: {e}")

def print_usage():
    """Print usage information."""
    print("Usage:")
    print("  python main.py                    # Run daily collection for current year")
    print("  python main.py --help            # Show this help message")
    print("  python main.py --test            # Run test collection (limited stations)")
    print("")
    print("Environment Variables:")
    print("  NOAA_CDO_TOKEN                   # NOAA API token (required)")
    print("  DATABASE_PATH                    # Path to SQLite database")
    print("  ENVIRONMENT                      # Environment (development/production)")
    print("")
    print("Cron Job Example:")
    print("  # Run daily at 2:00 AM")
    print("  0 2 * * * cd /path/to/backend && python main.py >> logs/cron.log 2>&1")

async def test_collection():
    """
    Run a test collection with limited stations for testing purposes.
    """
    current_year = datetime.now().year
    
    print("=" * 80)
    print("🧪 TEST WEATHER DATA COLLECTION")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Year: {current_year}")
    print(f"🔢 Limit: 5 stations (test mode)")
    print("=" * 80)
    
    try:
        # Run test collection with limited stations
        result = await collect_year(current_year, limit=5)
        
        if result and result.get('success', False):
            print("✅ Test collection completed successfully!")
            print(f"📊 Test Results:")
            print(f"   📡 Stations processed: {result.get('stations_processed', 0)}")
            print(f"   ✅ Successful: {result.get('stations_successful', 0)}")
            print(f"   ❌ Failed: {result.get('stations_failed', 0)}")
            print(f"   📈 Records collected: {result.get('total_records_collected', 0)}")
            print(f"   💾 Records stored: {result.get('total_records_stored', 0)}")
            print(f"   ⏱️  Duration: {result.get('duration_seconds', 0):.1f} seconds")
        else:
            print("❌ Test collection failed!")
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"   Error: {error_msg}")
            return 1
            
    except Exception as e:
        print(f"❌ Test collection failed with exception: {str(e)}")
        return 1
    
    return 0

async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print_usage()
            return 0
        elif sys.argv[1] == '--test':
            return await test_collection()
        else:
            print(f"❌ Unknown option: {sys.argv[1]}")
            print_usage()
            return 1
    
    # Check for required environment variables
    if not os.getenv('NOAA_CDO_TOKEN'):
        print("❌ Error: NOAA_CDO_TOKEN environment variable is required")
        print("   Set it with: export NOAA_CDO_TOKEN=your_token_here")
        return 1
    
    # Ensure stations are loaded before collection
    print("🇨🇦 Ensuring Canadian stations are loaded...")
    if not load_stations():
        print("❌ Failed to load stations")
        return 1
    
    # Run daily collection
    return await daily_collection()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)