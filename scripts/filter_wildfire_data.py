#!/usr/bin/env python3
"""
Filter Canadian NOAA station data to only include wildfire-relevant parameters
"""

import os
from pathlib import Path
import shutil

def filter_dly_file(input_file, output_file, wildfire_params):
    """Filter a .dly file to only include wildfire-relevant parameters"""
    records_kept = 0
    records_total = 0
    
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                if len(line) >= 35:  # Minimum line length for valid record
                    records_total += 1
                    # Extract data type from position 17-21
                    data_type = line[17:21].strip()
                    
                    if data_type in wildfire_params:
                        outfile.write(line)
                        records_kept += 1
    
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return 0, 0
    
    return records_kept, records_total

def main():
    """Filter all Canadian station files to wildfire-relevant parameters only"""
    
    # Define wildfire-relevant parameters
    wildfire_params = {
        'TMAX',  # Maximum Temperature
        'TMIN',  # Minimum Temperature
        'PRCP',  # Precipitation
        'SNWD',  # Snow Depth
        'WESD',  # Water Equivalent of Snow Depth
        'WESF',  # Water Equivalent of Snowfall
        'WSFG',  # Peak Gust Wind Speed
        'SNOW',  # Snowfall (useful for snow depth calculations)
        'TAVG'   # Average Temperature (if available)
    }
    
    input_dir = Path("canadian_stations")
    output_dir = Path("canadian_stations_filtered")
    
    if not input_dir.exists():
        print("Canadian stations directory not found!")
        return
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print("Filtering Canadian station data for wildfire prediction...")
    print(f"Keeping only these parameters: {', '.join(sorted(wildfire_params))}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    total_records_kept = 0
    total_records_original = 0
    files_processed = 0
    files_with_data = 0
    
    # Process each station file
    for dly_file in input_dir.glob("*.dly"):
        station_id = dly_file.stem
        output_file = output_dir / f"{station_id}.dly"
        
        records_kept, records_total = filter_dly_file(dly_file, output_file, wildfire_params)
        
        total_records_kept += records_kept
        total_records_original += records_total
        files_processed += 1
        
        if records_kept > 0:
            files_with_data += 1
        
        if files_processed % 1000 == 0:
            print(f"Processed {files_processed} files...")
    
    print(f"\nFiltering complete!")
    print(f"Files processed: {files_processed}")
    print(f"Files with wildfire data: {files_with_data}")
    print(f"Total records original: {total_records_original:,}")
    print(f"Total records kept: {total_records_kept:,}")
    
    if total_records_original > 0:
        reduction_percent = ((total_records_original - total_records_kept) / total_records_original) * 100
        print(f"Records removed: {total_records_original - total_records_kept:,} ({reduction_percent:.1f}%)")
    
    # Check file sizes
    print(f"\nChecking file sizes...")
    
    # Get original size
    original_size = 0
    for file in input_dir.glob("*.dly"):
        original_size += file.stat().st_size
    
    # Get filtered size
    filtered_size = 0
    for file in output_dir.glob("*.dly"):
        filtered_size += file.stat().st_size
    
    original_size_mb = original_size / (1024 * 1024)
    filtered_size_mb = filtered_size / (1024 * 1024)
    size_reduction_mb = original_size_mb - filtered_size_mb
    size_reduction_percent = (size_reduction_mb / original_size_mb) * 100
    
    print(f"Original size: {original_size_mb:.1f} MB")
    print(f"Filtered size: {filtered_size_mb:.1f} MB")
    print(f"Size reduction: {size_reduction_mb:.1f} MB ({size_reduction_percent:.1f}%)")
    
    # Show sample of filtered files
    print(f"\nSample of filtered files:")
    sample_files = list(output_dir.glob("*.dly"))[:5]
    for file in sample_files:
        size_kb = file.stat().st_size / 1024
        print(f"  {file.name}: {size_kb:.1f} KB")

if __name__ == "__main__":
    main()
