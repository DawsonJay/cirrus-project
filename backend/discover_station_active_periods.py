#!/usr/bin/env python3
"""
Discover active periods for each station by checking for actual data availability
Since NOAA doesn't provide active periods in station metadata, we need to determine
when each station was actually collecting data by making test API calls
"""

import asyncio
import aiohttp
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from app.config import settings

def get_database_connection():
    """Get database connection"""
    db_path = Path("data/weather_pool.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

class StationActivePeriodDiscoverer:
    def __init__(self):
        self.session = None
        self.processed_stations = 0
        self.total_stations = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_active_periods_table(self):
        """Create table to store station active periods"""
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS station_active_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id VARCHAR(50) UNIQUE NOT NULL,
                first_data_date DATE,
                last_data_date DATE,
                total_records INTEGER DEFAULT 0,
                data_types TEXT,
                is_active BOOLEAN DEFAULT FALSE,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (station_id) REFERENCES all_canadian_stations(station_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Active periods table created")
    
    async def discover_station_active_period(self, station_id: str) -> Optional[Dict]:
        """Discover the active period for a specific station"""
        try:
            # Strategy 1: Check for recent data (last 2 years)
            recent_data = await self.check_station_data_period(
                station_id, 
                date.today() - timedelta(days=730),  # 2 years ago
                date.today()
            )
            
            if recent_data and recent_data['total_records'] > 0:
                # Station has recent data, get full period
                full_period = await self.get_full_active_period(station_id)
                return full_period
            
            # Strategy 2: Check for historical data (last 10 years)
            historical_data = await self.check_station_data_period(
                station_id,
                date.today() - timedelta(days=3650),  # 10 years ago
                date.today() - timedelta(days=730)    # 2 years ago
            )
            
            if historical_data and historical_data['total_records'] > 0:
                # Station has historical data, get full period
                full_period = await self.get_full_active_period(station_id)
                return full_period
            
            # Strategy 3: Check for very old data (1990-2010)
            old_data = await self.check_station_data_period(
                station_id,
                date(1990, 1, 1),
                date(2010, 12, 31)
            )
            
            if old_data and old_data['total_records'] > 0:
                # Station has old data, get full period
                full_period = await self.get_full_active_period(station_id)
                return full_period
            
            # No data found
            return {
                'station_id': station_id,
                'first_data_date': None,
                'last_data_date': None,
                'total_records': 0,
                'data_types': None,
                'is_active': False
            }
            
        except Exception as e:
            print(f"    ❌ Error discovering period for {station_id}: {e}")
            return None
    
    async def check_station_data_period(self, station_id: str, start_date: date, end_date: date) -> Optional[Dict]:
        """Check if station has data in a specific period"""
        try:
            url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
            params = {
                'stationid': station_id,
                'startdate': start_date.strftime('%Y-%m-%d'),
                'enddate': end_date.strftime('%Y-%m-%d'),
                'limit': 1,  # Just check if data exists
                'sortfield': 'date',
                'sortorder': 'desc'
            }
            headers = {'token': settings.NOAA_CDO_TOKEN}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    metadata = data.get('metadata', {})
                    resultset = metadata.get('resultset', {})
                    
                    if results:
                        # Get data types from the results
                        data_types = set()
                        for result in results:
                            if result.get('datatype'):
                                data_types.add(result['datatype'])
                        
                        return {
                            'has_data': True,
                            'total_records': resultset.get('count', 0),
                            'data_types': list(data_types),
                            'latest_date': results[0].get('date')
                        }
                    else:
                        return {
                            'has_data': False,
                            'total_records': 0,
                            'data_types': [],
                            'latest_date': None
                        }
                else:
                    return None
                    
        except Exception as e:
            print(f"    ❌ Error checking data for {station_id}: {e}")
            return None
    
    async def get_full_active_period(self, station_id: str) -> Optional[Dict]:
        """Get the full active period for a station by checking multiple time ranges"""
        try:
            # Check different time periods to find the full range
            periods = [
                (date(1990, 1, 1), date(1995, 12, 31)),  # 1990s
                (date(1995, 1, 1), date(2000, 12, 31)),  # Late 1990s
                (date(2000, 1, 1), date(2005, 12, 31)),  # Early 2000s
                (date(2005, 1, 1), date(2010, 12, 31)),  # Late 2000s
                (date(2010, 1, 1), date(2015, 12, 31)),  # Early 2010s
                (date(2015, 1, 1), date(2020, 12, 31)),  # Late 2010s
                (date(2020, 1, 1), date.today())         # Recent
            ]
            
            first_date = None
            last_date = None
            total_records = 0
            all_data_types = set()
            
            for start_date, end_date in periods:
                data_info = await self.check_station_data_period(station_id, start_date, end_date)
                if data_info and data_info['has_data']:
                    if not first_date:
                        first_date = start_date
                    last_date = end_date
                    total_records += data_info['total_records']
                    all_data_types.update(data_info['data_types'])
            
            if first_date and last_date:
                return {
                    'station_id': station_id,
                    'first_data_date': first_date,
                    'last_data_date': last_date,
                    'total_records': total_records,
                    'data_types': list(all_data_types),
                    'is_active': last_date >= date.today() - timedelta(days=365)  # Active if data in last year
                }
            else:
                return {
                    'station_id': station_id,
                    'first_data_date': None,
                    'last_data_date': None,
                    'total_records': 0,
                    'data_types': [],
                    'is_active': False
                }
                
        except Exception as e:
            print(f"    ❌ Error getting full period for {station_id}: {e}")
            return None
    
    def store_active_period(self, period_info: Dict):
        """Store active period information in database"""
        if not period_info:
            return
            
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO station_active_periods 
            (station_id, first_data_date, last_data_date, total_records, data_types, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            period_info['station_id'],
            period_info['first_data_date'],
            period_info['last_data_date'],
            period_info['total_records'],
            ','.join(period_info['data_types']) if period_info['data_types'] else None,
            period_info['is_active']
        ))
        
        conn.commit()
        conn.close()
    
    async def discover_all_active_periods(self, max_stations: int = 100):
        """Discover active periods for all stations (with limit for testing)"""
        print(f"🔍 Discovering active periods for up to {max_stations} stations...")
        
        # Create the active periods table
        self.create_active_periods_table()
        
        # Get stations to process
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT station_id FROM all_canadian_stations LIMIT ?', (max_stations,))
        stations = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.total_stations = len(stations)
        print(f"📊 Processing {self.total_stations} stations...")
        
        for i, station_id in enumerate(stations):
            self.processed_stations += 1
            print(f"  🔍 Processing {station_id} ({self.processed_stations}/{self.total_stations})...")
            
            # Discover active period
            period_info = await self.discover_station_active_period(station_id)
            
            if period_info:
                # Store the information
                self.store_active_period(period_info)
                
                if period_info['is_active']:
                    print(f"    ✅ Active: {period_info['first_data_date']} to {period_info['last_data_date']} ({period_info['total_records']} records)")
                else:
                    print(f"    ⚠️  Inactive: {period_info['first_data_date']} to {period_info['last_data_date']} ({period_info['total_records']} records)")
            else:
                print(f"    ❌ No data found")
            
            # Rate limiting
            if i % 10 == 0:
                print(f"    💾 Processed {i+1} stations...")
                await asyncio.sleep(2)  # Be conservative with rate limiting
            else:
                await asyncio.sleep(0.5)
        
        print(f"✅ Completed processing {self.processed_stations} stations")
        return self.processed_stations
    
    def get_active_periods_summary(self) -> Dict:
        """Get summary of discovered active periods"""
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Total stations processed
        cursor.execute('SELECT COUNT(*) FROM station_active_periods')
        total_processed = cursor.fetchone()[0]
        
        # Active stations
        cursor.execute('SELECT COUNT(*) FROM station_active_periods WHERE is_active = 1')
        active_stations = cursor.fetchone()[0]
        
        # Date range
        cursor.execute('SELECT MIN(first_data_date), MAX(last_data_date) FROM station_active_periods WHERE first_data_date IS NOT NULL')
        date_range = cursor.fetchone()
        
        # Data types
        cursor.execute('SELECT data_types FROM station_active_periods WHERE data_types IS NOT NULL')
        all_data_types = set()
        for row in cursor.fetchall():
            if row[0]:
                all_data_types.update(row[0].split(','))
        
        conn.close()
        
        return {
            'total_processed': total_processed,
            'active_stations': active_stations,
            'inactive_stations': total_processed - active_stations,
            'date_range': {
                'first_date': date_range[0],
                'last_date': date_range[1]
            },
            'data_types': list(all_data_types)
        }

async def main():
    """Test the active period discovery system"""
    async with StationActivePeriodDiscoverer() as discoverer:
        # Test with a small number of stations first
        await discoverer.discover_all_active_periods(max_stations=20)
        
        # Show summary
        summary = discoverer.get_active_periods_summary()
        print(f"\n📊 Active Periods Summary:")
        print(f"  Total stations processed: {summary['total_processed']}")
        print(f"  Active stations: {summary['active_stations']}")
        print(f"  Inactive stations: {summary['inactive_stations']}")
        print(f"  Date range: {summary['date_range']['first_date']} to {summary['date_range']['last_date']}")
        print(f"  Data types found: {', '.join(summary['data_types'])}")

if __name__ == "__main__":
    asyncio.run(main())
