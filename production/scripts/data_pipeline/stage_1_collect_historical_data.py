#!/usr/bin/env python3
"""
Historical Weather Data Collection
=================================
Downloads and processes NOAA GHCN-Daily historical data for Canadian stations.

Process:
1. Clear raw_data folder
2. Download GHCN-Daily tar file from NOAA FTP
3. Extract tar file
4. Delete original tar and version files
5. Filter for Canadian stations (spatial bounds)
6. Filter for temporal bounds (3 full years)
7. Rename folder to canadian_stations
8. Download metadata files (inventory.txt, stations.txt)
9. Organize final structure

Spatial bounds: Canada below northern territories (41.75°N to 60.0°N, -137.72°W to -52.67°W)
Temporal bounds: 3 full years from current year (e.g., 2022-2025)
"""

import os
import sys
import shutil
import tarfile
import logging
import requests
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../production/logs/historical_data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdaptiveSystemMonitor:
    """Adaptive system monitoring for different hardware configurations"""
    
    def __init__(self, max_memory_percent=80, max_memory_gb=None):
        self.max_memory_percent = max_memory_percent
        self.max_memory_gb = max_memory_gb
        self.total_memory_gb = psutil.virtual_memory().total / (1024**3)
        self.cpu_count = psutil.cpu_count()
        
        # Detect hardware type and capabilities
        self.hardware_type = self._detect_hardware_type()
        self.optimal_settings = self._get_optimal_settings()
        
        if self.max_memory_gb is None:
            self.max_memory_gb = self.total_memory_gb * (max_memory_percent / 100)
        
        logger.info(f"🔧 Adaptive System Monitor initialized:")
        logger.info(f"   Hardware type: {self.hardware_type}")
        logger.info(f"   Total system memory: {self.total_memory_gb:.1f} GB")
        logger.info(f"   CPU cores: {self.cpu_count}")
        logger.info(f"   Max memory limit: {self.max_memory_gb:.1f} GB ({max_memory_percent}%)")
        logger.info(f"   Optimal settings: {self.optimal_settings}")
    
    def _detect_hardware_type(self):
        """Detect the type of hardware we're running on"""
        memory_gb = self.total_memory_gb
        cpu_count = self.cpu_count
        
        # Raspberry Pi detection
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                    return 'raspberry_pi'
        except:
            pass
        
        # Hardware classification based on specs
        if memory_gb <= 1:
            return 'raspberry_pi'  # Raspberry Pi 3B (1GB)
        elif memory_gb <= 4:
            return 'low_end'  # Old laptops, small VMs
        elif memory_gb <= 8:
            return 'mid_range'  # Modern laptops, small servers
        elif memory_gb <= 32:
            return 'high_end'  # Workstations, servers
        else:
            return 'enterprise'  # High-end servers, workstations
    
    def _get_optimal_settings(self):
        """Get optimal settings based on hardware type"""
        settings = {
            'raspberry_pi': {
                'max_processes': 1,  # Single process for stability
                'files_per_batch': 5,  # Very small batches
                'memory_percent': 60,  # Very conservative memory usage
                'description': 'Raspberry Pi - Ultra-conservative settings for 1GB RAM'
            },
            'low_end': {
                'max_processes': 2,
                'files_per_batch': 10,
                'memory_percent': 70,
                'description': 'Low-end hardware - Small batches, limited parallelism'
            },
            'mid_range': {
                'max_processes': 3,
                'files_per_batch': 20,
                'memory_percent': 75,
                'description': 'Mid-range hardware - Balanced performance and safety'
            },
            'high_end': {
                'max_processes': 4,
                'files_per_batch': 50,
                'memory_percent': 80,
                'description': 'High-end hardware - Maximum performance'
            },
            'enterprise': {
                'max_processes': min(8, self.cpu_count),
                'files_per_batch': 100,
                'memory_percent': 85,
                'description': 'Enterprise hardware - Maximum parallelism'
            }
        }
        
        return settings.get(self.hardware_type, settings['mid_range'])
    
    def get_optimal_processes(self):
        """Get optimal number of processes for this hardware"""
        return self.optimal_settings['max_processes']
    
    def get_optimal_files_per_batch(self):
        """Get optimal number of files per batch for this hardware"""
        return self.optimal_settings['files_per_batch']
    
    def get_optimal_memory_percent(self):
        """Get optimal memory usage percentage for this hardware"""
        return self.optimal_settings['memory_percent']
    
    def get_memory_usage(self):
        """Get current memory usage"""
        memory = psutil.virtual_memory()
        return {
            'used_gb': memory.used / (1024**3),
            'available_gb': memory.available / (1024**3),
            'percent_used': memory.percent,
            'free_gb': memory.free / (1024**3)
        }
    
    def can_allocate_memory(self, requested_gb):
        """Check if we can safely allocate requested memory"""
        current = self.get_memory_usage()
        projected_usage = current['used_gb'] + requested_gb
        
        if projected_usage > self.max_memory_gb:
            logger.warning(f"⚠️ Memory allocation would exceed limit:")
            logger.warning(f"   Current: {current['used_gb']:.1f} GB")
            logger.warning(f"   Requested: {requested_gb:.1f} GB")
            logger.warning(f"   Projected: {projected_usage:.1f} GB")
            logger.warning(f"   Limit: {self.max_memory_gb:.1f} GB")
            return False
        
        return True
    
    def log_memory_status(self):
        """Log current memory status"""
        memory = self.get_memory_usage()
        logger.info(f"🧠 Memory Status: {memory['used_gb']:.1f} GB used, {memory['available_gb']:.1f} GB available ({memory['percent_used']:.1f}%)")

class HistoricalDataCollector:
    """Collects and processes NOAA GHCN-Daily historical weather data"""
    
    def __init__(self, data_dir="../../data"):
        self.data_dir = Path(data_dir)
        self.raw_data_dir = self.data_dir / "raw_data"
        self.historical_noaa_dir = self.raw_data_dir / "historical_noaa_data"
        
        # Adaptive system monitoring
        self.system_monitor = AdaptiveSystemMonitor()
        self.canadian_stations_dir = self.historical_noaa_dir / "canadian_stations"
        self.metadata_dir = self.historical_noaa_dir / "metadata"
        
        # NOAA FTP configuration
        self.ftp_base = "ftp.ncdc.noaa.gov"
        self.ftp_path = "/pub/data/ghcn/daily"
        self.tar_filename = "ghcnd_all.tar.gz"
        
        # Temporal bounds (3 complete years)
        current_year = datetime.now().year
        self.temporal_bounds = {
            'start_year': current_year - 3,  # 2022
            'end_year': current_year         # 2025
        }
        
        # Spatial bounds for Canada below northern territories
        self.spatial_bounds = {
            'min_lat': 41.75,
            'max_lat': 60.0,
            'min_lon': -137.72,
            'max_lon': -52.67
        }
        
        # Temporal bounds (3 full years from current year)
        current_year = datetime.now().year
        self.start_year = current_year - 3
        self.end_year = current_year
        
        logger.info(f"🌍 Historical Data Collector initialized")
        logger.info(f"   Spatial bounds: {self.spatial_bounds['min_lat']:.2f}°N to {self.spatial_bounds['max_lat']:.2f}°N")
        logger.info(f"   Longitude: {self.spatial_bounds['min_lon']:.2f}°W to {self.spatial_bounds['max_lon']:.2f}°W")
        logger.info(f"   Temporal bounds: {self.start_year} to {self.end_year} ({self.end_year - self.start_year + 1} years)")
    
    def clear_historical_noaa_folder(self):
        """Clear the historical NOAA data folder for a clean start"""
        logger.info("🧹 Clearing historical NOAA data folder...")
        
        if self.historical_noaa_dir.exists():
            shutil.rmtree(self.historical_noaa_dir)
            logger.info("✅ Historical NOAA data folder cleared")
        else:
            logger.info("📁 Historical NOAA data folder doesn't exist, creating...")
        
        self.historical_noaa_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Historical NOAA data folder ready")
    
    def download_ghcn_tar_file(self):
        """Download the GHCN-Daily tar file from NOAA FTP"""
        logger.info("📥 Downloading GHCN-Daily tar file from NOAA...")
        
        tar_url = f"ftp://{self.ftp_base}{self.ftp_path}/{self.tar_filename}"
        tar_path = self.historical_noaa_dir / self.tar_filename
        
        try:
            # Use wget for reliable FTP download
            cmd = [
                'wget', 
                '--progress=bar',
                '--timeout=300',
                '--tries=3',
                '-O', str(tar_path),
                tar_url
            ]
            
            logger.info(f"   Command: {' '.join(cmd)}")
            logger.info("   Downloading... (this may take several minutes)")
            result = subprocess.run(cmd, check=True)
            
            if tar_path.exists() and tar_path.stat().st_size > 0:
                size_mb = tar_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Downloaded {self.tar_filename} ({size_mb:.1f} MB)")
                return True
            else:
                logger.error(f"❌ Download failed - file is empty or missing")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Download failed with error: {e}")
            logger.error(f"   stdout: {e.stdout}")
            logger.error(f"   stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during download: {e}")
            return False
    
    def extract_tar_file(self):
        """Extract the downloaded tar file"""
        logger.info("📦 Extracting tar file...")
        
        tar_path = self.historical_noaa_dir / self.tar_filename
        
        if not tar_path.exists():
            logger.error(f"❌ Tar file not found: {tar_path}")
            return False
        
        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(self.historical_noaa_dir)
            
            # Check what was extracted
            extracted_files = list(self.historical_noaa_dir.glob('*'))
            logger.info(f"✅ Extracted {len(extracted_files)} files/directories")
            
            # List the extracted contents
            for item in extracted_files:
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    logger.info(f"   📄 {item.name} ({size_mb:.1f} MB)")
                else:
                    logger.info(f"   📁 {item.name}/")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return False
    
    def cleanup_original_files(self):
        """Delete the original tar file and version files"""
        logger.info("🗑️ Cleaning up original files...")
        
        # Delete tar file
        tar_path = self.historical_noaa_dir / self.tar_filename
        if tar_path.exists():
            tar_path.unlink()
            logger.info(f"✅ Deleted {self.tar_filename}")
        
        # Delete version files
        version_files = ['ghcnd-version.txt', 'ghcnd-stations.txt', 'ghcnd-inventory.txt']
        for version_file in version_files:
            version_path = self.raw_data_dir / version_file
            if version_path.exists():
                version_path.unlink()
                logger.info(f"✅ Deleted {version_file}")
        
        logger.info("✅ Cleanup complete")
    
    def load_station_metadata(self):
        """Load station metadata from stations file"""
        logger.info("📋 Loading station metadata...")
        
        stations_file = self.metadata_dir / "ghcnd-stations.txt"
        if not stations_file.exists():
            logger.error(f"❌ Stations file not found: {stations_file}")
            return {}
        
        stations = {}
        try:
            with open(stations_file, 'r') as f:
                for line in f:
                    if len(line) >= 85:  # Minimum line length for valid record
                        station_id = line[0:11].strip()
                        lat = float(line[12:20].strip())
                        lon = float(line[21:30].strip())
                        elevation = float(line[31:37].strip()) if line[31:37].strip() != '-999.9' else None
                        name = line[41:71].strip()
                        
                        stations[station_id] = {
                            'lat': lat,
                            'lon': lon,
                            'elevation': elevation,
                            'name': name
                        }
            
            logger.info(f"   Loaded {len(stations)} station records")
            return stations
            
        except Exception as e:
            logger.error(f"❌ Error loading station metadata: {e}")
            return {}
    
    def filter_canadian_stations(self):
        """Filter for Canadian stations within spatial bounds"""
        logger.info("🇨🇦 Filtering for Canadian stations...")
        
        # Load station metadata
        stations = self.load_station_metadata()
        if not stations:
            logger.error("❌ No station metadata available")
            return False
        
        # Find the extracted directory (should contain .dly files)
        extracted_dirs = [d for d in self.historical_noaa_dir.iterdir() if d.is_dir()]
        if not extracted_dirs:
            logger.error("❌ No extracted directories found")
            return False
        
        source_dir = extracted_dirs[0]  # Assume first directory contains the data
        logger.info(f"   Source directory: {source_dir}")
        
        # Count total .dly files
        dly_files = list(source_dir.glob('*.dly'))
        logger.info(f"   Found {len(dly_files)} .dly files to process")
        
        # Create canadian_stations directory
        self.canadian_stations_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each .dly file
        canadian_files = 0
        total_records = 0
        kept_records = 0
        
        for dly_file in dly_files:
            station_id = dly_file.stem
            
            # Check if this is a Canadian station (starts with CA)
            if not station_id.startswith('CA'):
                continue
            
            # Get station metadata
            if station_id not in stations:
                logger.warning(f"   ⚠️ {station_id}: No metadata found")
                continue
            
            station_info = stations[station_id]
            lat = station_info['lat']
            lon = station_info['lon']
            
            # Check if within spatial bounds
            if (self.spatial_bounds['min_lat'] <= lat <= self.spatial_bounds['max_lat'] and
                self.spatial_bounds['min_lon'] <= lon <= self.spatial_bounds['max_lon']):
                
                # Filter for temporal bounds and create filtered file
                filtered_records = self._filter_temporal_bounds(dly_file)
                if filtered_records > 0:
                    output_file = self.canadian_stations_dir / dly_file.name
                    if self._create_filtered_dly_file(dly_file, output_file):
                        canadian_files += 1
                        kept_records += filtered_records
                        logger.info(f"   ✅ {station_id}: {lat:.2f}°N, {lon:.2f}°W ({filtered_records} records)")
                    else:
                        logger.warning(f"   ⚠️ {station_id}: Failed to create filtered file")
                else:
                    logger.info(f"   ⚠️ {station_id}: No data in temporal bounds")
            else:
                logger.debug(f"   ❌ {station_id}: Outside spatial bounds ({lat:.2f}°N, {lon:.2f}°W)")
        
        logger.info(f"✅ Canadian station filtering complete")
        logger.info(f"   Files processed: {canadian_files}")
        logger.info(f"   Records kept: {kept_records:,}")
        
        return canadian_files > 0
    
    def _filter_temporal_bounds(self, dly_file):
        """Filter a .dly file for temporal bounds and return record count"""
        try:
            with open(dly_file, 'r') as f:
                lines = f.readlines()
            
            kept_records = 0
            for line in lines:
                if len(line) >= 15:
                    year_str = line[11:15]
                    try:
                        year = int(year_str)
                        if self.temporal_bounds['start_year'] <= year <= self.temporal_bounds['end_year']:
                            kept_records += 1
                    except ValueError:
                        continue
            
            return kept_records
            
        except Exception as e:
            logger.warning(f"   Error filtering temporal bounds for {dly_file}: {e}")
            return 0
    
    def _create_filtered_dly_file(self, source_file, output_file):
        """Create a filtered .dly file with only data within temporal bounds"""
        try:
            with open(source_file, 'r') as f_in, open(output_file, 'w') as f_out:
                for line in f_in:
                    if len(line) >= 15:
                        year_str = line[11:15]
                        try:
                            year = int(year_str)
                            if self.temporal_bounds['start_year'] <= year <= self.temporal_bounds['end_year']:
                                f_out.write(line)
                        except ValueError:
                            continue
            
            return True
            
        except Exception as e:
            logger.warning(f"   Error filtering {source_file.name}: {e}")
            return False
    
    def download_metadata_files(self):
        """Download metadata files (inventory.txt, stations.txt)"""
        logger.info("📋 Downloading metadata files...")
        
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_files = [
            'ghcnd-inventory.txt',
            'ghcnd-stations.txt'
        ]
        
        for filename in metadata_files:
            url = f"ftp://{self.ftp_base}{self.ftp_path}/{filename}"
            output_path = self.metadata_dir / filename
            
            try:
                cmd = [
                    'wget',
                    '--progress=bar',
                    '--timeout=60',
                    '--tries=3',
                    '-O', str(output_path),
                    url
                ]
                
                result = subprocess.run(cmd, check=True)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    size_kb = output_path.stat().st_size / 1024
                    logger.info(f"   ✅ Downloaded {filename} ({size_kb:.1f} KB)")
                else:
                    logger.error(f"   ❌ Failed to download {filename}")
                    return False
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"   ❌ Failed to download {filename}: {e}")
                return False
            except Exception as e:
                logger.error(f"   ❌ Error downloading {filename}: {e}")
                return False
        
        logger.info("✅ Metadata files downloaded")
        return True
    
    def cleanup_extracted_directory(self):
        """Remove the original extracted directory after filtering"""
        logger.info("🧹 Cleaning up extracted directory...")
        
        extracted_dirs = [d for d in self.historical_noaa_dir.iterdir() if d.is_dir()]
        for extracted_dir in extracted_dirs:
            if extracted_dir.name == "ghcnd_all":
                shutil.rmtree(extracted_dir)
                logger.info(f"   ✅ Removed {extracted_dir.name}")
        
        logger.info("✅ Cleanup complete")
    
    def verify_final_structure(self):
        """Verify the final data structure"""
        logger.info("🔍 Verifying final data structure...")
        
        # Check canadian_stations directory
        if not self.canadian_stations_dir.exists():
            logger.error("❌ canadian_stations directory not found")
            return False
        
        dly_files = list(self.canadian_stations_dir.glob('*.dly'))
        logger.info(f"   Canadian stations: {len(dly_files)} .dly files")
        
        # Check metadata directory
        if not self.metadata_dir.exists():
            logger.error("❌ metadata directory not found")
            return False
        
        metadata_files = list(self.metadata_dir.glob('*.txt'))
        logger.info(f"   Metadata files: {len(metadata_files)} .txt files")
        
        # Verify temporal bounds in filtered data
        self._verify_temporal_bounds(dly_files)
        
        # Sample a few files to verify content
        if dly_files:
            sample_file = dly_files[0]
            try:
                with open(sample_file, 'r') as f:
                    first_line = f.readline().strip()
                logger.info(f"   Sample record: {first_line[:50]}...")
            except Exception as e:
                logger.warning(f"   ⚠️ Could not read sample file: {e}")
        
        logger.info("✅ Final structure verification complete")
        return True
    
    def _verify_temporal_bounds(self, dly_files):
        """Verify that all data is within our temporal bounds"""
        logger.info("   📅 Verifying temporal bounds...")
        
        years_found = set()
        total_records = 0
        
        # Sample a few files to check years
        sample_files = dly_files[:min(10, len(dly_files))]
        
        for dly_file in sample_files:
            try:
                with open(dly_file, 'r') as f:
                    for line in f:
                        if len(line) >= 15:
                            year_str = line[11:15]
                            try:
                                year = int(year_str)
                                years_found.add(year)
                                total_records += 1
                            except ValueError:
                                continue
            except Exception as e:
                logger.warning(f"   ⚠️ Error reading {dly_file.name}: {e}")
        
        years_found = sorted(years_found)
        logger.info(f"   Years found in sample: {years_found}")
        logger.info(f"   Total records in sample: {total_records}")
        
        # Check if all years are within bounds
        out_of_bounds = [y for y in years_found if y < self.temporal_bounds['start_year'] or y > self.temporal_bounds['end_year']]
        if out_of_bounds:
            logger.warning(f"   ⚠️ Found data outside temporal bounds: {out_of_bounds}")
        else:
            logger.info(f"   ✅ All data within temporal bounds ({self.temporal_bounds['start_year']}-{self.temporal_bounds['end_year']})")
    
    def run_full_collection(self, test_mode=False):
        """Run the complete historical data collection process"""
        logger.info("🚀 Starting Historical Weather Data Collection")
        if test_mode:
            logger.info("🧪 TEST MODE - Skipping download, testing filtering only")
        logger.info("=" * 60)
        
        # Check memory before starting
        self.system_monitor.log_memory_status()
        
        try:
            if not test_mode:
                # Step 1: Clear historical NOAA data folder
                self.clear_historical_noaa_folder()
                
                # Step 2: Download GHCN tar file
                if not self.download_ghcn_tar_file():
                    raise Exception("Failed to download GHCN tar file")
                
                # Step 3: Extract tar file
                if not self.extract_tar_file():
                    raise Exception("Failed to extract tar file")
                
                # Step 4: Clean up original files
                self.cleanup_original_files()
                
                # Step 5: Download metadata files
                if not self.download_metadata_files():
                    raise Exception("Failed to download metadata files")
            else:
                logger.info("🧪 Skipping download steps in test mode")
            
            # Step 6: Filter for Canadian stations
            if not self.filter_canadian_stations():
                raise Exception("Failed to filter Canadian stations")
            
            if not test_mode:
                # Step 7: Clean up extracted directory (but keep canadian_stations and metadata)
                self.cleanup_extracted_directory()
            
            # Step 8: Verify final structure
            if not self.verify_final_structure():
                raise Exception("Final structure verification failed")
            
            logger.info("🎉 Historical data collection completed successfully!")
            logger.info("=" * 60)
            logger.info("Final structure:")
            logger.info(f"   📁 {self.canadian_stations_dir} - Canadian station .dly files")
            logger.info(f"   📁 {self.metadata_dir} - Metadata files")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Historical data collection failed: {e}")
            logger.error("=" * 60)
            logger.error("ERROR LOG:")
            logger.error(f"   Error: {e}")
            logger.error(f"   Type: {type(e).__name__}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return False

def main():
    """Main execution function"""
    import sys
    
    # Check for test mode
    test_mode = "--test" in sys.argv
    
    try:
        collector = HistoricalDataCollector()
        success = collector.run_full_collection(test_mode=test_mode)
        return success
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Historical data collection completed successfully!")
        sys.exit(0)
    else:
        print("❌ Historical data collection failed!")
        sys.exit(1)
