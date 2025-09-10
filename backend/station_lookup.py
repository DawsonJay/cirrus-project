#!/usr/bin/env python3
"""
Station lookup system for efficient data collection
Provides methods to find active stations for specific time periods
"""

import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from app.database.schema_noaa import get_database_connection

class StationLookup:
    def __init__(self):
        self.conn = get_database_connection()
    
    def get_active_stations_for_period(self, start_date: date, end_date: date, 
                                     min_data_points: int = 100) -> List[Dict]:
        """Get stations that were active during a specific time period"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT 
                station_id, name, latitude, longitude, elevation, state, country,
                first_year, last_year, has_recent_data, latest_data_date, data_count
            FROM weather_stations_audit
            WHERE is_active = 1
                AND first_year <= ?
                AND last_year >= ?
                AND data_count >= ?
            ORDER BY data_count DESC, latitude, longitude
        '''
        
        cursor.execute(query, (end_date.year, start_date.year, min_data_points))
        results = cursor.fetchall()
        
        stations = []
        for row in results:
            stations.append({
                'station_id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'elevation': row[4],
                'state': row[5],
                'country': row[6],
                'first_year': row[7],
                'last_year': row[8],
                'has_recent_data': row[9],
                'latest_data_date': row[10],
                'data_count': row[11]
            })
        
        return stations
    
    def get_stations_by_region(self, min_lat: float, max_lat: float, 
                              min_lon: float, max_lon: float) -> List[Dict]:
        """Get stations within a geographic region"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT 
                station_id, name, latitude, longitude, elevation, state, country,
                first_year, last_year, has_recent_data, latest_data_date, data_count
            FROM weather_stations_audit
            WHERE is_active = 1
                AND latitude BETWEEN ? AND ?
                AND longitude BETWEEN ? AND ?
            ORDER BY data_count DESC
        '''
        
        cursor.execute(query, (min_lat, max_lat, min_lon, max_lon))
        results = cursor.fetchall()
        
        stations = []
        for row in results:
            stations.append({
                'station_id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'elevation': row[4],
                'state': row[5],
                'country': row[6],
                'first_year': row[7],
                'last_year': row[8],
                'has_recent_data': row[9],
                'latest_data_date': row[10],
                'data_count': row[11]
            })
        
        return stations
    
    def get_stations_near_location(self, lat: float, lon: float, 
                                  radius_km: float = 100) -> List[Dict]:
        """Get stations within a radius of a location"""
        # Rough conversion: 1 degree ≈ 111 km
        lat_range = radius_km / 111.0
        lon_range = radius_km / (111.0 * abs(lat) * 0.0174532925)  # Adjust for latitude
        
        return self.get_stations_by_region(
            lat - lat_range, lat + lat_range,
            lon - lon_range, lon + lon_range
        )
    
    def get_high_quality_stations(self, min_data_points: int = 1000) -> List[Dict]:
        """Get stations with high data quality (many data points)"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT 
                station_id, name, latitude, longitude, elevation, state, country,
                first_year, last_year, has_recent_data, latest_data_date, data_count
            FROM weather_stations_audit
            WHERE is_active = 1
                AND data_count >= ?
            ORDER BY data_count DESC
        '''
        
        cursor.execute(query, (min_data_points,))
        results = cursor.fetchall()
        
        stations = []
        for row in results:
            stations.append({
                'station_id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'elevation': row[4],
                'state': row[5],
                'country': row[6],
                'first_year': row[7],
                'last_year': row[8],
                'has_recent_data': row[9],
                'latest_data_date': row[10],
                'data_count': row[11]
            })
        
        return stations
    
    def get_station_info(self, station_id: str) -> Optional[Dict]:
        """Get detailed information about a specific station"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT 
                station_id, name, latitude, longitude, elevation, state, country,
                wmo_id, gsn_flag, hcn_flag, first_year, last_year,
                has_recent_data, latest_data_date, data_count, is_active
            FROM weather_stations_audit
            WHERE station_id = ?
        '''
        
        cursor.execute(query, (station_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                'station_id': result[0],
                'name': result[1],
                'latitude': result[2],
                'longitude': result[3],
                'elevation': result[4],
                'state': result[5],
                'country': result[6],
                'wmo_id': result[7],
                'gsn_flag': result[8],
                'hcn_flag': result[9],
                'first_year': result[10],
                'last_year': result[11],
                'has_recent_data': result[12],
                'latest_data_date': result[13],
                'data_count': result[14],
                'is_active': result[15]
            }
        
        return None
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the station database"""
        cursor = self.conn.cursor()
        
        # Total stations
        cursor.execute('SELECT COUNT(*) FROM weather_stations_audit')
        total_stations = cursor.fetchone()[0]
        
        # Active stations
        cursor.execute('SELECT COUNT(*) FROM weather_stations_audit WHERE is_active = 1')
        active_stations = cursor.fetchone()[0]
        
        # Stations with recent data
        cursor.execute('SELECT COUNT(*) FROM weather_stations_audit WHERE has_recent_data = 1')
        recent_data_stations = cursor.fetchone()[0]
        
        # High quality stations
        cursor.execute('SELECT COUNT(*) FROM weather_stations_audit WHERE data_count >= 1000')
        high_quality_stations = cursor.fetchone()[0]
        
        # Date range
        cursor.execute('SELECT MIN(first_year), MAX(last_year) FROM weather_stations_audit')
        date_range = cursor.fetchone()
        
        # Geographic coverage
        cursor.execute('''
            SELECT 
                MIN(latitude), MAX(latitude), 
                MIN(longitude), MAX(longitude)
            FROM weather_stations_audit
        ''')
        geo_coverage = cursor.fetchone()
        
        return {
            'total_stations': total_stations,
            'active_stations': active_stations,
            'recent_data_stations': recent_data_stations,
            'high_quality_stations': high_quality_stations,
            'date_range': {
                'first_year': date_range[0],
                'last_year': date_range[1]
            },
            'geographic_coverage': {
                'min_lat': geo_coverage[0],
                'max_lat': geo_coverage[1],
                'min_lon': geo_coverage[2],
                'max_lon': geo_coverage[3]
            }
        }
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Test the station lookup system"""
    lookup = StationLookup()
    
    print("📊 Station Database Statistics:")
    stats = lookup.get_database_stats()
    print(f"  Total stations: {stats['total_stations']}")
    print(f"  Active stations: {stats['active_stations']}")
    print(f"  Stations with recent data: {stats['recent_data_stations']}")
    print(f"  High quality stations: {stats['high_quality_stations']}")
    print(f"  Date range: {stats['date_range']['first_year']} - {stats['date_range']['last_year']}")
    print(f"  Geographic coverage: {stats['geographic_coverage']['min_lat']:.2f}°N to {stats['geographic_coverage']['max_lat']:.2f}°N")
    print(f"  Longitude: {stats['geographic_coverage']['min_lon']:.2f}°W to {stats['geographic_coverage']['max_lon']:.2f}°W")
    
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
    
    # Test getting stations near Toronto
    print(f"\n📍 Stations near Toronto (within 100km):")
    toronto_stations = lookup.get_stations_near_location(43.6532, -79.3832, 100)
    print(f"  Found {len(toronto_stations)} stations")
    
    if toronto_stations:
        print("  Top 3 stations:")
        for i, station in enumerate(toronto_stations[:3]):
            print(f"    {i+1}. {station['name']} ({station['station_id']}) - {station['data_count']} records")
    
    lookup.close()

if __name__ == "__main__":
    main()
