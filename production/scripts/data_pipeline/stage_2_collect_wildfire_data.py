#!/usr/bin/env python3
"""
Collect Canadian Wildfire Data
=============================

Downloads and filters Canadian wildfire data from CWFIS DataMart.
Focuses on polygon data for accurate fire perimeter representation.

Data Source: Canadian Forest Service CWFIS DataMart
Spatial Bounds: All of Canada below northern territories
Temporal Bounds: 2022-2025 (3+ years based on current date)
"""

import os
import sys
import requests
import zipfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
import geopandas as gpd
import pandas as pd
import warnings

# Suppress fiona warnings
warnings.filterwarnings('ignore', category=UserWarning, module='fiona')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../production/logs/wildfire_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WildfireDataCollector:
    """Collects and processes Canadian wildfire data from CWFIS DataMart"""
    
    def __init__(self, data_dir="../../data"):
        self.data_dir = Path(data_dir)
        self.raw_data_dir = self.data_dir / "raw_data"
        self.wildfire_data_dir = self.raw_data_dir / "wildfire_data"
        
        # CWFIS DataMart URLs for wildfire data
        self.wildfire_urls = {
            "nfdb_polygon": "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_poly.zip",
            "nfdb_polygon_large": "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_poly_large_fires.zip",
            "nfdb_point": "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point.zip",
            "nfdb_point_large": "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_large_fires.zip"
        }
        
        # Spatial bounds (same as weather data)
        self.spatial_bounds = {
            'min_lat': 41.75,   # Southern boundary
            'max_lat': 60.0,    # Northern boundary (below territories)
            'min_lon': -137.72, # Western boundary
            'max_lon': -52.67   # Eastern boundary
        }
        
        # Temporal bounds (3+ years based on current date)
        current_year = datetime.now().year
        self.temporal_bounds = {
            'start_year': current_year - 3,  # 2022
            'end_year': current_year         # 2025
        }
        
        logger.info(f"🔥 Wildfire Data Collector initialized")
        logger.info(f"   Spatial bounds: {self.spatial_bounds['min_lat']:.2f}°N to {self.spatial_bounds['max_lat']:.2f}°N")
        logger.info(f"   Longitude: {self.spatial_bounds['min_lon']:.2f}°W to {self.spatial_bounds['max_lon']:.2f}°W")
        logger.info(f"   Temporal bounds: {self.temporal_bounds['start_year']} to {self.temporal_bounds['end_year']} ({self.temporal_bounds['end_year'] - self.temporal_bounds['start_year'] + 1} years)")
    
    def clear_wildfire_data_folder(self):
        """Clear the wildfire data folder for a clean start"""
        logger.info("🧹 Clearing wildfire data folder...")
        
        if self.wildfire_data_dir.exists():
            shutil.rmtree(self.wildfire_data_dir)
            logger.info("✅ Wildfire data folder cleared")
        else:
            logger.info("📁 Wildfire data folder doesn't exist, creating...")
        
        self.wildfire_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Wildfire data folder ready")
    
    def download_wildfire_datasets(self):
        """Download wildfire datasets from CWFIS DataMart"""
        logger.info("📥 Downloading wildfire datasets from CWFIS DataMart...")
        
        downloaded_files = []
        
        for dataset_name, url in self.wildfire_urls.items():
            logger.info(f"   📦 Downloading {dataset_name}...")
            logger.info(f"      URL: {url}")
            
            try:
                # Download the file
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Save to file
                zip_file = self.wildfire_data_dir / f"{dataset_name}.zip"
                with open(zip_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = zip_file.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"      ✅ Downloaded: {file_size:.1f} MB")
                
                # Extract the zip file
                extract_dir = self.wildfire_data_dir / dataset_name
                extract_dir.mkdir(exist_ok=True)
                
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                logger.info(f"      ✅ Extracted to: {extract_dir.name}")
                downloaded_files.append(extract_dir)
                
                # Remove zip file to save space
                zip_file.unlink()
                logger.info(f"      🗑️ Removed zip file")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"      ❌ Error downloading {dataset_name}: {e}")
                continue
            except zipfile.BadZipFile as e:
                logger.error(f"      ❌ Error extracting {dataset_name}: {e}")
                continue
            except Exception as e:
                logger.error(f"      ❌ Unexpected error with {dataset_name}: {e}")
                continue
        
        logger.info(f"✅ Downloaded {len(downloaded_files)} datasets successfully")
        return downloaded_files
    
    def _convert_shapefile_to_csv(self, shapefile_path, csv_path):
        """
        Convert shapefile to CSV using ogr2ogr to bypass fiona date validation issues.
        This is much more reliable than trying to handle fiona errors.
        """
        logger.info(f"   🔄 Converting {shapefile_path.name} to CSV...")
        
        try:
            import subprocess
            
            # Use ogr2ogr to convert shapefile to CSV
            # This bypasses all fiona date validation issues
            cmd = [
                'ogr2ogr',
                '-f', 'CSV',
                str(csv_path),
                str(shapefile_path),
                '-lco', 'GEOMETRY=AS_WKT'  # Include geometry as WKT
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"   ✅ Successfully converted to CSV: {csv_path.name}")
                return True
            else:
                logger.error(f"   ❌ ogr2ogr failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"   ❌ ogr2ogr timed out after 5 minutes")
            return False
        except FileNotFoundError:
            logger.error(f"   ❌ ogr2ogr not found. Please install GDAL: sudo apt-get install gdal-bin")
            return False
        except Exception as e:
            logger.error(f"   ❌ Error converting shapefile to CSV: {e}")
            return False
    
    def _load_csv_as_geodataframe(self, csv_path):
        """
        Load CSV file and convert it back to a GeoDataFrame.
        This approach bypasses fiona date validation issues entirely.
        """
        logger.info(f"   📊 Loading CSV and converting to GeoDataFrame...")
        
        try:
            import pandas as pd
            from shapely import wkt
            
            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"   📊 Loaded {len(df)} records from CSV")
            
            # Convert WKT geometry to shapely geometry
            if 'WKT' in df.columns:
                df['geometry'] = df['WKT'].apply(wkt.loads)
                df = df.drop('WKT', axis=1)
            else:
                logger.error(f"   ❌ No WKT column found in CSV")
                return None
            
            # Convert to GeoDataFrame
            gdf = gpd.GeoDataFrame(df, geometry='geometry')
            
            # Filter out invalid records
            # Check if this is point data (has LATITUDE/LONGITUDE) or polygon data
            if 'LATITUDE' in gdf.columns and 'LONGITUDE' in gdf.columns:
                # Point data - filter by coordinates and dates
                invalid_dates = (
                    (gdf['YEAR'] == 0) | (gdf['YEAR'] == -9999) |
                    (gdf['MONTH'] == 0) | (gdf['MONTH'] == -9999) |
                    (gdf['DAY'] == 0) | (gdf['DAY'] == -9999) |
                    (gdf['LATITUDE'].isna()) | (gdf['LONGITUDE'].isna())
                )
            else:
                # Polygon data - only filter by dates
                invalid_dates = (
                    (gdf['YEAR'] == 0) | (gdf['YEAR'] == -9999) |
                    (gdf['MONTH'] == 0) | (gdf['MONTH'] == -9999) |
                    (gdf['DAY'] == 0) | (gdf['DAY'] == -9999)
                )
            
            invalid_count = invalid_dates.sum()
            if invalid_count > 0:
                logger.info(f"   ⚠️ Found {invalid_count} invalid records, filtering them out")
                gdf = gdf[~invalid_dates].copy()
            
            logger.info(f"   ✅ Successfully created GeoDataFrame with {len(gdf)} valid records")
            return gdf
            
        except Exception as e:
            logger.error(f"   ❌ Error loading CSV as GeoDataFrame: {e}")
            return None
    
    def filter_wildfire_data_spatial(self, shapefile_path, output_path):
        """Filter wildfire data by spatial bounds using CSV conversion approach"""
        logger.info(f"🌍 Filtering {shapefile_path.name} by spatial bounds...")
        
        try:
            # Convert shapefile to CSV first to bypass fiona issues
            csv_path = shapefile_path.parent / f"{shapefile_path.stem}_temp.csv"
            
            if not self._convert_shapefile_to_csv(shapefile_path, csv_path):
                logger.error(f"   ❌ Failed to convert {shapefile_path.name} to CSV")
                return False
            
            # Load CSV as GeoDataFrame
            gdf = self._load_csv_as_geodataframe(csv_path)
            if gdf is None or len(gdf) == 0:
                logger.warning(f"   ⚠️ No valid records loaded from {shapefile_path.name}")
                # Clean up temp CSV
                if csv_path.exists():
                    csv_path.unlink()
                return False
            
            logger.info(f"   📊 Loaded {len(gdf)} valid records")
            
            # Apply spatial filter
            if 'LATITUDE' in gdf.columns and 'LONGITUDE' in gdf.columns:
                # Point data - filter by coordinates
                spatial_filter = (
                    (gdf['LATITUDE'] >= self.spatial_bounds['min_lat']) &
                    (gdf['LATITUDE'] <= self.spatial_bounds['max_lat']) &
                    (gdf['LONGITUDE'] >= self.spatial_bounds['min_lon']) &
                    (gdf['LONGITUDE'] <= self.spatial_bounds['max_lon'])
                )
                gdf_filtered = gdf[spatial_filter].copy()
            else:
                # Polygon data - use spatial intersection with bounding box
                from shapely.geometry import box
                
                # Create bounding box for Canadian bounds
                bbox = box(
                    self.spatial_bounds['min_lon'],  # west
                    self.spatial_bounds['min_lat'],  # south
                    self.spatial_bounds['max_lon'],  # east
                    self.spatial_bounds['max_lat']   # north
                )
                
                # Filter polygons that intersect with the bounding box
                spatial_filter = gdf.geometry.intersects(bbox)
                gdf_filtered = gdf[spatial_filter].copy()
            records_kept = len(gdf_filtered)
            records_removed = len(gdf) - records_kept
            
            logger.info(f"   ✅ Kept {records_kept} records, removed {records_removed} outside bounds")
            
            if records_kept > 0:
                # Save filtered data
                gdf_filtered.to_file(output_path, driver='ESRI Shapefile')
                logger.info(f"   💾 Saved filtered data to {output_path.name}")
                
                # Clean up temp CSV
                if csv_path.exists():
                    csv_path.unlink()
                return True
            else:
                logger.warning(f"   ⚠️ No records within spatial bounds")
                # Clean up temp CSV
                if csv_path.exists():
                    csv_path.unlink()
                return False
                
        except Exception as e:
            logger.error(f"   ❌ Error filtering {shapefile_path.name} spatially: {e}")
            # Clean up temp CSV if it exists
            csv_path = shapefile_path.parent / f"{shapefile_path.stem}_temp.csv"
            if csv_path.exists():
                csv_path.unlink()
            return False
    
    def filter_wildfire_data_temporal(self, shapefile_path, output_path):
        """Filter wildfire data by temporal bounds using CSV conversion approach"""
        logger.info(f"📅 Filtering {shapefile_path.name} by temporal bounds...")
        
        try:
            # Convert shapefile to CSV first to bypass fiona issues
            csv_path = shapefile_path.parent / f"{shapefile_path.stem}_temp.csv"
            
            if not self._convert_shapefile_to_csv(shapefile_path, csv_path):
                logger.error(f"   ❌ Failed to convert {shapefile_path.name} to CSV")
                return False
            
            # Load CSV as GeoDataFrame
            gdf = self._load_csv_as_geodataframe(csv_path)
            if gdf is None or len(gdf) == 0:
                logger.warning(f"   ⚠️ No valid records loaded from {shapefile_path.name}")
                # Clean up temp CSV
                if csv_path.exists():
                    csv_path.unlink()
                return False
            
            logger.info(f"   📊 Loaded {len(gdf)} valid records")
            
            # Apply temporal filter
            temporal_filter = (
                (gdf['YEAR'] >= self.temporal_bounds['start_year']) &
                (gdf['YEAR'] <= self.temporal_bounds['end_year'])
            )
            
            gdf_filtered = gdf[temporal_filter].copy()
            records_kept = len(gdf_filtered)
            records_removed = len(gdf) - records_kept
            
            logger.info(f"   ✅ Kept {records_kept} records, removed {records_removed} outside temporal bounds")
            
            if records_kept > 0:
                # Save filtered data
                gdf_filtered.to_file(output_path, driver='ESRI Shapefile')
                logger.info(f"   💾 Saved filtered data to {output_path.name}")
                
                # Clean up temp CSV
                if csv_path.exists():
                    csv_path.unlink()
                return True
            else:
                logger.warning(f"   ⚠️ No records within temporal bounds")
                # Clean up temp CSV
                if csv_path.exists():
                    csv_path.unlink()
                return False
                
        except Exception as e:
            logger.error(f"   ❌ Error filtering {shapefile_path.name} temporally: {e}")
            # Clean up temp CSV if it exists
            csv_path = shapefile_path.parent / f"{shapefile_path.stem}_temp.csv"
            if csv_path.exists():
                csv_path.unlink()
            return False
    
    def process_wildfire_datasets(self, downloaded_dirs):
        """Process downloaded wildfire datasets with spatial and temporal filtering"""
        logger.info("🔄 Processing wildfire datasets...")
        
        processed_files = []
        
        for dataset_dir in downloaded_dirs:
            logger.info(f"📁 Processing {dataset_dir.name}...")
            
            # Find shapefiles in the dataset
            shapefiles = list(dataset_dir.glob("*.shp"))
            
            if not shapefiles:
                logger.warning(f"   ⚠️ No shapefiles found in {dataset_dir.name}")
                continue
            
            for shapefile in shapefiles:
                logger.info(f"   🔍 Processing {shapefile.name}...")
                
                # Create filtered output directory
                filtered_dir = self.wildfire_data_dir / "filtered" / dataset_dir.name
                filtered_dir.mkdir(parents=True, exist_ok=True)
                
                # Apply spatial filtering first
                spatial_output = filtered_dir / f"spatial_{shapefile.name}"
                if self.filter_wildfire_data_spatial(shapefile, spatial_output):
                    # Apply temporal filtering to spatially filtered data
                    temporal_output = filtered_dir / f"filtered_{shapefile.name}"
                    if self.filter_wildfire_data_temporal(spatial_output, temporal_output):
                        processed_files.append(temporal_output)
                        logger.info(f"   ✅ Successfully processed {shapefile.name}")
                    else:
                        logger.warning(f"   ⚠️ No temporal data for {shapefile.name}")
                else:
                    logger.warning(f"   ⚠️ No spatial data for {shapefile.name}")
        
        logger.info(f"✅ Processed {len(processed_files)} wildfire files")
        return processed_files
    
    def verify_final_structure(self, processed_files):
        """Verify the final data structure"""
        logger.info("🔍 Verifying final wildfire data structure...")
        
        # Check filtered directory
        filtered_dir = self.wildfire_data_dir / "filtered"
        if filtered_dir.exists():
            subdirs = [d for d in filtered_dir.iterdir() if d.is_dir()]
            logger.info(f"   📁 Filtered datasets: {len(subdirs)}")
            
            for subdir in subdirs:
                shapefiles = list(subdir.glob("*.shp"))
                logger.info(f"      {subdir.name}: {len(shapefiles)} shapefiles")
        
        # Check processed files
        logger.info(f"   📊 Total processed files: {len(processed_files)}")
        
        # Sample verification
        if processed_files:
            sample_file = processed_files[0]
            try:
                # Convert to CSV and load
                csv_path = sample_file.parent / f"{sample_file.stem}_verify_temp.csv"
                if self._convert_shapefile_to_csv(sample_file, csv_path):
                    gdf = self._load_csv_as_geodataframe(csv_path)
                    if gdf is not None and len(gdf) > 0:
                        logger.info(f"   📋 Sample file: {sample_file.name}")
                        logger.info(f"      Records: {len(gdf)}")
                        logger.info(f"      Columns: {list(gdf.columns)}")
                        
                        # Check date range
                        if 'YEAR' in gdf.columns:
                            year_range = f"{gdf['YEAR'].min()}-{gdf['YEAR'].max()}"
                            logger.info(f"      Year range: {year_range}")
                        
                        # Check spatial bounds
                        if 'LATITUDE' in gdf.columns and 'LONGITUDE' in gdf.columns:
                            # Point data
                            lat_range = f"{gdf['LATITUDE'].min():.2f}°N to {gdf['LATITUDE'].max():.2f}°N"
                            lon_range = f"{gdf['LONGITUDE'].min():.2f}°W to {gdf['LONGITUDE'].max():.2f}°W"
                            logger.info(f"      Latitude: {lat_range}")
                            logger.info(f"      Longitude: {lon_range}")
                        else:
                            # Polygon data - show geometry bounds
                            bounds = gdf.geometry.bounds
                            lat_range = f"{bounds['miny'].min():.2f}°N to {bounds['maxy'].max():.2f}°N"
                            lon_range = f"{bounds['minx'].min():.2f}°W to {bounds['maxx'].max():.2f}°W"
                            logger.info(f"      Latitude: {lat_range}")
                            logger.info(f"      Longitude: {lon_range}")
                            logger.info(f"      Geometry type: {gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else 'Unknown'}")
                    else:
                        logger.warning(f"   ⚠️ Could not load sample file: {sample_file.name}")
                    
                    # Clean up temp CSV
                    if csv_path.exists():
                        csv_path.unlink()
                else:
                    logger.error(f"   ❌ Failed to convert sample file to CSV")
                
            except Exception as e:
                logger.error(f"   ❌ Error verifying sample file: {e}")
        
        logger.info("✅ Final structure verification complete")
    
    def convert_final_data_to_csv(self, processed_files):
        """Convert final filtered shapefiles to CSV and clean up intermediate files"""
        logger.info("🔄 Converting final data to CSV format...")
        
        try:
            csv_dir = self.wildfire_data_dir / "final_csv"
            csv_dir.mkdir(exist_ok=True)
            
            converted_files = []
            
            for shapefile_path in processed_files:
                try:
                    # Convert shapefile to CSV
                    csv_filename = f"{shapefile_path.stem}.csv"
                    csv_path = csv_dir / csv_filename
                    
                    logger.info(f"   📄 Converting {shapefile_path.name} to CSV...")
                    
                    if self._convert_shapefile_to_csv(shapefile_path, csv_path):
                        # Load and clean the CSV data
                        gdf = self._load_csv_as_geodataframe(csv_path)
                        if gdf is not None and len(gdf) > 0:
                            # Save CSV with geometry column preserved as WKT
                            # Convert geometry to WKT for database compatibility
                            gdf_copy = gdf.copy()
                            gdf_copy['geometry_wkt'] = gdf_copy['geometry'].apply(lambda x: x.wkt if x is not None else None)
                            # Drop the shapely geometry column but keep WKT
                            clean_df = gdf_copy.drop('geometry', axis=1)
                            clean_df.to_csv(csv_path, index=False)
                            
                            logger.info(f"      ✅ Saved {len(clean_df)} records to {csv_filename}")
                            converted_files.append(csv_path)
                        else:
                            logger.warning(f"      ⚠️ No valid data in {shapefile_path.name}")
                            csv_path.unlink()  # Remove empty CSV
                    else:
                        logger.error(f"      ❌ Failed to convert {shapefile_path.name}")
                        
                except Exception as e:
                    logger.error(f"      ❌ Error converting {shapefile_path.name}: {e}")
                    continue
            
            logger.info(f"✅ Converted {len(converted_files)} files to CSV format")
            return converted_files
            
        except Exception as e:
            logger.error(f"❌ Error converting to CSV: {e}")
            return []
    
    def cleanup_intermediate_files(self):
        """Remove all intermediate files, keeping only final CSV files"""
        logger.info("🧹 Cleaning up intermediate files...")
        
        try:
            # Remove all zip files
            zip_files = list(self.wildfire_data_dir.glob("*.zip"))
            for zip_file in zip_files:
                zip_file.unlink()
                logger.info(f"   🗑️ Removed {zip_file.name}")
            
            # Remove all shapefile directories except final_csv
            for item in self.wildfire_data_dir.iterdir():
                if item.is_dir() and item.name != "final_csv":
                    import shutil
                    shutil.rmtree(item)
                    logger.info(f"   🗑️ Removed directory {item.name}")
            
            # Remove any remaining temp CSV files
            temp_csv_files = list(self.wildfire_data_dir.rglob("*_temp.csv"))
            for temp_file in temp_csv_files:
                temp_file.unlink()
                logger.info(f"   🗑️ Removed temp file {temp_file.name}")
            
            logger.info("✅ Cleanup completed - only final CSV files remain")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            return False
    
    def run_full_collection(self, test_mode=False):
        """Run the complete wildfire data collection process"""
        logger.info("🔥 Starting Canadian Wildfire Data Collection")
        logger.info("=" * 60)
        
        if test_mode:
            logger.info("🧪 TEST MODE - Skipping download, testing filtering only")
        logger.info("=" * 60)
        
        try:
            # Step 1: Clear wildfire data folder
            self.clear_wildfire_data_folder()
            
            if not test_mode:
                # Step 2: Download wildfire datasets
                downloaded_dirs = self.download_wildfire_datasets()
                if not downloaded_dirs:
                    raise Exception("No datasets downloaded successfully")
            else:
                # Test mode - use existing data if available
                downloaded_dirs = [d for d in self.wildfire_data_dir.iterdir() if d.is_dir() and d.name != "filtered"]
                if not downloaded_dirs:
                    logger.warning("⚠️ No existing data found for test mode")
                    return False
            
            # Step 3: Process datasets with filtering
            processed_files = self.process_wildfire_datasets(downloaded_dirs)
            
            # Step 4: Verify final structure
            self.verify_final_structure(processed_files)
            
            # Convert final data to CSV format
            csv_files = self.convert_final_data_to_csv(processed_files)
            
            # Clean up intermediate files
            self.cleanup_intermediate_files()
            
            logger.info("🎉 Wildfire data collection completed successfully!")
            logger.info("=" * 60)
            logger.info("Final structure:")
            logger.info(f"   📁 {self.wildfire_data_dir}/final_csv - Clean CSV files ({len(csv_files)} files)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Wildfire data collection failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def main():
    """Main function to run wildfire data collection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect Canadian Wildfire Data')
    parser.add_argument('--test', action='store_true', help='Test mode - skip download, test filtering only')
    args = parser.parse_args()
    
    collector = WildfireDataCollector()
    success = collector.run_full_collection(test_mode=args.test)
    
    if success:
        print("✅ Wildfire data collection completed successfully!")
    else:
        print("❌ Wildfire data collection failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
