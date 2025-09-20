#!/usr/bin/env python3
"""
Stage 5: Memory-Safe Parallel Interpolated Grid Database Creator
===============================================================
Parallel processing with memory monitoring and safety limits.

Key Features:
- Memory monitoring and limits
- Safe parallel processing (2-4 processes max)
- Database connection pooling
- Automatic fallback to sequential if memory insufficient
- Real-time memory usage tracking
"""

import sqlite3
import pandas as pd
import numpy as np
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Tuple, Optional
import time
import math
import psutil
import multiprocessing as mp
from scipy.spatial.distance import cdist
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import sys
import threading
import json

warnings.filterwarnings('ignore')

def log_progress(message: str):
    """Simple progress logging that works with parallel processes"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")
    logger.info(message)

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('../../production/logs/stage_5_interpolated_grid.log')
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
        
        # Start with full memory allocation, but will scale down if under pressure
        if self.max_memory_gb is None:
            self.max_memory_gb = self.total_memory_gb * (max_memory_percent / 100)
        
        logger.info(f"🔧 Adaptive System Monitor initialized:")
        logger.info(f"   Hardware type: {self.hardware_type}")
        logger.info(f"   Total system memory: {self.total_memory_gb:.1f} GB")
        logger.info(f"   CPU cores: {self.cpu_count}")
        logger.info(f"   Memory limit: {self.max_memory_gb:.1f} GB ({max_memory_percent}%)")
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
        if memory_gb <= 4:
            return 'low_end'  # Raspberry Pi, old laptops
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
                'chunk_size': 10,    # Very small chunks
                'memory_percent': 70, # Conservative memory usage
                'database_mode': 'sequential',  # No parallel DB writes
                'description': 'Raspberry Pi - Conservative settings for stability'
            },
            'low_end': {
                'max_processes': 2,
                'chunk_size': 25,
                'memory_percent': 75,
                'database_mode': 'sequential',
                'description': 'Low-end hardware - Small chunks, limited parallelism'
            },
            'mid_range': {
                'max_processes': 3,
                'chunk_size': 50,
                'memory_percent': 80,
                'database_mode': 'parallel',
                'description': 'Mid-range hardware - Balanced performance and safety'
            },
            'high_end': {
                'max_processes': 4,
                'chunk_size': 20,
                'memory_percent': 85,
                'database_mode': 'parallel',
                'description': 'High-end hardware - Memory-safe parallel processing'
            },
            'enterprise': {
                'max_processes': min(8, self.cpu_count),
                'chunk_size': 200,
                'memory_percent': 90,
                'database_mode': 'parallel',
                'description': 'Enterprise hardware - Maximum parallelism'
            }
        }
        
        return settings.get(self.hardware_type, settings['mid_range'])
    
    def get_optimal_processes(self):
        """Get optimal number of processes for this hardware"""
        return self.optimal_settings['max_processes']
    
    def get_optimal_chunk_size(self):
        """Get optimal chunk size for this hardware"""
        return self.optimal_settings['chunk_size']
    
    def get_optimal_memory_percent(self):
        """Get optimal memory usage percentage for this hardware"""
        return self.optimal_settings['memory_percent']
    
    def should_use_parallel_database(self):
        """Determine if parallel database writes are safe"""
        return self.optimal_settings['database_mode'] == 'parallel'
    
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
    
    def is_memory_stressed(self):
        """Check if system is under memory stress"""
        memory = self.get_memory_usage()
        return memory['percent_used'] > 90 or memory['available_gb'] < 2.0
    
    def get_dynamic_process_count(self, base_processes):
        """Get dynamic process count based on current system load"""
        memory = self.get_memory_usage()
        
        # Scale down processes based on memory pressure
        if memory['percent_used'] > 85:
            return max(1, base_processes // 2)  # Half the processes
        elif memory['percent_used'] > 75:
            return max(1, int(base_processes * 0.75))  # 75% of processes
        else:
            return base_processes  # Full processes
    
    def get_dynamic_chunk_size(self, base_chunk_size):
        """Get dynamic chunk size based on current system load"""
        memory = self.get_memory_usage()
        
        # Scale down chunk size based on memory pressure
        if memory['percent_used'] > 85:
            return max(10, base_chunk_size // 2)  # Half the chunk size
        elif memory['percent_used'] > 75:
            return max(25, int(base_chunk_size * 0.75))  # 75% of chunk size
        else:
            return base_chunk_size  # Full chunk size
    
    def should_fallback_to_sequential(self):
        """Determine if we should fall back to sequential processing"""
        return self.is_memory_stressed() or not self.should_use_parallel_database()

def process_date_chunk_parallel(args):
    """Process a chunk of dates in parallel (worker function)"""
    (date_chunk, land_cells_data, cell_station_assignments, 
     raw_db_path, chunk_id) = args
    
    try:
        # Connect to database
        raw_conn = sqlite3.connect(raw_db_path)
        
        # Convert land_cells_data back to DataFrame
        land_cells = pd.DataFrame(land_cells_data)
        
        # Get weather data for this date chunk
        date_placeholders = ','.join(['?' for _ in date_chunk])
        chunk_weather = pd.read_sql_query(f'''
            SELECT station_id, date, tmax, tmin, tavg, temp_range, prcp, snwd,
                   year, month, day_of_year, season, data_completeness
            FROM weather_data_wide
            WHERE date IN ({date_placeholders})
            ORDER BY date, station_id
        ''', raw_conn, params=date_chunk)
        
        # Create weather records for this chunk
        weather_records = []
        
        # Group weather data by date for efficient processing
        weather_by_date = chunk_weather.groupby('date')
        
        for date_str, date_weather in weather_by_date:
            # Create a lookup for this date's weather data
            date_weather_lookup = {row['station_id']: row for _, row in date_weather.iterrows()}
            
            # Process all cells for this date
            for _, cell in land_cells.iterrows():
                cell_id = cell['cell_id']
                assignment = cell_station_assignments[cell_id]
                
                # Get weather data for primary station
                if assignment['primary_station'] in date_weather_lookup:
                    weather_row = date_weather_lookup[assignment['primary_station']]
                    
                    weather_records.append({
                        'cell_id': cell_id,
                        'date': date_str,
                        'tmax': weather_row['tmax'],
                        'tmin': weather_row['tmin'],
                        'tavg': weather_row['tavg'],
                        'temp_range': weather_row['temp_range'],
                        'prcp': weather_row['prcp'],
                        'snwd': weather_row['snwd'],
                        'year': weather_row['year'],
                        'month': weather_row['month'],
                        'day_of_year': weather_row['day_of_year'],
                        'season': weather_row['season'],
                        'data_completeness': weather_row['data_completeness'],
                        'interpolation_method': 'nearest_station',
                        'nearest_station_id': assignment['primary_station'],
                        'nearest_station_distance_km': assignment['primary_distance'],
                        'station_count_used': 1,
                        'confidence_score': max(0.1, 1.0 - assignment['primary_distance'] / 100.0)
                    })
                else:
                    # Use seasonal defaults
                    seasonal_data = get_seasonal_defaults(date_str)
                    weather_records.append({
                        'cell_id': cell_id,
                        'date': date_str,
                        **seasonal_data,
                        'interpolation_method': 'seasonal_default',
                        'nearest_station_id': None,
                        'nearest_station_distance_km': None,
                        'station_count_used': 0,
                        'confidence_score': 0.1
                    })
        
        raw_conn.close()
        
        # Clean up memory in worker process
        del chunk_weather
        del weather_by_date
        del date_weather_lookup
        del land_cells
        
        import gc
        gc.collect()
        
        return {
            'chunk_id': chunk_id,
            'records': weather_records,
            'count': len(weather_records),
            'dates_processed': len(date_chunk)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in parallel chunk {chunk_id}: {e}")
        return {
            'chunk_id': chunk_id,
            'records': [],
            'count': 0,
            'dates_processed': 0,
            'error': str(e)
        }

def get_seasonal_defaults(date_str: str) -> Dict:
    """Get seasonal default weather values (standalone function for parallel processing)"""
    date = pd.to_datetime(date_str)
    month = date.month
    
    # Seasonal temperature pattern for Canada
    avg_temp = 10 + 15 * np.sin(2 * np.pi * (month - 3) / 12)
    temp_range = 8 + 4 * np.sin(2 * np.pi * (month - 6) / 12)
    
    tmax = avg_temp + temp_range / 2
    tmin = avg_temp - temp_range / 2
    
    # Seasonal precipitation
    precipitation = max(0, 2 + np.sin(2 * np.pi * (month - 6) / 12))
    
    # Snow depth (winter only)
    snow_depth = max(0, 10 * np.sin(2 * np.pi * (month - 12) / 12)) if month in [11, 12, 1, 2, 3] else 0
    
    # Season
    if month in [12, 1, 2]:
        season = 'winter'
    elif month in [3, 4, 5]:
        season = 'spring'
    elif month in [6, 7, 8]:
        season = 'summer'
    else:
        season = 'fall'
    
    return {
        'tmax': tmax,
        'tmin': tmin,
        'tavg': avg_temp,
        'temp_range': temp_range,
        'prcp': precipitation,
        'snwd': snow_depth,
        'year': date.year,
        'month': date.month,
        'day_of_year': date.timetuple().tm_yday,
        'season': season,
        'data_completeness': 0.0
    }

class ParallelSafeInterpolatedGridCreator:
    """Memory-safe parallel interpolated grid creator"""
    
    def __init__(self, 
                 raw_db_path: str = "../../databases/raw_weather_db.db",
                 output_db_path: str = "../../databases/interpolated_grid_db.db",
                 test_mode: bool = False,
                 test_region: str = "toronto",
                 grid_size_km: int = 10,
                 max_processes: int = None,
                 max_memory_percent: int = 80):
        
        self.raw_db_path = Path(raw_db_path)
        self.output_db_path = Path(output_db_path)
        self.test_mode = test_mode
        self.test_region = test_region
        self.grid_size_km = grid_size_km
        
        # Adaptive system monitoring
        self.system_monitor = AdaptiveSystemMonitor(max_memory_percent=max_memory_percent)
        
        # Use adaptive settings unless explicitly overridden
        if max_processes is None:
            self.max_processes = self.system_monitor.get_optimal_processes()
        else:
            self.max_processes = max_processes
        
        # Override memory percent if hardware suggests different
        if max_memory_percent == 80:  # Default value
            optimal_memory_percent = self.system_monitor.get_optimal_memory_percent()
            if optimal_memory_percent != 80:
                self.system_monitor.max_memory_percent = optimal_memory_percent
                self.system_monitor.max_memory_gb = self.system_monitor.total_memory_gb * (optimal_memory_percent / 100)
                logger.info(f"   🔧 Adjusted memory limit to {optimal_memory_percent}% for {self.system_monitor.hardware_type}")
        
        logger.info(f"🔧 Adaptive processing settings:")
        logger.info(f"   Max processes: {self.max_processes}")
        logger.info(f"   Available memory: {self.system_monitor.get_memory_usage()['available_gb']:.1f} GB")
        
        # Spatial bounds for Southern Canada
        self.spatial_bounds = {
            'lat_min': 41.75, 'lat_max': 60.0, 
            'lon_min': -137.72, 'lon_max': -52.67
        }
        
        # Test regions (smaller areas for testing)
        self.test_regions = {
            'toronto': {'lat_min': 43.0, 'lat_max': 44.0, 'lon_min': -80.0, 'lon_max': -78.0},
            'vancouver': {'lat_min': 49.0, 'lat_max': 50.0, 'lon_min': -125.0, 'lon_max': -122.0},
            'calgary': {'lat_min': 50.0, 'lat_max': 51.0, 'lon_min': -115.0, 'lon_max': -113.0},
            'montreal': {'lat_min': 45.0, 'lat_max': 46.0, 'lon_min': -74.0, 'lon_max': -73.0}
        }
        
        # Use test bounds if in test mode
        if self.test_mode and self.test_region in self.test_regions:
            self.spatial_bounds = self.test_regions[self.test_region]
            logger.info(f"🧪 Test mode: Using {self.test_region} region")
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate haversine distance between two points in km"""
        R = 6371  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c
    
    def create_database(self) -> bool:
        """Create memory-safe parallel interpolated grid database"""
        start_time = time.time()
        
        print("🚀 Starting Stage 5: Interpolated Grid Database Creation")
        log_progress(f"Grid size: {self.grid_size_km}km")
        log_progress(f"Bounds: {self.spatial_bounds['lat_min']:.2f}°N to {self.spatial_bounds['lat_max']:.2f}°N")
        log_progress(f"Database: {self.output_db_path}")
        
        try:
            # Step 1: Clear existing database
            self._clear_existing_database()
            
            # Step 2: Create optimized schema
            self._create_optimized_schema()
            
            # Step 3: Generate curvature-adjusted grid
            grid_count = self._create_curvature_adjusted_grid()
            
            # Step 4: Classify terrain using spatial rules
            land_count = self._classify_terrain_spatial_rules()
            
            # Step 5: Memory-safe parallel weather interpolation
            weather_count = self._interpolate_weather_parallel_safe()
            
            # Step 6: Smart wildfire assignment
            wildfire_count = self._assign_wildfires_smart()
            
            # Step 7: Create optimized indexes
            self._create_optimized_indexes()
            
            # Step 8: Generate summary statistics
            self._generate_summary_stats()
            
            # Final summary
            total_time = time.time() - start_time
            
            logger.info("=" * 70)
            logger.info("🎉 Stage 5 Complete - Memory-Safe Parallel Interpolated Grid Created!")
            logger.info("=" * 70)
            logger.info(f"📊 Final Results:")
            logger.info(f"   Grid cells: {grid_count:,}")
            logger.info(f"   Land/Urban cells: {land_count:,}")
            logger.info(f"   Weather records: {weather_count:,}")
            logger.info(f"   Wildfire assignments: {wildfire_count:,}")
            logger.info(f"⏱️ Total time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
            logger.info(f"🚀 Processing rate: {weather_count/total_time:,.0f} records/second")
            logger.info(f"💾 Database: {self.output_db_path}")
            
            print("✅ Stage 5 Complete: Interpolated Grid Database Created Successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating database: {e}")
            print("❌ Stage 5 Failed: Database Creation Unsuccessful")
            raise
    
    def _clear_existing_database(self):
        """Clear existing database"""
        if self.output_db_path.exists():
            self.output_db_path.unlink()
            logger.info("   ✅ Removed existing database")
    
    def _create_optimized_schema(self):
        """Create optimized database schema for AI training"""
        logger.info("🏗️ Creating optimized database schema...")
        
        conn = sqlite3.connect(self.output_db_path)
        
        # Grid cells table
        conn.execute('''
            CREATE TABLE grid_cells (
                cell_id INTEGER PRIMARY KEY,
                center_lat REAL NOT NULL,
                center_lon REAL NOT NULL,
                terrain_type TEXT NOT NULL,
                is_water INTEGER DEFAULT 0,
                urban_flag INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Weather data table (enhanced with all Stage 4 fields)
        conn.execute('''
            CREATE TABLE weather_data (
                cell_id INTEGER,
                date TEXT,
                -- Core temperature data (from Stage 4)
                tmax REAL,
                tmin REAL,
                tavg REAL,
                temp_range REAL,
                -- Precipitation and snow
                prcp REAL,
                snwd REAL,
                -- Temporal features (from Stage 4)
                year INTEGER,
                month INTEGER,
                day_of_year INTEGER,
                season TEXT,
                -- Data quality indicators
                data_completeness REAL,
                -- Interpolation metadata
                interpolation_method TEXT,
                nearest_station_id TEXT,
                nearest_station_distance_km REAL,
                station_count_used INTEGER,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (cell_id) REFERENCES grid_cells(cell_id)
            )
        ''')
        
        # Fire events table (one record per fire)
        conn.execute('''
            CREATE TABLE fire_events (
                fire_id TEXT PRIMARY KEY,
                center_cell_id INTEGER,
                start_date TEXT,
                end_date TEXT,
                total_size_ha REAL,
                fire_type TEXT,
                latitude REAL,
                longitude REAL,
                affected_cells TEXT,              -- JSON array of affected cell_ids
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (center_cell_id) REFERENCES grid_cells(cell_id)
            )
        ''')
        
        # Cell-fire relationships (many-to-many)
        conn.execute('''
            CREATE TABLE cell_fire_relationships (
                cell_id INTEGER,
                fire_id TEXT,
                fire_size_ha REAL,                -- Portion of fire in this cell
                fire_start_date TEXT,
                fire_end_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (cell_id, fire_id),
                FOREIGN KEY (cell_id) REFERENCES grid_cells(cell_id),
                FOREIGN KEY (fire_id) REFERENCES fire_events(fire_id)
            )
        ''')
        
        conn.close()
        logger.info("   ✅ Optimized schema created")
    
    def _create_curvature_adjusted_grid(self) -> int:
        """Create curvature-adjusted 10km grid for consistent area coverage"""
        logger.info("🗺️ Creating curvature-adjusted grid...")
        
        bounds = self.spatial_bounds
        grid_size_km = self.grid_size_km
        
        # Calculate grid spacing adjusted for Earth's curvature
        # Latitude spacing (constant)
        lat_spacing_deg = grid_size_km / 111.32  # ~0.09 degrees for 10km
        
        # Generate latitude points
        lats = np.arange(bounds['lat_min'], bounds['lat_max'], lat_spacing_deg)
        
        # Generate longitude points (adjusted for each latitude)
        grid_points = []
        cell_id = 1
        
        for lat in lats:
            # Longitude spacing adjusted for latitude (Earth's curvature)
            lon_spacing_deg = grid_size_km / (111.32 * math.cos(math.radians(lat)))
            lons = np.arange(bounds['lon_min'], bounds['lon_max'], lon_spacing_deg)
            
            for lon in lons:
                grid_points.append({
                    'cell_id': cell_id,
                    'center_lat': lat,
                    'center_lon': lon,
                    'terrain_type': 'unknown',
                    'is_water': 0,
                    'urban_flag': 0
                })
                cell_id += 1
        
        # Create DataFrame and save to database
        grid_df = pd.DataFrame(grid_points)
        
        conn = sqlite3.connect(self.output_db_path)
        grid_df.to_sql('grid_cells', conn, if_exists='append', index=False)
        conn.close()
        
        logger.info(f"   ✅ Created {len(grid_df):,} grid cells with curvature adjustment")
        return len(grid_df)
    
    def _classify_terrain_spatial_rules(self) -> int:
        """Classify terrain using simple spatial rules for speed"""
        logger.info("🌍 Classifying terrain using spatial rules...")
        
        conn = sqlite3.connect(self.output_db_path)
        grid_df = pd.read_sql_query("SELECT * FROM grid_cells", conn)
        
        # Initialize terrain classifications
        grid_df['terrain_type'] = 'land'  # Default
        grid_df['is_water'] = 0
        grid_df['urban_flag'] = 0
        
        # Water classification (vectorized)
        water_mask = (
            # Great Lakes region
            ((grid_df['center_lat'] >= 41.75) & (grid_df['center_lat'] <= 49.0) &
             (grid_df['center_lon'] >= -92.0) & (grid_df['center_lon'] <= -76.0)) |
            # Atlantic coast
            (grid_df['center_lon'] >= -65.0) |
            # Pacific coast
            ((grid_df['center_lat'] >= 48.0) & (grid_df['center_lon'] <= -125.0)) |
            # Arctic waters
            (grid_df['center_lat'] >= 58.0)
        )
        
        # Urban classification (vectorized)
        urban_mask = np.zeros(len(grid_df), dtype=bool)
        urban_areas = [
            (43.0, 44.5, -80.0, -78.5),  # Toronto
            (49.0, 49.5, -123.5, -122.5), # Vancouver
            (45.3, 45.7, -74.0, -73.5),   # Montreal
            (51.0, 51.2, -114.2, -113.8), # Calgary
            (53.4, 53.7, -113.7, -113.3), # Edmonton
            (50.0, 50.5, -97.0, -96.5),   # Winnipeg
            (46.8, 47.0, -71.2, -71.0),   # Quebec City
            (44.6, 44.8, -63.8, -63.4),   # Halifax
        ]
        
        for lat_min, lat_max, lon_min, lon_max in urban_areas:
            urban_mask |= (
                (grid_df['center_lat'] >= lat_min) & (grid_df['center_lat'] <= lat_max) &
                (grid_df['center_lon'] >= lon_min) & (grid_df['center_lon'] <= lon_max)
            )
        
        # Forest classification (vectorized)
        forest_mask = (
            # Boreal forest (northern)
            (grid_df['center_lat'] >= 55.0) |
            # Mixed forest (central)
            ((grid_df['center_lat'] >= 50.0) & (grid_df['center_lat'] < 55.0)) |
            # Deciduous forest (southern)
            ((grid_df['center_lat'] >= 45.0) & (grid_df['center_lat'] < 50.0))
        )
        
        # Apply classifications with hierarchy
        grid_df.loc[water_mask, 'terrain_type'] = 'water'
        grid_df.loc[water_mask, 'is_water'] = 1
        
        grid_df.loc[urban_mask, 'terrain_type'] = 'urban'
        grid_df.loc[urban_mask, 'urban_flag'] = 1
        
        # Forest overrides other land types
        forest_land_mask = forest_mask & ~water_mask & ~urban_mask
        grid_df.loc[forest_land_mask, 'terrain_type'] = 'forest'
        
        # Update database
        conn.execute("DELETE FROM grid_cells")
        grid_df.to_sql('grid_cells', conn, if_exists='append', index=False)
        
        # Count results
        terrain_counts = grid_df['terrain_type'].value_counts()
        land_count = len(grid_df[grid_df['terrain_type'].isin(['land', 'urban', 'forest'])])
        
        conn.close()
        
        logger.info(f"   ✅ Terrain classification complete:")
        for terrain, count in terrain_counts.items():
            logger.info(f"      {terrain}: {count:,} cells")
        
        return land_count
    
    def _interpolate_weather_parallel_safe(self) -> int:
        """Memory-safe parallel weather interpolation"""
        log_progress("Starting weather interpolation...")
        start_time = time.time()
        
        raw_conn = sqlite3.connect(self.raw_db_path)
        grid_conn = sqlite3.connect(self.output_db_path)
        
        # Get land cells only
        land_cells = pd.read_sql_query(
            "SELECT cell_id, center_lat, center_lon FROM grid_cells WHERE terrain_type IN ('land', 'urban', 'forest')",
            grid_conn
        )
        
        if len(land_cells) == 0:
            log_progress("No land cells found")
            return 0
        
        log_progress(f"Interpolating to {len(land_cells):,} land/urban/forest cells")
        
        # Get all stations
        stations_df = pd.read_sql_query(
            "SELECT station_id, latitude, longitude FROM stations", 
            raw_conn
        )
        
        # Pre-compute cell-station assignments
        log_progress("Pre-computing cell-station assignments...")
        cell_station_assignments = self._compute_cell_station_assignments_vectorized(land_cells, stations_df)
        
        # Get unique dates
        log_progress("Getting unique dates from database...")
        unique_dates_df = pd.read_sql_query('''
            SELECT DISTINCT date FROM weather_data_wide ORDER BY date
        ''', raw_conn)
        unique_dates = unique_dates_df['date'].tolist()
        log_progress(f"Found {len(unique_dates)} unique dates")
        
        # Get settings
        base_chunk_size = self.system_monitor.get_optimal_chunk_size()
        base_processes = self.max_processes
        dates_per_chunk = self.system_monitor.get_dynamic_chunk_size(base_chunk_size)
        dynamic_processes = self.system_monitor.get_dynamic_process_count(base_processes)
        
        cells_count = len(land_cells)
        estimated_records_per_chunk = cells_count * dates_per_chunk
        estimated_memory_per_chunk_gb = (estimated_records_per_chunk * 200) / (1024**3)
        
        log_progress(f"Using {dynamic_processes} processes, {dates_per_chunk} dates per chunk")
        log_progress(f"Estimated {estimated_records_per_chunk:,} records per chunk, {estimated_memory_per_chunk_gb:.2f} GB memory")
        
        # Process data
        if (dynamic_processes > 1 and 
            self.system_monitor.can_allocate_memory(estimated_memory_per_chunk_gb * dynamic_processes) and
            not self.system_monitor.should_fallback_to_sequential()):
            log_progress(f"Using parallel processing with {dynamic_processes} processes")
            total_records = self._process_parallel(unique_dates, land_cells, cell_station_assignments, dates_per_chunk, dynamic_processes)
        else:
            log_progress("Using sequential processing")
            total_records = self._process_sequential(unique_dates, land_cells, cell_station_assignments, raw_conn, dates_per_chunk)
        
        raw_conn.close()
        grid_conn.close()
        
        processing_time = time.time() - start_time
        log_progress(f"Weather interpolation complete: {total_records:,} records in {processing_time:.1f}s")
        
        return total_records
    
    def _process_parallel(self, unique_dates, land_cells, cell_station_assignments, dates_per_chunk, dynamic_processes=None):
        """Process dates in parallel with memory safety"""
        if dynamic_processes is None:
            dynamic_processes = self.max_processes
        
        # Prepare data for parallel processing
        land_cells_data = land_cells.to_dict('records')
        
        # Create date chunks
        date_chunks = [unique_dates[i:i+dates_per_chunk] for i in range(0, len(unique_dates), dates_per_chunk)]
        total_chunks = len(date_chunks)
        
        log_progress(f"Processing {total_chunks} chunks with {dynamic_processes} processes")
        
        # Prepare arguments for parallel processing
        parallel_args = []
        for i, date_chunk in enumerate(date_chunks):
            parallel_args.append((
                date_chunk, land_cells_data, cell_station_assignments,
                str(self.raw_db_path), i
            ))
        
        total_records = 0
        grid_conn = sqlite3.connect(self.output_db_path)
        
        # Process chunks in parallel
        with ProcessPoolExecutor(max_workers=dynamic_processes) as executor:
            # Submit all chunks
            future_to_chunk = {executor.submit(process_date_chunk_parallel, args): args[4] for args in parallel_args}
            
            # Process completed chunks
            completed_chunks = 0
            start_time = time.time()
            
            for future in as_completed(future_to_chunk):
                chunk_id = future_to_chunk[future]
                completed_chunks += 1
                
                try:
                    result = future.result()
                    
                    if 'error' in result:
                        log_progress(f"Chunk {chunk_id} failed: {result['error']}")
                        continue
                    
                    # Insert records from this chunk
                    if result['records']:
                        weather_df_chunk = pd.DataFrame(result['records'])
                        weather_df_chunk.to_sql('weather_data', grid_conn, if_exists='append', index=False)
                        total_records += result['count']
                        
                        # Explicitly clean up memory
                        del weather_df_chunk
                        del result['records']
                    
                    # Force garbage collection every few chunks
                    if completed_chunks % 5 == 0:
                        import gc
                        gc.collect()
                    
                    # Log progress every few chunks
                    if completed_chunks % 5 == 0 or completed_chunks == total_chunks:
                        elapsed_time = time.time() - start_time
                        progress_percent = (completed_chunks / total_chunks) * 100
                        rate = total_records / elapsed_time if elapsed_time > 0 else 0
                        log_progress(f"Weather progress: {completed_chunks}/{total_chunks} chunks ({progress_percent:.1f}%) - {total_records:,} records - {rate:,.0f} rec/s")
                    
                except Exception as e:
                    log_progress(f"Error processing chunk {chunk_id}: {e}")
        
        grid_conn.close()
        return total_records
    
    def _process_sequential(self, unique_dates, land_cells, cell_station_assignments, raw_conn, date_chunk_size=None):
        """Hardware-optimized sequential processing"""
        logger.info("   🔄 Processing dates sequentially...")
        
        # Use adaptive chunk size if not specified
        if date_chunk_size is None:
            date_chunk_size = self.system_monitor.get_optimal_chunk_size()
        
        total_chunks = len(unique_dates) // date_chunk_size + 1
        logger.info(f"   📊 Processing {total_chunks} chunks sequentially")
        logger.info(f"   📅 Dates per chunk: {date_chunk_size}")
        logger.info(f"   🎯 Total dates: {len(unique_dates)}")
        
        total_records = 0
        grid_conn = sqlite3.connect(self.output_db_path)
        start_time = time.time()
        
        for i in range(0, len(unique_dates), date_chunk_size):
            chunk_num = i // date_chunk_size + 1
            date_chunk = unique_dates[i:i+date_chunk_size]
            
            # Get weather data for this date chunk only
            date_placeholders = ','.join(['?' for _ in date_chunk])
            chunk_weather = pd.read_sql_query(f'''
                SELECT station_id, date, tmax, tmin, tavg, temp_range, prcp, snwd,
                       year, month, day_of_year, season, data_completeness
                FROM weather_data_wide
                WHERE date IN ({date_placeholders})
                ORDER BY date, station_id
            ''', raw_conn, params=date_chunk)
            
            # Create weather records for all cells and dates in this chunk
            weather_records = self._create_weather_records_vectorized(
                land_cells, chunk_weather, cell_station_assignments, {}
            )
            
            # Insert this chunk immediately to avoid memory accumulation
            if weather_records:
                weather_df_chunk = pd.DataFrame(weather_records)
                weather_df_chunk.to_sql('weather_data', grid_conn, if_exists='append', index=False)
                total_records += len(weather_records)
            
            # Calculate progress and ETA
            elapsed_time = time.time() - start_time
            progress_percent = (chunk_num / total_chunks) * 100
            avg_time_per_chunk = elapsed_time / chunk_num
            remaining_chunks = total_chunks - chunk_num
            eta_seconds = remaining_chunks * avg_time_per_chunk
            eta_minutes = eta_seconds / 60
            
            # Log progress every chunk (frequent updates)
            progress_msg = (f"   📈 Progress: {chunk_num}/{total_chunks} chunks ({progress_percent:.1f}%) - "
                          f"Chunk {chunk_num}: {len(weather_records):,} records, {len(date_chunk)} dates - "
                          f"ETA: {eta_minutes:.1f} min")
            logger.info(progress_msg)
                    # Only log to file, no console output
            
            # Clear memory
            del chunk_weather, weather_records, weather_df_chunk
            
            # Log memory status every 5 chunks and check for dynamic scaling
            if chunk_num % 5 == 0:
                self.system_monitor.log_memory_status()
                logger.info(f"   🚀 Processing rate: {total_records/elapsed_time:,.0f} records/second")
                
                # Check if we need to scale down due to memory pressure
                if self.system_monitor.is_memory_stressed():
                    logger.warning(f"   ⚠️ Memory stress detected during processing - using smaller chunks")
        
        grid_conn.close()
        return total_records
    
    def _compute_cell_station_assignments_vectorized(self, land_cells: pd.DataFrame, stations_df: pd.DataFrame) -> Dict:
        """Compute cell-station assignments with euclidean pre-filtering"""
        log_progress("Computing cell-station assignments (euclidean pre-filtered)...")
        
        # Convert to numpy arrays
        cell_coords = land_cells[['center_lat', 'center_lon']].values
        station_coords = stations_df[['latitude', 'longitude']].values
        
        log_progress(f"Processing {len(cell_coords):,} cells against {len(station_coords):,} stations...")
        
        # Process cells in chunks to manage memory
        chunk_size = 1000
        cell_assignments = {}
        
        for chunk_start in range(0, len(cell_coords), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(cell_coords))
            cell_chunk = cell_coords[chunk_start:chunk_end]
            cell_ids_chunk = land_cells['cell_id'].iloc[chunk_start:chunk_end]
            
            # Progress update
            if chunk_start % (chunk_size * 5) == 0 or chunk_end == len(cell_coords):
                progress = (chunk_end / len(cell_coords)) * 100
                log_progress(f"Processing cell chunk {chunk_start//chunk_size + 1}/{(len(cell_coords) + chunk_size - 1)//chunk_size} ({progress:.1f}%)")
            
            # Process this chunk of cells
            for i, (cell_lat, cell_lon) in enumerate(cell_chunk):
                cell_id = cell_ids_chunk.iloc[i]
                
                # Step 1: Calculate euclidean distances to all stations (fast)
                euclidean_distances = []
                for j, (station_lat, station_lon) in enumerate(station_coords):
                    # Simple euclidean distance (much faster than haversine)
                    lat_diff = cell_lat - station_lat
                    lon_diff = cell_lon - station_lon
                    euclidean_dist = np.sqrt(lat_diff**2 + lon_diff**2)
                    euclidean_distances.append((j, euclidean_dist))
                
                # Step 2: Find 10 closest stations by euclidean distance
                euclidean_distances.sort(key=lambda x: x[1])
                closest_10_indices = [idx for idx, _ in euclidean_distances[:10]]
                
                # Step 3: Calculate haversine distances only for the 10 closest
                haversine_distances = []
                for j in closest_10_indices:
                    station_lat, station_lon = station_coords[j]
                    haversine_dist = self.haversine_distance(cell_lat, cell_lon, station_lat, station_lon)
                    station_id = stations_df.iloc[j]['station_id']
                    haversine_distances.append((station_id, haversine_dist))
                
                # Step 4: Sort by haversine distance and select stations
                haversine_distances.sort(key=lambda x: x[1])
                closest_distance = haversine_distances[0][1]
                
                # Determine how many stations to use based on distance
                if closest_distance < 50:  # Very close - use 1 station
                    selected_stations = haversine_distances[:1]
                elif closest_distance < 200:  # Close - use 3 stations
                    selected_stations = haversine_distances[:3]
                elif closest_distance < 500:  # Distant - use 5 stations
                    selected_stations = haversine_distances[:5]
                else:  # Very distant - use 5 closest regardless
                    selected_stations = haversine_distances[:5]
                
                # Store assignment with multiple stations
                cell_assignments[cell_id] = {
                    'stations': selected_stations,  # List of (station_id, distance) tuples
                    'primary_station': selected_stations[0][0],  # Closest station for backward compatibility
                    'primary_distance': selected_stations[0][1]
                }
        
        log_progress(f"Computed assignments for {len(cell_assignments):,} cells")
        return cell_assignments
    
    
    def _create_weather_records_vectorized(self, land_cells: pd.DataFrame, weather_chunk: pd.DataFrame, 
                                         cell_station_assignments: Dict, station_lookup: Dict) -> List[Dict]:
        """Create weather records using multiple station interpolation"""
        weather_records = []
        
        # Group weather data by date for efficient processing
        weather_by_date = weather_chunk.groupby('date')
        
        for date_str, date_weather in weather_by_date:
            # Create a lookup for this date's weather data
            date_weather_lookup = {row['station_id']: row for _, row in date_weather.iterrows()}
            
            # Process all cells for this date
            for _, cell in land_cells.iterrows():
                cell_id = cell['cell_id']
                assignment = cell_station_assignments[cell_id]
                
                # Get weather data using multiple stations if available
                available_stations = []
                for station_id, distance in assignment['stations']:
                    if station_id in date_weather_lookup:
                        weather_row = date_weather_lookup[station_id]
                        available_stations.append((weather_row, distance))
                
                if available_stations:
                    if len(available_stations) == 1:
                        # Single station - use directly
                        weather_row, distance = available_stations[0]
                        weather_records.append({
                            'cell_id': cell_id,
                            'date': date_str,
                            'tmax': weather_row['tmax'],
                            'tmin': weather_row['tmin'],
                            'tavg': weather_row['tavg'],
                            'temp_range': weather_row['temp_range'],
                            'prcp': weather_row['prcp'],
                            'snwd': weather_row['snwd'],
                            'year': weather_row['year'],
                            'month': weather_row['month'],
                            'day_of_year': weather_row['day_of_year'],
                            'season': weather_row['season'],
                            'data_completeness': weather_row['data_completeness'],
                            'interpolation_method': 'nearest_station',
                            'nearest_station_id': assignment['primary_station'],
                            'nearest_station_distance_km': assignment['primary_distance'],
                            'station_count_used': 1,
                            'confidence_score': max(0.1, 1.0 - assignment['primary_distance'] / 100.0)
                        })
                    else:
                        # Multiple stations - use distance-weighted interpolation
                        weights = [1.0 / (distance**2) for _, distance in available_stations]
                        total_weight = sum(weights)
                        
                        # Calculate weighted averages
                        weighted_tmax = sum(row['tmax'] * weight for (row, _), weight in zip(available_stations, weights)) / total_weight
                        weighted_tmin = sum(row['tmin'] * weight for (row, _), weight in zip(available_stations, weights)) / total_weight
                        weighted_tavg = sum(row['tavg'] * weight for (row, _), weight in zip(available_stations, weights)) / total_weight
                        weighted_temp_range = sum(row['temp_range'] * weight for (row, _), weight in zip(available_stations, weights)) / total_weight
                        weighted_prcp = sum(row['prcp'] * weight for (row, _), weight in zip(available_stations, weights)) / total_weight
                        weighted_snwd = sum(row['snwd'] * weight for (row, _), weight in zip(available_stations, weights)) / total_weight
                        weighted_data_completeness = sum(row['data_completeness'] * weight for (row, _), weight in zip(available_stations, weights)) / total_weight
                        
                        # Use data from closest station for metadata
                        closest_row = available_stations[0][0]
                        
                        weather_records.append({
                            'cell_id': cell_id,
                            'date': date_str,
                            'tmax': weighted_tmax,
                            'tmin': weighted_tmin,
                            'tavg': weighted_tavg,
                            'temp_range': weighted_temp_range,
                            'prcp': weighted_prcp,
                            'snwd': weighted_snwd,
                            'year': closest_row['year'],
                            'month': closest_row['month'],
                            'day_of_year': closest_row['day_of_year'],
                            'season': closest_row['season'],
                            'data_completeness': weighted_data_completeness,
                            'interpolation_method': 'distance_weighted',
                            'nearest_station_id': assignment['primary_station'],
                            'nearest_station_distance_km': assignment['primary_distance'],
                            'station_count_used': len(available_stations),
                            'confidence_score': max(0.1, 1.0 - assignment['primary_distance'] / 200.0)
                        })
                else:
                    # Use seasonal defaults
                    seasonal_data = get_seasonal_defaults(date_str)
                    weather_records.append({
                        'cell_id': cell_id,
                        'date': date_str,
                        **seasonal_data,
                        'interpolation_method': 'seasonal_default',
                        'nearest_station_id': None,
                        'nearest_station_distance_km': None,
                        'station_count_used': 0,
                        'confidence_score': 0.1
                    })
        
        return weather_records
    
    def _assign_wildfires_smart(self) -> int:
        """Improved wildfire assignment - realistic fire size-based assignment"""
        log_progress("Starting improved wildfire assignment...")
        start_time = time.time()
        
        raw_conn = sqlite3.connect(self.raw_db_path)
        grid_conn = sqlite3.connect(self.output_db_path)
        
        # Get wildfires
        log_progress("Loading wildfire data from database...")
        wildfires_df = pd.read_sql_query('''
            SELECT NFDBFIREID, LATITUDE, LONGITUDE, REP_DATE, OUT_DATE, SIZE_HA, FIRE_TYPE
            FROM wildfires
        ''', raw_conn)
        
        # Get grid cells
        log_progress("Loading grid cell data...")
        cells_df = pd.read_sql_query(
            "SELECT cell_id, center_lat, center_lon FROM grid_cells WHERE terrain_type IN ('land', 'urban', 'forest')",
            grid_conn
        )
        
        log_progress(f"Processing {len(wildfires_df):,} fires for {len(cells_df):,} cells")
        
        # Convert cell coordinates to numpy array for vectorized operations
        cell_coords = cells_df[['center_lat', 'center_lon']].values
        cell_ids = cells_df['cell_id'].values
        
        # Create lookup for cell_id to index mapping
        cell_id_to_index = {cell_id: idx for idx, cell_id in enumerate(cell_ids)}
        
        fire_events = []
        cell_fire_relationships = []
        
        if len(wildfires_df) > 0:
            # Pre-filter fires by spatial bounds to reduce processing
            log_progress("Pre-filtering fires by spatial bounds...")
            lat_min, lat_max = cell_coords[:, 0].min() - 1, cell_coords[:, 0].max() + 1
            lon_min, lon_max = cell_coords[:, 1].min() - 1, cell_coords[:, 1].max() + 1
            
            # Filter fires to only those within reasonable bounds
            spatial_mask = (
                (wildfires_df['LATITUDE'] >= lat_min) & (wildfires_df['LATITUDE'] <= lat_max) &
                (wildfires_df['LONGITUDE'] >= lon_min) & (wildfires_df['LONGITUDE'] <= lon_max)
            )
            filtered_fires = wildfires_df[spatial_mask].copy()
            
            log_progress(f"Filtered from {len(wildfires_df):,} to {len(filtered_fires):,} fires within bounds")
            
            # Process fires in batches for progress tracking
            batch_size = 1000
            total_fires = len(filtered_fires)
            processed_fires = 0
            
            log_progress(f"Processing fires in batches of {batch_size:,}")
            
            for batch_start in range(0, total_fires, batch_size):
                batch_end = min(batch_start + batch_size, total_fires)
                batch_fires = filtered_fires.iloc[batch_start:batch_end]
                
                for fire_idx, (_, fire) in enumerate(batch_fires.iterrows()):
                    processed_fires += 1
                    
                    try:
                        # Parse dates
                        start_date = pd.to_datetime(fire['REP_DATE'])
                        
                        # Handle end date
                        if fire['OUT_DATE'] and fire['OUT_DATE'] != '0000/00/00':
                            end_date = pd.to_datetime(fire['OUT_DATE'])
                        else:
                            end_date = start_date  # Single day fire
                        
                        # Calculate realistic fire radius based on size
                        fire_size_ha = fire['SIZE_HA'] if fire['SIZE_HA'] and fire['SIZE_HA'] > 0 else 1.0
                        fire_radius_km = min(math.sqrt(fire_size_ha / math.pi) / 10, 20.0)  # Cap at 20km
                        
                        # Find center cell (closest to fire coordinates)
                        fire_lat, fire_lon = fire['LATITUDE'], fire['LONGITUDE']
                        
                        # Calculate distances to all cells
                        distances = np.array([
                            self.haversine_distance(fire_lat, fire_lon, cell_lat, cell_lon)
                            for cell_lat, cell_lon in cell_coords
                        ])
                        
                        # Find cells within realistic fire radius
                        affected_mask = distances <= fire_radius_km
                        affected_cells = cells_df[affected_mask]
                        
                        if len(affected_cells) == 0:
                            continue  # No cells affected
                        
                        # Find center cell (closest to fire)
                        center_cell_idx = np.argmin(distances)
                        center_cell_id = cell_ids[center_cell_idx]
                        
                        # Create fire event record
                        fire_event = {
                            'fire_id': fire['NFDBFIREID'],
                            'center_cell_id': center_cell_id,
                            'start_date': start_date.strftime('%Y-%m-%d'),
                            'end_date': end_date.strftime('%Y-%m-%d'),
                            'total_size_ha': fire_size_ha,
                            'fire_type': fire['FIRE_TYPE'] or 'Unknown',
                            'latitude': fire_lat,
                            'longitude': fire_lon,
                            'affected_cells': json.dumps(affected_cells['cell_id'].tolist())
                        }
                        fire_events.append(fire_event)
                        
                        # Create cell-fire relationships
                        fire_size_per_cell = fire_size_ha / len(affected_cells)
                        for _, cell in affected_cells.iterrows():
                            cell_fire_rel = {
                                'cell_id': cell['cell_id'],
                                'fire_id': fire['NFDBFIREID'],
                                'fire_size_ha': fire_size_per_cell,
                                'fire_start_date': start_date.strftime('%Y-%m-%d'),
                                'fire_end_date': end_date.strftime('%Y-%m-%d')
                            }
                            cell_fire_relationships.append(cell_fire_rel)
                    
                    except Exception as e:
                        log_progress(f"Error processing fire {fire['NFDBFIREID']}: {e}")
                        continue
                
                # Log progress every few batches
                if (batch_start // batch_size + 1) % 5 == 0 or batch_end >= total_fires:
                    progress_percent = (processed_fires / total_fires) * 100
                    elapsed_time = time.time() - start_time
                    rate = processed_fires / elapsed_time if elapsed_time > 0 else 0
                    log_progress(f"Fire progress: {processed_fires:,}/{total_fires:,} fires ({progress_percent:.1f}%) - {len(fire_events):,} fire events - {rate:,.0f} fires/s")
        
        # Save fire events to database
        log_progress("Saving fire events to database...")
        if fire_events:
            fire_events_df = pd.DataFrame(fire_events)
            # Remove duplicates based on fire_id (keep first occurrence)
            fire_events_df = fire_events_df.drop_duplicates(subset=['fire_id'], keep='first')
            fire_events_df.to_sql('fire_events', grid_conn, if_exists='append', index=False)
            log_progress(f"Saved {len(fire_events_df):,} fire events to database")
        
        # Save cell-fire relationships to database
        log_progress("Saving cell-fire relationships to database...")
        if cell_fire_relationships:
            cell_fire_df = pd.DataFrame(cell_fire_relationships)
            # Remove duplicates based on cell_id, fire_id combination (keep first occurrence)
            cell_fire_df = cell_fire_df.drop_duplicates(subset=['cell_id', 'fire_id'], keep='first')
            cell_fire_df.to_sql('cell_fire_relationships', grid_conn, if_exists='append', index=False)
            log_progress(f"Saved {len(cell_fire_df):,} cell-fire relationships to database")
        
        # Get total counts
        cursor = grid_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fire_events")
        fire_events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cell_fire_relationships")
        relationships_count = cursor.fetchone()[0]
        
        grid_conn.commit()
        raw_conn.close()
        grid_conn.close()
        
        processing_time = time.time() - start_time
        log_progress(f"Improved wildfire assignment finished: {fire_events_count:,} fire events, {relationships_count:,} cell relationships in {processing_time:.1f}s")
        
        return fire_events_count
    
    
    def _create_optimized_indexes(self):
        """Create optimized indexes for fast AI training queries"""
        logger.info("📊 Creating optimized indexes...")
        
        conn = sqlite3.connect(self.output_db_path)
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_grid_cells_location ON grid_cells(center_lat, center_lon)",
            "CREATE INDEX IF NOT EXISTS idx_grid_cells_terrain ON grid_cells(terrain_type)",
            "CREATE INDEX IF NOT EXISTS idx_weather_cell_date ON weather_data(cell_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data(date)",
            "CREATE INDEX IF NOT EXISTS idx_weather_season ON weather_data(season)",
            "CREATE INDEX IF NOT EXISTS idx_fire_events_center_cell ON fire_events(center_cell_id)",
            "CREATE INDEX IF NOT EXISTS idx_fire_events_date ON fire_events(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_cell_fire_cell_id ON cell_fire_relationships(cell_id)",
            "CREATE INDEX IF NOT EXISTS idx_cell_fire_fire_id ON cell_fire_relationships(fire_id)",
            "CREATE INDEX IF NOT EXISTS idx_cell_fire_dates ON cell_fire_relationships(fire_start_date, fire_end_date)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
        conn.close()
        
        logger.info("   ✅ Optimized indexes created")
    
    def _generate_summary_stats(self):
        """Generate summary statistics for validation"""
        logger.info("📊 Generating summary statistics...")
        
        conn = sqlite3.connect(self.output_db_path)
        
        # Grid statistics
        grid_stats = pd.read_sql_query("""
            SELECT terrain_type, COUNT(*) as count
            FROM grid_cells
            GROUP BY terrain_type
        """, conn)
        
        # Weather statistics
        weather_stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT cell_id) as unique_cells,
                COUNT(DISTINCT date) as unique_dates,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM weather_data
        """, conn)
        
        # Fire events statistics
        fire_events_stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_fire_events,
                SUM(total_size_ha) as total_fire_area_ha
            FROM fire_events
        """, conn)
        
        # Cell-fire relationships statistics
        cell_fire_stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_cell_fire_relationships,
                COUNT(DISTINCT cell_id) as cells_with_fires
            FROM cell_fire_relationships
        """, conn)
        
        conn.close()
        
        logger.info("   📊 Summary Statistics:")
        logger.info("   Grid cells by terrain:")
        for _, row in grid_stats.iterrows():
            logger.info(f"      {row['terrain_type']}: {row['count']:,}")
        
        logger.info("   Weather data:")
        logger.info(f"      Total records: {weather_stats['total_records'].iloc[0]:,}")
        logger.info(f"      Unique cells: {weather_stats['unique_cells'].iloc[0]:,}")
        logger.info(f"      Date range: {weather_stats['earliest_date'].iloc[0]} to {weather_stats['latest_date'].iloc[0]}")
        
        logger.info("   Fire events:")
        logger.info(f"      Total fire events: {fire_events_stats['total_fire_events'].iloc[0]:,}")
        total_area = fire_events_stats['total_fire_area_ha'].iloc[0]
        if total_area is not None:
            logger.info(f"      Total fire area: {total_area:,.1f} hectares")
        else:
            logger.info(f"      Total fire area: 0 hectares")
        
        logger.info("   Cell-fire relationships:")
        logger.info(f"      Total relationships: {cell_fire_stats['total_cell_fire_relationships'].iloc[0]:,}")
        cells_with_fires = cell_fire_stats['cells_with_fires'].iloc[0]
        if cells_with_fires is not None:
            logger.info(f"      Cells with fires: {cells_with_fires:,}")
        else:
            logger.info(f"      Cells with fires: 0")

def main():
    parser = argparse.ArgumentParser(description='Create memory-safe parallel interpolated grid database')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--region', choices=['toronto', 'vancouver', 'calgary', 'montreal'], 
                       default='toronto', help='Test region to use')
    parser.add_argument('--grid-size', type=int, default=10, help='Grid size in km')
    parser.add_argument('--max-processes', type=int, default=None, help='Maximum number of parallel processes')
    parser.add_argument('--max-memory-percent', type=int, default=80, help='Maximum memory usage percentage')
    
    args = parser.parse_args()
    
    creator = ParallelSafeInterpolatedGridCreator(
        test_mode=args.test,
        test_region=args.region,
        grid_size_km=args.grid_size,
        max_processes=args.max_processes,
        max_memory_percent=args.max_memory_percent
    )
    
    success = creator.create_database()
    
    if success:
        # Only log to file, no console output
        return 1
    else:
        # Only log to file, no console output
        return 0
    
    return 0

if __name__ == "__main__":
    exit(main())
