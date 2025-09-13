#!/usr/bin/env python3
"""
Analyze Canadian NOAA station data to identify data types and coverage
"""

import os
from pathlib import Path
from collections import defaultdict, Counter
import re

def analyze_dly_file(file_path):
    """Analyze a single .dly file and extract data type information"""
    data_types = set()
    record_count = 0
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if len(line) >= 35:  # Minimum line length for valid record
                    # Extract data type from position 17-21
                    data_type = line[17:21].strip()
                    if data_type:
                        data_types.add(data_type)
                        record_count += 1
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return data_types, record_count

def main():
    """Analyze all Canadian station files"""
    data_dir = Path("canadian_stations")
    
    if not data_dir.exists():
        print("Canadian stations directory not found!")
        return
    
    print("Analyzing Canadian NOAA station data...")
    print(f"Scanning {len(list(data_dir.glob('*.dly')))} station files...")
    
    # Track data types across all stations
    all_data_types = set()
    data_type_counts = defaultdict(int)
    station_data_types = defaultdict(set)
    total_records = 0
    stations_processed = 0
    
    # Process each station file
    for dly_file in data_dir.glob("*.dly"):
        station_id = dly_file.stem
        data_types, record_count = analyze_dly_file(dly_file)
        
        all_data_types.update(data_types)
        total_records += record_count
        stations_processed += 1
        
        # Track which stations have which data types
        for data_type in data_types:
            data_type_counts[data_type] += 1
            station_data_types[data_type].add(station_id)
        
        if stations_processed % 1000 == 0:
            print(f"Processed {stations_processed} stations...")
    
    print(f"\nAnalysis complete!")
    print(f"Stations processed: {stations_processed}")
    print(f"Total records: {total_records:,}")
    print(f"Unique data types found: {len(all_data_types)}")
    
    # Data type definitions (common NOAA GHCN-Daily parameters)
    data_type_definitions = {
        'TMAX': 'Maximum Temperature',
        'TMIN': 'Minimum Temperature', 
        'TAVG': 'Average Temperature',
        'PRCP': 'Precipitation',
        'SNOW': 'Snowfall',
        'SNWD': 'Snow Depth',
        'WESD': 'Water Equivalent of Snow Depth',
        'WESF': 'Water Equivalent of Snowfall',
        'WT01': 'Fog, ice fog, or freezing fog',
        'WT02': 'Heavy fog or heaving freezing fog',
        'WT03': 'Thunder',
        'WT04': 'Ice pellets, sleet, snow pellets, or small hail',
        'WT05': 'Hail',
        'WT06': 'Glaze or rime',
        'WT07': 'Dust, volcanic ash, blowing dust, blowing sand, or blowing obstruction',
        'WT08': 'Smoke or haze',
        'WT09': 'Blowing or drifting snow',
        'WT11': 'High or damaging winds',
        'WT13': 'Mist',
        'WT14': 'Drizzle',
        'WT15': 'Freezing drizzle',
        'WT16': 'Rain (not freezing)',
        'WT17': 'Freezing rain',
        'WT18': 'Snow or ice pellets or snow pellets',
        'WT19': 'Unknown precipitation',
        'WT21': 'Ground fog',
        'WT22': 'Ice fog or freezing fog',
        'AWND': 'Average Wind Speed',
        'WSF2': 'Fastest 2-minute wind speed',
        'WSF5': 'Fastest 5-second wind speed',
        'WSFG': 'Peak gust wind speed',
        'WDF2': 'Direction of fastest 2-minute wind',
        'WDF5': 'Direction of fastest 5-second wind',
        'WDFG': 'Direction of peak gust wind speed',
        'ACMC': 'Average cloudiness midnight to midnight',
        'ACSC': 'Average cloudiness sunrise to sunset',
        'AWDR': 'Average wind direction',
        'DAEV': 'Number of days included in the multiday evaporation total',
        'DAPR': 'Number of days included in the multiday precipitation total',
        'DASF': 'Number of days included in the multiday snowfall total',
        'DATN': 'Number of days included in the multiday minimum temperature',
        'DATX': 'Number of days included in the multiday maximum temperature',
        'DAWM': 'Number of days included in the multiday wind movement',
        'DWPR': 'Number of days with non-zero precipitation included in multiday precipitation total',
        'EVAP': 'Evaporation of water from evaporation pan',
        'FMTM': 'Time of fastest mile or fastest 1-minute wind',
        'FRGB': 'Base of frozen ground layer',
        'FRGT': 'Top of frozen ground layer',
        'FRTH': 'Thickness of frozen ground layer',
        'GAHT': 'Difference between river and gauge height',
        'MDEV': 'Multiday evaporation total',
        'MDPR': 'Multiday precipitation total',
        'MDSF': 'Multiday snowfall total',
        'MDTN': 'Multiday minimum temperature',
        'MDTX': 'Multiday maximum temperature',
        'MDWM': 'Multiday wind movement',
        'MNPN': 'Minimum temperature of water in an evaporation pan',
        'MXPN': 'Maximum temperature of water in an evaporation pan',
        'PGTM': 'Peak gust time',
        'PSUN': 'Daily percent of possible sunshine',
        'SN32': 'Minimum soil temperature with 3.2 cm (1.25 in) of the surface',
        'SN52': 'Minimum soil temperature with 5.2 cm (2.05 in) of the surface',
        'SN72': 'Minimum soil temperature with 7.2 cm (2.83 in) of the surface',
        'SN92': 'Minimum soil temperature with 9.2 cm (3.62 in) of the surface',
        'SX32': 'Maximum soil temperature with 3.2 cm (1.25 in) of the surface',
        'SX52': 'Maximum soil temperature with 5.2 cm (2.05 in) of the surface',
        'SX72': 'Maximum soil temperature with 7.2 cm (2.83 in) of the surface',
        'SX92': 'Maximum soil temperature with 9.2 cm (3.62 in) of the surface',
        'THIC': 'Thickness of ice on water',
        'TOBS': 'Temperature at the time of observation',
        'TSUN': 'Total sunshine for the period',
        'WDMV': '24-hour wind movement',
        'WESD': 'Water equivalent of snow on the ground',
        'WESF': 'Water equivalent of snowfall'
    }
    
    print(f"\n{'Data Type':<8} {'Stations':<10} {'Description':<50}")
    print("=" * 70)
    
    # Sort by station count (most common first)
    sorted_types = sorted(data_type_counts.items(), key=lambda x: x[1], reverse=True)
    
    for data_type, station_count in sorted_types:
        description = data_type_definitions.get(data_type, 'Unknown parameter')
        percentage = (station_count / stations_processed) * 100
        print(f"{data_type:<8} {station_count:<10} ({percentage:5.1f}%) {description}")
    
    # Wildfire-relevant parameters
    wildfire_params = ['TMAX', 'TMIN', 'PRCP', 'SNWD', 'WESD', 'WESF', 'AWND', 'WSF2', 'WSFG']
    print(f"\n{'Wildfire-Relevant Parameters':<50}")
    print("=" * 50)
    for param in wildfire_params:
        if param in data_type_counts:
            station_count = data_type_counts[param]
            percentage = (station_count / stations_processed) * 100
            description = data_type_definitions.get(param, 'Unknown')
            print(f"{param:<8} {station_count:<10} ({percentage:5.1f}%) {description}")
    
    print(f"\nSummary:")
    print(f"- Total stations: {stations_processed:,}")
    print(f"- Total records: {total_records:,}")
    print(f"- Unique data types: {len(all_data_types)}")
    print(f"- Wildfire-relevant parameters available: {len([p for p in wildfire_params if p in data_type_counts])}")

if __name__ == "__main__":
    main()
