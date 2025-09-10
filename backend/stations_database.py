#!/usr/bin/env python3
"""
Stations Database Operations

This module handles all operations related to the stations database,
including station lookup, metadata management, and active period tracking.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from pathlib import Path

# Database path
DATABASE_PATH = Path(__file__).parent / "data" / "weather_pool.db"

def update_active_periods(station_id: str, station_data: Dict[str, List[Dict]]) -> None:
    """
    Update active periods for a station based on new data.
    
    An active period is a continuous range of dates where the station has data.
    This function analyzes the provided data, determines active periods,
    and merges them with existing periods in the database.
    
    Args:
        station_id: NOAA station ID (e.g., 'GHCND:CA006158355')
        station_data: Dictionary from get_station_data_year() with dataset IDs as keys
                     and lists of weather records as values
    """
    # Extract all unique dates from the station data
    all_dates = set()
    
    for dataset_id, records in station_data.items():
        for record in records:
            # Extract date from ISO format (e.g., '2024-12-31T00:00:00' -> '2024-12-31')
            date_str = record['date'][:10]
            all_dates.add(date_str)
    
    if not all_dates:
        print(f"⚠️  No dates found in station data for {station_id}")
        return
    
    # Convert to sorted list of date objects
    sorted_dates = sorted([datetime.strptime(date, '%Y-%m-%d').date() for date in all_dates])
    
    # Find continuous date ranges (active periods)
    new_periods = _find_continuous_periods(sorted_dates)
    
    if not new_periods:
        print(f"⚠️  No continuous periods found for {station_id}")
        return
    
    print(f"🔍 Found {len(new_periods)} new active periods for {station_id}")
    for period in new_periods:
        print(f"  📅 {period[0]} to {period[1]} ({period[2]} days)")
    
    # Get existing active periods from database
    existing_periods = _get_existing_periods(station_id)
    
    # Merge new periods with existing ones
    merged_periods = _merge_periods(existing_periods, new_periods)
    
    # Update database with merged periods
    _update_database_periods(station_id, merged_periods)
    
    print(f"✅ Updated active periods for {station_id}: {len(merged_periods)} total periods")

def _find_continuous_periods(dates: List[datetime.date]) -> List[Tuple[str, str, int]]:
    """
    Find continuous date ranges from a sorted list of dates.
    
    Args:
        dates: Sorted list of date objects
        
    Returns:
        List of tuples (start_date, end_date, day_count) as strings
    """
    if not dates:
        return []
    
    periods = []
    current_start = dates[0]
    current_end = dates[0]
    
    for i in range(1, len(dates)):
        # Check if this date is consecutive to the previous one
        if dates[i] == current_end + timedelta(days=1):
            current_end = dates[i]
        else:
            # End of current period, start a new one
            day_count = (current_end - current_start).days + 1
            periods.append((
                current_start.strftime('%Y-%m-%d'),
                current_end.strftime('%Y-%m-%d'),
                day_count
            ))
            current_start = dates[i]
            current_end = dates[i]
    
    # Add the last period
    day_count = (current_end - current_start).days + 1
    periods.append((
        current_start.strftime('%Y-%m-%d'),
        current_end.strftime('%Y-%m-%d'),
        day_count
    ))
    
    return periods

def _get_existing_periods(station_id: str) -> List[Tuple[str, str, int]]:
    """
    Get existing active periods for a station from the database.
    
    Args:
        station_id: NOAA station ID
        
    Returns:
        List of tuples (start_date, end_date, day_count)
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Check if the station exists and has active_periods data
            cursor.execute("""
                SELECT active_periods FROM all_canadian_stations 
                WHERE station_id = ?
            """, (station_id,))
            
            result = cursor.fetchone()
            if not result or not result[0]:
                return []
            
            # Parse JSON data
            periods_data = json.loads(result[0])
            return [(period['start'], period['end'], period['days']) for period in periods_data]
            
    except Exception as e:
        print(f"❌ Error getting existing periods for {station_id}: {e}")
        return []

def _merge_periods(existing: List[Tuple[str, str, int]], 
                  new: List[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
    """
    Merge existing and new active periods, combining overlapping or adjacent periods.
    
    Args:
        existing: List of existing periods (start, end, days)
        new: List of new periods (start, end, days)
        
    Returns:
        List of merged periods
    """
    # Combine all periods
    all_periods = existing + new
    
    if not all_periods:
        return []
    
    # Convert to date objects for easier manipulation
    period_objects = []
    for start_str, end_str, days in all_periods:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        period_objects.append((start_date, end_date))
    
    # Sort by start date
    period_objects.sort(key=lambda x: x[0])
    
    # Merge overlapping or adjacent periods
    merged = [period_objects[0]]
    
    for current_start, current_end in period_objects[1:]:
        last_start, last_end = merged[-1]
        
        # Check if periods overlap or are adjacent (within 1 day)
        if current_start <= last_end + timedelta(days=1):
            # Merge periods
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            # Add as new period
            merged.append((current_start, current_end))
    
    # Convert back to string format
    result = []
    for start_date, end_date in merged:
        day_count = (end_date - start_date).days + 1
        result.append((
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            day_count
        ))
    
    return result

def _update_database_periods(station_id: str, periods: List[Tuple[str, str, int]]) -> None:
    """
    Update the database with merged active periods.
    
    Args:
        station_id: NOAA station ID
        periods: List of merged periods (start, end, days)
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Convert periods to JSON format
            periods_json = json.dumps([
                {
                    'start': start,
                    'end': end,
                    'days': days
                }
                for start, end, days in periods
            ])
            
            # Update the station record
            cursor.execute("""
                UPDATE all_canadian_stations 
                SET active_periods = ?
                WHERE station_id = ?
            """, (periods_json, station_id))
            
            if cursor.rowcount == 0:
                print(f"⚠️  Station {station_id} not found in database")
            else:
                conn.commit()
                print(f"✅ Updated database with {len(periods)} active periods for {station_id}")
                
    except Exception as e:
        print(f"❌ Error updating database for {station_id}: {e}")

# TODO: Implement additional station database operations
# - Station lookup by coordinates, name, or ID
# - Station metadata updates
# - Geographic filtering and search
