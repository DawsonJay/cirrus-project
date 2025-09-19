#!/usr/bin/env python3
"""
Validate and Process Raw Weather Data
=====================================
Validates raw .dly files and metadata, outputs clean CSV files ready for database import.
Processes stations metadata, inventory data, and weather records with detailed error reporting.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import shutil
from typing import Dict, List, Tuple, Optional
import re
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../production/logs/data_validation.log'),
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
                'files_per_chunk': 5,  # Very small chunks
                'memory_percent': 60,  # Very conservative memory usage
                'description': 'Raspberry Pi - Ultra-conservative settings for 1GB RAM'
            },
            'low_end': {
                'max_processes': 2,
                'files_per_chunk': 10,
                'memory_percent': 70,
                'description': 'Low-end hardware - Small chunks, limited parallelism'
            },
            'mid_range': {
                'max_processes': 3,
                'files_per_chunk': 20,
                'memory_percent': 75,
                'description': 'Mid-range hardware - Balanced performance and safety'
            },
            'high_end': {
                'max_processes': 4,
                'files_per_chunk': 50,
                'memory_percent': 80,
                'description': 'High-end hardware - Maximum performance'
            },
            'enterprise': {
                'max_processes': min(8, self.cpu_count),
                'files_per_chunk': 100,
                'memory_percent': 85,
                'description': 'Enterprise hardware - Maximum parallelism'
            }
        }
        
        return settings.get(self.hardware_type, settings['mid_range'])
    
    def get_optimal_processes(self):
        """Get optimal number of processes for this hardware"""
        return self.optimal_settings['max_processes']
    
    def get_optimal_files_per_chunk(self):
        """Get optimal number of files per chunk for this hardware"""
        return self.optimal_settings['files_per_chunk']
    
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

class RawDataValidator:
    """Validates and processes raw GHCN-Daily weather data"""
    
    def __init__(self, data_dir="../../data", test_mode=False, test_wildfire_only=False):
        self.data_dir = Path(data_dir)
        self.raw_data_dir = self.data_dir / "raw_data"
        self.validated_data_dir = self.data_dir / "validated_data"
        self.test_mode = test_mode
        self.test_wildfire_only = test_wildfire_only
        
        # Adaptive system monitoring
        self.system_monitor = AdaptiveSystemMonitor()
        
        # Input paths
        self.stations_file = self.raw_data_dir / "historical_noaa_data" / "metadata" / "ghcnd-stations.txt"
        self.inventory_file = self.raw_data_dir / "historical_noaa_data" / "metadata" / "ghcnd-inventory.txt"
        self.dly_files_dir = self.raw_data_dir / "historical_noaa_data" / "canadian_stations"
        self.wildfire_data_dir = self.raw_data_dir / "wildfire_data" / "final_csv"
        
        # Output paths
        self.weather_csv = self.validated_data_dir / "weather_records.csv"
        self.stations_csv = self.validated_data_dir / "stations.csv"
        self.inventory_csv = self.validated_data_dir / "station_inventory.csv"
        self.wildfire_csv = self.validated_data_dir / "wildfire_records.csv"
        self.report_file = self.validated_data_dir / "validation_report.txt"
        
        # Validation statistics
        self.stats = {
            'stations_processed': 0,
            'stations_valid': 0,
            'stations_removed': 0,
            'weather_records_processed': 0,
            'weather_records_valid': 0,
            'weather_records_removed': 0,
            'wildfire_records_processed': 0,
            'wildfire_records_valid': 0,
            'wildfire_records_removed': 0,
            'errors': []
        }
        
        # Canadian climate bounds for validation
        self.temp_bounds = {'min': -60, 'max': 45}  # °C
        self.precip_bounds = {'min': 0, 'max': 500}  # mm
        self.snow_bounds = {'min': 0, 'max': 500}   # cm
        
    def clear_validated_data_folder(self):
        """Clear the validated_data folder for a fresh start"""
        logger.info("🧹 Clearing validated_data folder...")
        
        if self.validated_data_dir.exists():
            shutil.rmtree(self.validated_data_dir)
            logger.info("   ✅ Removed existing validated_data folder")
        
        self.validated_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("   ✅ Created fresh validated_data folder")
    
    def validate_stations_metadata(self):
        """Validate and process station metadata"""
        logger.info("🏢 Processing station metadata...")
        
        if not self.stations_file.exists():
            raise Exception(f"Stations file not found: {self.stations_file}")
        
        stations_data = []
        
        with open(self.stations_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if len(line.strip()) < 80:  # Skip incomplete lines
                    continue
                
                try:
                    # Parse station metadata (fixed width format)
                    station_id = line[0:11].strip()
                    latitude = float(line[12:20].strip())
                    longitude = float(line[21:30].strip())
                    elevation = float(line[31:37].strip()) if line[31:37].strip() != '-999.9' else None
                    name = line[41:71].strip()
                    country = line[0:2]
                    
                    # Validate coordinates (should be within our Canadian bounds)
                    if not (41.75 <= latitude <= 60.0 and -137.72 <= longitude <= -52.67):
                        self.stats['errors'].append(f"Station {station_id}: Outside Canadian bounds (lat={latitude}, lon={longitude})")
                        continue
                    
                    # Validate elevation
                    if elevation is not None and (elevation < -100 or elevation > 5000):
                        self.stats['errors'].append(f"Station {station_id}: Invalid elevation {elevation}m")
                        elevation = None
                    
                    stations_data.append({
                        'station_id': station_id,
                        'latitude': latitude,
                        'longitude': longitude,
                        'elevation': elevation,
                        'name': name,
                        'country': country
                    })
                    
                except (ValueError, IndexError) as e:
                    self.stats['errors'].append(f"Line {line_num}: Invalid station format - {e}")
                    continue
        
        # Create stations DataFrame and save
        stations_df = pd.DataFrame(stations_data)
        stations_df.to_csv(self.stations_csv, index=False)
        
        self.stats['stations_processed'] = len(stations_data)
        self.stats['stations_valid'] = len(stations_df)
        
        logger.info(f"   ✅ Processed {len(stations_data)} stations")
        logger.info(f"   📊 Valid stations: {len(stations_df)}")
        
        return stations_df
    
    def validate_inventory_metadata(self):
        """Validate and process inventory metadata"""
        logger.info("📋 Processing inventory metadata...")
        
        if not self.inventory_file.exists():
            logger.warning("   ⚠️ Inventory file not found, skipping...")
            return pd.DataFrame()
        
        inventory_data = []
        
        with open(self.inventory_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if len(line.strip()) < 80:  # Skip incomplete lines
                    continue
                
                try:
                    # Parse inventory metadata (fixed width format)
                    station_id = line[0:11].strip()
                    latitude = float(line[12:20].strip())
                    longitude = float(line[21:30].strip())
                    element = line[31:35].strip()
                    first_year = int(line[36:40].strip())
                    last_year = int(line[41:45].strip())
                    
                    # Only keep stations within our bounds and time period
                    if not (41.75 <= latitude <= 60.0 and -137.72 <= longitude <= -52.67):
                        continue
                    
                    # Only keep data from our time period (2022-2025)
                    if last_year < 2022 or first_year > 2025:
                        continue
                    
                    # Only keep relevant weather variables
                    if element not in ['TMAX', 'TMIN', 'PRCP', 'SNWD', 'TAVG']:
                        continue
                    
                    inventory_data.append({
                        'station_id': station_id,
                        'parameter': element,
                        'start_year': first_year,
                        'end_year': last_year,
                        'latitude': latitude,
                        'longitude': longitude
                    })
                    
                except (ValueError, IndexError) as e:
                    self.stats['errors'].append(f"Inventory line {line_num}: Invalid format - {e}")
                    continue
        
        # Create inventory DataFrame and save
        inventory_df = pd.DataFrame(inventory_data)
        
        if len(inventory_df) > 0:
            inventory_df.to_csv(self.inventory_csv, index=False)
            logger.info(f"   ✅ Processed {len(inventory_data)} inventory records")
            logger.info(f"   📊 Parameters: {inventory_df['parameter'].value_counts().to_dict()}")
        else:
            # Create empty CSV with proper headers
            empty_df = pd.DataFrame(columns=['station_id', 'parameter', 'start_year', 'end_year', 'latitude', 'longitude'])
            empty_df.to_csv(self.inventory_csv, index=False)
            logger.info(f"   ✅ Processed {len(inventory_data)} inventory records (empty)")
        
        return inventory_df
    
    def validate_weather_records(self):
        """Validate and process weather records from .dly files in WIDE FORMAT"""
        logger.info("🌡️ Processing weather records (wide format)...")
        
        if not self.dly_files_dir.exists():
            raise Exception(f"Canadian stations directory not found: {self.dly_files_dir}")
        
        weather_data = {}  # station_id -> date -> {variable: (value, quality)}
        dly_files = list(self.dly_files_dir.glob("*.dly"))
        
        logger.info(f"   📁 Processing {len(dly_files)} .dly files...")
        
        for file_idx, dly_file in enumerate(dly_files, 1):
            if file_idx % 100 == 0:
                logger.info(f"   📈 Progress: {file_idx}/{len(dly_files)} files")
            
            try:
                self._process_dly_file_wide(dly_file, weather_data)
            except Exception as e:
                self.stats['errors'].append(f"File {dly_file.name}: {e}")
                continue
        
        # Convert to wide format DataFrame
        logger.info("   🔄 Converting to wide format DataFrame...")
        weather_records = []
        
        for station_id, dates in weather_data.items():
            for date, variables in dates.items():
                record = {
                    'station_id': station_id,
                    'date': date,
                    'tmax': None, 'tmin': None, 'tavg': None, 'prcp': None, 'snwd': None,
                    'tmax_quality': None, 'tmin_quality': None, 'tavg_quality': None, 
                    'prcp_quality': None, 'snwd_quality': None
                }
                
                # Fill in available variables
                for var, (value, quality) in variables.items():
                    var_lower = var.lower()
                    record[var_lower] = value
                    record[f"{var_lower}_quality"] = quality
                
                weather_records.append(record)
        
        # Create DataFrame and save
        weather_df = pd.DataFrame(weather_records)
        weather_df.to_csv(self.weather_csv, index=False)
        
        self.stats['weather_records_processed'] = len(weather_records)
        self.stats['weather_records_valid'] = len(weather_df)
        
        logger.info(f"   ✅ Processed {len(weather_records)} weather records (wide format)")
        if len(weather_df) > 0:
            # Count non-null values for each variable
            var_counts = {}
            for var in ['tmax', 'tmin', 'tavg', 'prcp', 'snwd']:
                var_counts[var] = weather_df[var].notna().sum()
            logger.info(f"   📊 Variable counts: {var_counts}")
        else:
            logger.info(f"   📊 Variables: No valid records found")
        
        return weather_df
    
    def validate_wildfire_records(self):
        """Validate and process wildfire records from CSV files"""
        logger.info("🔥 Processing wildfire records...")
        
        if not self.wildfire_data_dir.exists():
            logger.warning("   ⚠️ Wildfire data directory not found, skipping...")
            return pd.DataFrame()
        
        wildfire_files = list(self.wildfire_data_dir.glob("*.csv"))
        
        if not wildfire_files:
            logger.warning("   ⚠️ No wildfire CSV files found, skipping...")
            return pd.DataFrame()
        
        logger.info(f"   📁 Processing {len(wildfire_files)} wildfire CSV files...")
        
        all_wildfire_records = []
        
        for file_idx, wildfire_file in enumerate(wildfire_files, 1):
            logger.info(f"   📈 Processing {wildfire_file.name} ({file_idx}/{len(wildfire_files)})...")
            
            try:
                # Read the CSV file
                df = pd.read_csv(wildfire_file)
                logger.info(f"   📊 Loaded {len(df)} records from {wildfire_file.name}")
                
                # Validate each record
                valid_records = self._validate_wildfire_dataframe(df, wildfire_file.name)
                all_wildfire_records.extend(valid_records)
                
                logger.info(f"   ✅ Validated {len(valid_records)} records from {wildfire_file.name}")
                
            except Exception as e:
                self.stats['errors'].append(f"File {wildfire_file.name}: {e}")
                logger.error(f"   ❌ Error processing {wildfire_file.name}: {e}")
                continue
        
        # Create wildfire records DataFrame and save
        wildfire_df = pd.DataFrame(all_wildfire_records)
        wildfire_df.to_csv(self.wildfire_csv, index=False)
        
        self.stats['wildfire_records_processed'] = sum(len(pd.read_csv(f)) for f in wildfire_files)
        self.stats['wildfire_records_valid'] = len(wildfire_df)
        
        logger.info(f"   ✅ Processed {len(all_wildfire_records)} wildfire records")
        if len(wildfire_df) > 0:
            logger.info(f"   📊 Fire types: {wildfire_df['FIRE_TYPE'].value_counts().to_dict()}")
            logger.info(f"   📊 Years: {wildfire_df['YEAR'].value_counts().to_dict()}")
        else:
            logger.info(f"   📊 No valid wildfire records found")
        
        return wildfire_df
    
    def _validate_wildfire_dataframe(self, df: pd.DataFrame, filename: str) -> List[Dict]:
        """Validate a wildfire DataFrame and return valid records"""
        
        valid_records = []
        
        # Required columns for validation
        required_columns = ['LATITUDE', 'LONGITUDE', 'YEAR', 'MONTH', 'DAY', 'SIZE_HA']
        
        # Check if required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.stats['errors'].append(f"File {filename}: Missing required columns: {missing_columns}")
            return valid_records
        
        # Canadian bounds for validation
        canadian_bounds = {
            'lat_min': 41.75,
            'lat_max': 60.0,
            'lon_min': -137.72,
            'lon_max': -52.67
        }
        
        # Temporal bounds
        temporal_bounds = {
            'year_min': 2022,
            'year_max': 2025
        }
        
        for idx, row in df.iterrows():
            try:
                # Validate coordinates
                lat = float(row['LATITUDE'])
                lon = float(row['LONGITUDE'])
                
                if not (canadian_bounds['lat_min'] <= lat <= canadian_bounds['lat_max'] and 
                       canadian_bounds['lon_min'] <= lon <= canadian_bounds['lon_max']):
                    self.stats['errors'].append(f"File {filename}, row {idx}: Outside Canadian bounds (lat={lat}, lon={lon})")
                    continue
                
                # Validate temporal data
                year = int(row['YEAR'])
                month = int(row['MONTH'])
                day = int(row['DAY'])
                
                if not (temporal_bounds['year_min'] <= year <= temporal_bounds['year_max']):
                    self.stats['errors'].append(f"File {filename}, row {idx}: Year {year} outside bounds")
                    continue
                
                if not (1 <= month <= 12):
                    self.stats['errors'].append(f"File {filename}, row {idx}: Invalid month {month}")
                    continue
                
                if not (1 <= day <= 31):
                    self.stats['errors'].append(f"File {filename}, row {idx}: Invalid day {day}")
                    continue
                
                # Validate date consistency
                try:
                    fire_date = date(year, month, day)
                except ValueError:
                    self.stats['errors'].append(f"File {filename}, row {idx}: Invalid date {year}-{month:02d}-{day:02d}")
                    continue
                
                # Validate fire size
                size_ha = float(row['SIZE_HA']) if pd.notna(row['SIZE_HA']) else 0.0
                if size_ha < 0 or size_ha > 1000000:  # Reasonable bounds for fire size
                    self.stats['errors'].append(f"File {filename}, row {idx}: Invalid fire size {size_ha} ha")
                    continue
                
                # Validate geometry if present
                geometry_wkt = row.get('geometry_wkt', '')
                if geometry_wkt and not self._validate_geometry_wkt(geometry_wkt):
                    self.stats['errors'].append(f"File {filename}, row {idx}: Invalid geometry WKT")
                    continue
                
                # Create valid record
                valid_record = {
                    'NFDBFIREID': row.get('NFDBFIREID', ''),
                    'SRC_AGENCY': row.get('SRC_AGENCY', ''),
                    'FIRE_ID': row.get('FIRE_ID', ''),
                    'FIRENAME': row.get('FIRENAME', ''),
                    'LATITUDE': lat,
                    'LONGITUDE': lon,
                    'YEAR': year,
                    'MONTH': month,
                    'DAY': day,
                    'REP_DATE': row.get('REP_DATE', ''),
                    'ATTK_DATE': row.get('ATTK_DATE', ''),
                    'OUT_DATE': row.get('OUT_DATE', ''),
                    'SIZE_HA': size_ha,
                    'CAUSE': row.get('CAUSE', ''),
                    'CAUSE2': row.get('CAUSE2', ''),
                    'FIRE_TYPE': row.get('FIRE_TYPE', ''),
                    'RESPONSE': row.get('RESPONSE', ''),
                    'PROTZONE': row.get('PROTZONE', ''),
                    'PRESCRIBED': row.get('PRESCRIBED', ''),
                    'MORE_INFO': row.get('MORE_INFO', ''),
                    'CFS_NOTE1': row.get('CFS_NOTE1', ''),
                    'CFS_NOTE2': row.get('CFS_NOTE2', ''),
                    'ACQ_DATE': row.get('ACQ_DATE', ''),
                    'layer': row.get('layer', ''),
                    'omit': row.get('omit', ''),
                    'geometry_wkt': geometry_wkt,
                    'fire_date': fire_date.strftime('%Y-%m-%d')
                }
                
                valid_records.append(valid_record)
                
            except (ValueError, TypeError) as e:
                self.stats['errors'].append(f"File {filename}, row {idx}: Data validation error - {e}")
                continue
        
        return valid_records
    
    def _validate_geometry_wkt(self, geometry_wkt: str) -> bool:
        """Validate that geometry WKT is properly formatted"""
        if not geometry_wkt or geometry_wkt.strip() == '':
            return True  # Empty geometry is valid
        
        # Basic WKT validation - should start with POINT, POLYGON, etc.
        valid_prefixes = ['POINT', 'POLYGON', 'MULTIPOINT', 'MULTIPOLYGON', 'LINESTRING', 'MULTILINESTRING']
        geometry_wkt = geometry_wkt.strip().upper()
        
        return any(geometry_wkt.startswith(prefix) for prefix in valid_prefixes)
    
    def _process_dly_file_wide(self, dly_file: Path, weather_data: Dict):
        """Process a single .dly file and extract valid weather records in wide format"""
        
        records_found = 0
        
        with open(dly_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if len(line) < 35:  # Skip incomplete lines
                    continue
                
                try:
                    # Parse .dly line format
                    station_id = line[0:11].strip()
                    year = int(line[11:15])
                    month = int(line[15:17])
                    variable = line[17:21].strip()
                    
                    # Only process our target variables
                    if variable not in ['TMAX', 'TMIN', 'PRCP', 'SNWD', 'TAVG']:
                        continue
                    
                    # Only process our target years (adjust based on available data)
                    if not (2022 <= year <= 2025):
                        continue
                    
                    # Extract daily values and quality flags
                    daily_data = self._extract_daily_values(line, year, month, variable)
                    
                    # Initialize station data structure if needed
                    if station_id not in weather_data:
                        weather_data[station_id] = {}
                    
                    # Add valid records
                    for day, (value, quality) in daily_data.items():
                        if value is not None and quality == 'C':  # Only complete data
                            date_str = f"{year}-{month:02d}-{day:02d}"
                            
                            # Initialize date data structure if needed
                            if date_str not in weather_data[station_id]:
                                weather_data[station_id][date_str] = {}
                            
                            # Store variable data
                            weather_data[station_id][date_str][variable] = (value, quality)
                            records_found += 1
                
                except (ValueError, IndexError) as e:
                    self.stats['errors'].append(f"File {dly_file.name}, line {line_num}: {e}")
                    continue
        
        # Debug output for first few files
        if dly_file.name in ['CA001057052.dly', 'CA001010066.dly', 'CA001017098.dly']:
            logger.info(f"   Debug {dly_file.name}: Found {records_found} records")
    
    def _process_dly_file(self, dly_file: Path, weather_records: List[Dict]):
        """Process a single .dly file and extract valid weather records (LEGACY - kept for compatibility)"""
        
        records_found = 0
        
        with open(dly_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if len(line) < 35:  # Skip incomplete lines
                    continue
                
                try:
                    # Parse .dly line format
                    station_id = line[0:11].strip()
                    year = int(line[11:15])
                    month = int(line[15:17])
                    variable = line[17:21].strip()
                    
                    # Only process our target variables
                    if variable not in ['TMAX', 'TMIN', 'PRCP', 'SNWD', 'TAVG']:
                        continue
                    
                    # Only process our target years (adjust based on available data)
                    if not (2022 <= year <= 2025):
                        continue
                    
                    # Extract daily values and quality flags
                    daily_data = self._extract_daily_values(line, year, month, variable)
                    
                    # Add valid records
                    for day, (value, quality) in daily_data.items():
                        if value is not None and quality == 'C':  # Only complete data
                            weather_records.append({
                                'station_id': station_id,
                                'date': f"{year}-{month:02d}-{day:02d}",
                                'variable': variable,
                                'value': value,
                                'quality_flag': quality,
                                'original_line': line.strip()
                            })
                            records_found += 1
                
                except (ValueError, IndexError) as e:
                    self.stats['errors'].append(f"File {dly_file.name}, line {line_num}: {e}")
                    continue
        
        # Debug output for first few files
        if dly_file.name in ['CA001057052.dly', 'CA001010066.dly', 'CA001017098.dly']:
            logger.info(f"   Debug {dly_file.name}: Found {records_found} records")
    
    def _extract_daily_values(self, line: str, year: int, month: int, variable: str) -> Dict[int, Tuple[Optional[float], str]]:
        """Extract daily values and quality flags from a .dly line"""
        
        daily_data = {}
        
        # Calculate days in month
        if month in [1, 3, 5, 7, 8, 10, 12]:
            days_in_month = 31
        elif month in [4, 6, 9, 11]:
            days_in_month = 30
        elif month == 2:
            days_in_month = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
        else:
            return daily_data
        
        # Parse the data section (starts after position 21)
        data_section = line[21:].strip()
        
        # Split by spaces and process in pairs (value, quality_flag)
        parts = data_section.split()
        
        # Process each day's data
        for day in range(1, min(days_in_month + 1, len(parts) // 2 + 1)):
            if day * 2 - 1 < len(parts):
                value_str = parts[day * 2 - 2]  # Value is at even index
                quality_flag = parts[day * 2 - 1] if day * 2 - 1 < len(parts) else 'M'  # Quality flag is at odd index
                
                # Parse value
                if value_str == '-9999':
                    value = None
                else:
                    try:
                        value = float(value_str)
                        
                        # Convert to proper units
                        if variable in ['TMAX', 'TMIN', 'TAVG']:
                            value = value / 10.0  # Convert tenths of °C to °C
                        elif variable == 'PRCP':
                            value = value / 10.0  # Convert tenths of mm to mm
                        elif variable == 'SNWD':
                            value = value  # Already in mm
                        
                        # Validate value ranges
                        if not self._validate_value(value, variable):
                            value = None
                    
                    except ValueError:
                        value = None
                
                daily_data[day] = (value, quality_flag)
        
        return daily_data
    
    def _validate_value(self, value: float, variable: str) -> bool:
        """Validate that a weather value is within reasonable bounds"""
        
        if variable in ['TMAX', 'TMIN', 'TAVG']:
            return self.temp_bounds['min'] <= value <= self.temp_bounds['max']
        elif variable == 'PRCP':
            return self.precip_bounds['min'] <= value <= self.precip_bounds['max']
        elif variable == 'SNWD':
            return self.snow_bounds['min'] <= value <= self.snow_bounds['max']
        
        return True
    
    def generate_validation_report(self):
        """Generate detailed validation report"""
        logger.info("📝 Generating validation report...")
        
        with open(self.report_file, 'w') as f:
            f.write("WEATHER & WILDFIRE DATA VALIDATION REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Stations processed: {self.stats['stations_processed']}\n")
            f.write(f"Stations valid: {self.stats['stations_valid']}\n")
            f.write(f"Stations removed: {self.stats['stations_processed'] - self.stats['stations_valid']}\n")
            f.write(f"Weather records processed: {self.stats['weather_records_processed']}\n")
            f.write(f"Weather records valid: {self.stats['weather_records_valid']}\n")
            f.write(f"Weather records removed: {self.stats['weather_records_processed'] - self.stats['weather_records_valid']}\n")
            f.write(f"Wildfire records processed: {self.stats['wildfire_records_processed']}\n")
            f.write(f"Wildfire records valid: {self.stats['wildfire_records_valid']}\n")
            f.write(f"Wildfire records removed: {self.stats['wildfire_records_processed'] - self.stats['wildfire_records_valid']}\n")
            f.write(f"Total errors: {len(self.stats['errors'])}\n\n")
            
            # Error details
            if self.stats['errors']:
                f.write("ERROR DETAILS\n")
                f.write("-" * 15 + "\n")
                for i, error in enumerate(self.stats['errors'], 1):
                    f.write(f"{i:4d}. {error}\n")
            else:
                f.write("No errors found! ✅\n")
        
        logger.info(f"   ✅ Report saved to {self.report_file}")
    
    def run_validation(self):
        """Run the complete validation process"""
        if self.test_wildfire_only:
            logger.info("🔥 Starting Wildfire-Only Validation (Test Mode)")
        elif self.test_mode:
            logger.info("🧪 Starting Raw Data Validation (Test Mode)")
        else:
            logger.info("🚀 Starting Raw Data Validation")
        logger.info("=" * 50)
        
        try:
            # Step 1: Clear validated data folder
            self.clear_validated_data_folder()
            
            # Initialize default values
            stations_df = pd.DataFrame()
            inventory_df = pd.DataFrame()
            weather_df = pd.DataFrame()
            wildfire_df = pd.DataFrame()
            
            if self.test_wildfire_only:
                # Test mode: Only process wildfire data
                logger.info("🧪 Test mode: Processing wildfire data only...")
                wildfire_df = self.validate_wildfire_records()
            else:
                # Normal mode: Process all data
                # Step 2: Process station metadata
                stations_df = self.validate_stations_metadata()
                
                # Step 3: Process inventory metadata
                inventory_df = self.validate_inventory_metadata()
                
                # Step 4: Process weather records
                weather_df = self.validate_weather_records()
                
                # Step 5: Process wildfire records
                wildfire_df = self.validate_wildfire_records()
            
            # Step 6: Generate validation report
            self.generate_validation_report()
            
            # Final summary
            logger.info("🎉 Validation completed successfully!")
            logger.info(f"📊 Final results:")
            logger.info(f"   Stations: {len(stations_df)}")
            logger.info(f"   Inventory records: {len(inventory_df)}")
            logger.info(f"   Weather records: {len(weather_df)}")
            logger.info(f"   Wildfire records: {len(wildfire_df)}")
            logger.info(f"   Errors: {len(self.stats['errors'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return False

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate raw weather and wildfire data')
    parser.add_argument('--test', action='store_true', help='Run in test mode (faster processing)')
    parser.add_argument('--test-wildfire-only', action='store_true', help='Test only wildfire validation (fastest)')
    parser.add_argument('--data-dir', default='../../data', help='Data directory path')
    
    args = parser.parse_args()
    
    try:
        validator = RawDataValidator(
            data_dir=args.data_dir,
            test_mode=args.test,
            test_wildfire_only=args.test_wildfire_only
        )
        success = validator.run_validation()
        return success
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Raw data validation completed successfully!")
        sys.exit(0)
    else:
        print("❌ Raw data validation failed!")
        sys.exit(1)
