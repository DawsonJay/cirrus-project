#!/usr/bin/env python3
"""
Extract historical weather data from compressed archive
"""
import os
import tarfile
import sys
from pathlib import Path

def extract_historical_data():
    """Extract historical data from compressed archive"""
    # Paths
    compressed_file = Path("historical_data.tar.gz")
    extract_to = Path("raw_historical_station_data")
    
    print("🗜️  Extracting historical weather data...")
    
    # Check if compressed file exists
    if not compressed_file.exists():
        print(f"❌ Compressed file not found: {compressed_file}")
        return False
    
    # Check if already extracted
    if extract_to.exists():
        print(f"✅ Data already extracted: {extract_to}")
        return True
    
    try:
        # Extract the compressed file
        with tarfile.open(compressed_file, 'r:gz') as tar:
            tar.extractall()
        
        print(f"✅ Successfully extracted data to: {extract_to}")
        
        # Verify extraction
        if extract_to.exists():
            # Count files
            dly_files = list(extract_to.glob("**/*.dly"))
            print(f"📊 Extracted {len(dly_files)} weather station files")
            return True
        else:
            print("❌ Extraction failed - target directory not created")
            return False
            
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return False

def cleanup_compressed_data():
    """Remove compressed file to save space after extraction"""
    compressed_file = Path("historical_data.tar.gz")
    
    if compressed_file.exists():
        try:
            compressed_file.unlink()
            print("🗑️  Removed compressed file to save space")
            return True
        except Exception as e:
            print(f"⚠️  Could not remove compressed file: {e}")
            return False
    else:
        print("ℹ️  No compressed file to remove")
        return True

if __name__ == "__main__":
    print("🌤️  Historical Data Extraction")
    print("=" * 40)
    
    # Extract data
    if extract_historical_data():
        print("✅ Data extraction completed successfully")
        
        # Ask if we should clean up (for now, let's keep it for debugging)
        # cleanup_compressed_data()
        
        sys.exit(0)
    else:
        print("❌ Data extraction failed")
        sys.exit(1)