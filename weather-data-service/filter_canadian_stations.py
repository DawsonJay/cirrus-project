#!/usr/bin/env python3
"""
Filter Canadian stations from unfiltered_stations.json and save to canadian_stations.json
"""

import json

def filter_canadian_stations():
    """Filter out just the Canadian stations"""
    print('🇨🇦 Filtering Canadian stations from unfiltered data')
    print('=' * 60)
    
    # Load unfiltered stations
    with open('unfiltered_stations.json', 'r') as f:
        all_stations = json.load(f)
    
    print(f'📊 Total unfiltered stations: {len(all_stations)}')
    
    # Filter for Canadian stations (those ending with ", CA")
    canadian_stations = []
    for station in all_stations:
        name = station.get('name', '')
        if name.endswith(', CA'):
            canadian_stations.append(station)
    
    print(f'🇨🇦 Canadian stations found: {len(canadian_stations)}')
    
    # Save Canadian stations
    with open('canadian_stations.json', 'w') as f:
        json.dump(canadian_stations, f, indent=2)
    
    print(f'💾 Saved {len(canadian_stations)} Canadian stations to canadian_stations.json')
    
    # Show some sample Canadian stations
    print('\n📋 Sample Canadian stations:')
    for i, station in enumerate(canadian_stations[:10]):
        name = station.get('name', 'Unknown')
        station_id = station.get('id', 'Unknown')
        print(f'  {i+1:2d}: {name} (ID: {station_id})')
    
    return canadian_stations

if __name__ == "__main__":
    canadian_stations = filter_canadian_stations()
