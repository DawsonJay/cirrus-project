#!/usr/bin/env python3
"""
Create Raw Weather and Wildfire Database (OPTIMIZED)
====================================================
Creates the raw_weather_db database schema and populates it with validated weather and wildfire data.
OPTIMIZED for speed: No pivot operation needed, pre-computed station-grid mappings, wide format tables.
"""

import sqlite3
import pandas as pd
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.spatial.distance import cdist
import sys
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../production/logs/raw_weather_db_creation.log'),
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
                'chunk_size': 1000,  # Very small chunks
                'memory_percent': 60,  # Very conservative memory usage
                'database_mode': 'sequential',  # No parallel DB writes
                'description': 'Raspberry Pi - Ultra-conservative settings for 1GB RAM'
            },
            'low_end': {
                'max_processes': 2,
                'chunk_size': 5000,
                'memory_percent': 70,
                'database_mode': 'sequential',
                'description': 'Low-end hardware - Small chunks, limited parallelism'
            },
            'mid_range': {
                'max_processes': 3,
                'chunk_size': 10000,
                'memory_percent': 75,
                'database_mode': 'parallel',
                'description': 'Mid-range hardware - Balanced performance and safety'
            },
            'high_end': {
                'max_processes': 4,
                'chunk_size': 20000,
                'memory_percent': 80,
                'description': 'High-end hardware - Maximum performance'
            },
            'enterprise': {
                'max_processes': min(8, self.cpu_count),
                'chunk_size': 50000,
                'memory_percent': 85,
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

class OptimizedRawWeatherDatabaseCreator:
    """Creates and populates the raw weather and wildfire database (OPTIMIZED)"""
    
    def __init__(self, data_dir="../../data", db_dir="../../databases"):
        self.data_dir = Path(data_dir)
        self.db_dir = Path(db_dir)
        self.validated_data_dir = self.data_dir / "validated_data"
        self.db_path = self.db_dir / "raw_weather_db.db"
        
        # Adaptive system monitoring
        self.system_monitor = AdaptiveSystemMonitor()
        
        # Input files
        self.weather_csv = self.validated_data_dir / "weather_records.csv"
        self.stations_csv = self.validated_data_dir / "stations.csv"
        self.inventory_csv = self.validated_data_dir / "station_inventory.csv"
        self.wildfire_csv = self.validated_data_dir / "wildfire_records.csv"
    
    def clear_existing_database(self):
        """Delete existing database if it exists for a clean start"""
        logger.info("🧹 Clearing existing database...")
        
        # Check memory before starting
        self.system_monitor.log_memory_status()
        
        if self.db_path.exists():
            self.db_path.unlink()
            logger.info(f"   ✅ Removed existing database: {self.db_path}")
        else:
            logger.info("   ℹ️ No existing database found")
    
    def create_database_schema(self):
        """Create optimized database schema with all required tables"""
        logger.info("🏗️ Creating optimized database schema...")
        
        # Ensure database directory exists
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Stations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                station_id TEXT PRIMARY KEY,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                elevation REAL,
                name TEXT,
                country TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Weather data table (wide format with enhanced features)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_data_wide (
                station_id TEXT NOT NULL,
                date DATE NOT NULL,
                tmax REAL,
                tmin REAL,
                tavg REAL,
                prcp REAL,
                snwd REAL,
                tmax_quality TEXT,
                tmin_quality TEXT,
                tavg_quality TEXT,
                prcp_quality TEXT,
                snwd_quality TEXT,
                -- Enhanced features for AI training
                temp_range REAL,           -- tmax - tmin (daily temperature range)
                year INTEGER,              -- extracted year
                month INTEGER,             -- extracted month
                day_of_year INTEGER,       -- day of year (1-366)
                season TEXT,               -- spring/summer/fall/winter
                data_completeness REAL,    -- fraction of non-null weather variables
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (station_id, date),
                FOREIGN KEY (station_id) REFERENCES stations(station_id)
            )
        """)
        
        # 3. Station inventory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS station_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id TEXT NOT NULL,
                variable TEXT NOT NULL,
                first_year INTEGER,
                last_year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (station_id) REFERENCES stations(station_id)
            )
        """)
        
        # 4. Wildfires table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wildfires (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                NFDBFIREID TEXT,
                SRC_AGENCY TEXT,
                FIRE_ID TEXT,
                FIRENAME TEXT,
                LATITUDE REAL NOT NULL,
                LONGITUDE REAL NOT NULL,
                YEAR INTEGER,
                MONTH INTEGER,
                DAY INTEGER,
                REP_DATE TEXT,
                ATTK_DATE TEXT,
                OUT_DATE TEXT,
                SIZE_HA REAL,
                CAUSE TEXT,
                CAUSE2 TEXT,
                FIRE_TYPE TEXT,
                RESPONSE TEXT,
                PROTZONE TEXT,
                PRESCRIBED TEXT,
                MORE_INFO TEXT,
                CFS_NOTE1 TEXT,
                CFS_NOTE2 TEXT,
                ACQ_DATE TEXT,
                layer TEXT,
                omit TEXT,
                geometry_wkt TEXT,
                fire_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        
        # 5. Station distance matrix (for ultra-fast interpolation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS station_distances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_1 TEXT NOT NULL,
                station_2 TEXT NOT NULL,
                distance_km REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (station_1) REFERENCES stations(station_id),
                FOREIGN KEY (station_2) REFERENCES stations(station_id)
            )
        """)
        
        # 6. Station nearest neighbors (for fast lookup)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS station_neighbors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id TEXT NOT NULL,
                neighbor_id TEXT NOT NULL,
                distance_km REAL NOT NULL,
                rank INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (station_id) REFERENCES stations(station_id),
                FOREIGN KEY (neighbor_id) REFERENCES stations(station_id)
            )
        """)
        
        # 7. Database metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for optimal performance
        logger.info("   📊 Creating optimized indexes...")
        
        # Weather data indexes (optimized for interpolation)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_station_date ON weather_data_wide(station_id, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data_wide(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_station ON weather_data_wide(station_id)")
        
        # Station indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stations_location ON stations(latitude, longitude)")
        
        
        # Wildfire indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wildfires_location ON wildfires(LATITUDE, LONGITUDE)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wildfires_date ON wildfires(fire_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wildfires_year ON wildfires(YEAR)")
        
        # Station distance indexes (critical for fast interpolation)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_distances_station1 ON station_distances(station_1)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_distances_station2 ON station_distances(station_2)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_distances_both ON station_distances(station_1, station_2)")
        
        # Station neighbors indexes (critical for fast lookup)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_neighbors_station ON station_neighbors(station_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_neighbors_rank ON station_neighbors(station_id, rank)")
        
        conn.commit()
        conn.close()
        
        logger.info("   ✅ Database schema created with optimized indexes")
    
    def populate_stations(self):
        """Populate stations table from validated data"""
        logger.info("🏢 Populating stations table...")
        
        if not self.stations_csv.exists():
            raise Exception(f"Stations CSV not found: {self.stations_csv}")
        
        stations_df = pd.read_csv(self.stations_csv)
        
        conn = sqlite3.connect(self.db_path)
        stations_df.to_sql('stations', conn, if_exists='append', index=False)
        conn.close()
        
        logger.info(f"   ✅ Populated stations table with {len(stations_df):,} stations")
        return len(stations_df)
    
    def populate_weather_data_optimized(self):
        """Populate weather data table from wide format CSV (NO PIVOT NEEDED!)"""
        logger.info("🌡️ Populating weather data table (OPTIMIZED - no pivot)...")
        
        if not self.weather_csv.exists():
            raise Exception(f"Weather records CSV not found: {self.weather_csv}")
        
        logger.info("   🚀 Reading wide format weather data (NO PIVOT OPERATION!)...")
        
        # Use adaptive chunk size based on hardware
        chunk_size = self.system_monitor.get_optimal_chunk_size()
        logger.info(f"   🔧 Using adaptive chunk size: {chunk_size:,} records")
        
        # Check memory before starting
        self.system_monitor.log_memory_status()
        total_records = 0
        
        conn = sqlite3.connect(self.db_path)
        
        for chunk_idx, chunk in enumerate(pd.read_csv(self.weather_csv, chunksize=chunk_size)):
            # Ensure all required columns exist (fill missing with None)
            base_cols = ['station_id', 'date', 'tmax', 'tmin', 'tavg', 'prcp', 'snwd',
                        'tmax_quality', 'tmin_quality', 'tavg_quality', 'prcp_quality', 'snwd_quality']
            
            for col in base_cols:
                if col not in chunk.columns:
                    chunk[col] = None
            
            # Convert date to datetime for processing
            chunk['date'] = pd.to_datetime(chunk['date'])
            
            # Calculate enhanced features for AI training
            logger.info(f"      🔬 Computing enhanced features for chunk {chunk_idx + 1}...")
            
            # Temperature range (critical for AI models)
            chunk['temp_range'] = None
            temp_mask = chunk['tmax'].notna() & chunk['tmin'].notna()
            chunk.loc[temp_mask, 'temp_range'] = chunk.loc[temp_mask, 'tmax'] - chunk.loc[temp_mask, 'tmin']
            
            # Temporal features
            chunk['year'] = chunk['date'].dt.year
            chunk['month'] = chunk['date'].dt.month
            chunk['day_of_year'] = chunk['date'].dt.dayofyear
            
            # Season classification
            def get_season(month):
                if month in [12, 1, 2]:
                    return 'winter'
                elif month in [3, 4, 5]:
                    return 'spring'
                elif month in [6, 7, 8]:
                    return 'summer'
                else:
                    return 'fall'
            
            chunk['season'] = chunk['month'].apply(get_season)
            
            # Data completeness score (fraction of non-null weather variables)
            weather_vars = ['tmax', 'tmin', 'tavg', 'prcp', 'snwd']
            chunk['data_completeness'] = chunk[weather_vars].notna().sum(axis=1) / len(weather_vars)
            
            # Convert date back to string for database
            chunk['date'] = chunk['date'].dt.strftime('%Y-%m-%d')
            
            # Insert enhanced chunk into database
            chunk.to_sql('weather_data_wide', conn, if_exists='append', index=False)
            
            total_records += len(chunk)
            
            if (chunk_idx + 1) % 10 == 0:
                logger.info(f"      📈 Progress: {total_records:,} records processed")
        
        # Verify import
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM weather_data_wide")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"   ✅ Populated weather_data_wide table with {count:,} records (NO PIVOT OPERATION!)")
        return count
    
    def create_station_distance_matrix(self):
        """Pre-compute all station-to-station distances for ultra-fast interpolation"""
        logger.info("📏 Pre-computing station distance matrix...")
        
        # Check memory before starting
        self.system_monitor.log_memory_status()
        
        conn = sqlite3.connect(self.db_path)
        
        # Load all stations
        stations_df = pd.read_sql_query("SELECT station_id, latitude, longitude FROM stations", conn)
        logger.info(f"   📡 Computing distances for {len(stations_df):,} stations")
        
        # Calculate all pairwise distances
        from scipy.spatial.distance import pdist, squareform
        import numpy as np
        
        coords = stations_df[['latitude', 'longitude']].values
        
        # Compute distance matrix (in degrees, convert to km)
        logger.info("   🔄 Computing pairwise distances...")
        distances_deg = pdist(coords, metric='euclidean')
        distances_km = distances_deg * 111.32  # Rough conversion to km
        
        # Convert to square matrix
        distance_matrix = squareform(distances_km)
        
        # Create distance records (only store distances < 500km to save space)
        logger.info("   💾 Storing distance relationships...")
        distance_records = []
        
        for i, station_1 in enumerate(stations_df['station_id']):
            for j, station_2 in enumerate(stations_df['station_id']):
                if i != j:  # Don't store self-distances
                    distance = distance_matrix[i, j]
                    if distance < 500:  # Only store nearby stations
                        distance_records.append({
                            'station_1': station_1,
                            'station_2': station_2,
                            'distance_km': distance
                        })
        
        # Save distance matrix
        if distance_records:
            distances_df = pd.DataFrame(distance_records)
            distances_df.to_sql('station_distances', conn, if_exists='append', index=False)
            logger.info(f"   ✅ Stored {len(distance_records):,} station distance relationships")
        
        conn.close()
        return len(distance_records)
    
    def create_station_neighbor_lookup(self, max_neighbors=10):
        """Create fast lookup table for nearest neighbors of each station"""
        logger.info(f"🔍 Creating station neighbor lookup (top {max_neighbors} per station)...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get all stations
        stations_df = pd.read_sql_query("SELECT station_id FROM stations", conn)
        
        neighbor_records = []
        
        for station_id in stations_df['station_id']:
            # Get nearest neighbors for this station
            neighbors_df = pd.read_sql_query("""
                SELECT station_2 as neighbor_id, distance_km
                FROM station_distances
                WHERE station_1 = ?
                ORDER BY distance_km ASC
                LIMIT ?
            """, conn, params=[station_id, max_neighbors])
            
            # Add rank and create records
            for rank, (_, row) in enumerate(neighbors_df.iterrows(), 1):
                neighbor_records.append({
                    'station_id': station_id,
                    'neighbor_id': row['neighbor_id'],
                    'distance_km': row['distance_km'],
                    'rank': rank
                })
        
        # Save neighbor lookup
        if neighbor_records:
            neighbors_df = pd.DataFrame(neighbor_records)
            neighbors_df.to_sql('station_neighbors', conn, if_exists='append', index=False)
            logger.info(f"   ✅ Created neighbor lookup with {len(neighbor_records):,} relationships")
        
        conn.close()
        return len(neighbor_records)
    
    def populate_wildfire_data(self):
        """Populate wildfire data table from validated CSV"""
        logger.info("🔥 Populating wildfire data table...")
        
        if not self.wildfire_csv.exists():
            logger.warning("   ⚠️ Wildfire CSV not found, skipping...")
            return 0
        
        wildfire_df = pd.read_csv(self.wildfire_csv)
        
        conn = sqlite3.connect(self.db_path)
        wildfire_df.to_sql('wildfires', conn, if_exists='append', index=False)
        conn.close()
        
        logger.info(f"   ✅ Populated wildfires table with {len(wildfire_df):,} records")
        return len(wildfire_df)
    
    def add_database_metadata(self, stations_count, weather_count, wildfire_count, distance_count, neighbor_count):
        """Add metadata about the database creation"""
        logger.info("📝 Adding database metadata...")
        
        metadata = [
            ('creation_date', datetime.now().isoformat(), 'Database creation timestamp'),
            ('stations_count', str(stations_count), 'Number of weather stations'),
            ('weather_records_count', str(weather_count), 'Number of weather records'),
            ('wildfire_records_count', str(wildfire_count), 'Number of wildfire records'),
            ('station_distances_count', str(distance_count), 'Number of pre-computed station distances'),
            ('station_neighbors_count', str(neighbor_count), 'Number of pre-computed neighbor relationships'),
            ('format_version', 'optimized_v2', 'Database format version'),
            ('optimization_features', 'wide_format,no_pivot,enhanced_features,precomputed_distances,neighbor_lookup', 'Optimization features enabled')
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for key, value, description in metadata:
            cursor.execute("""
                INSERT OR REPLACE INTO db_metadata (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
        
        conn.commit()
        conn.close()
        
        logger.info("   ✅ Database metadata added")
    
    def run_optimized_creation(self):
        """Run the complete optimized database creation process"""
        logger.info("🚀 Starting OPTIMIZED raw weather database creation...")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Clear existing database
            self.clear_existing_database()
            
            # Step 2: Create schema
            self.create_database_schema()
            
            # Step 3: Populate stations
            stations_count = self.populate_stations()
            
            # Step 4: Populate weather data (OPTIMIZED with enhanced features)
            weather_count = self.populate_weather_data_optimized()
            
            # Step 5: Pre-compute station distances (CRITICAL for fast interpolation)
            distance_count = self.create_station_distance_matrix()
            
            # Step 6: Create neighbor lookup tables (CRITICAL for fast interpolation)
            neighbor_count = self.create_station_neighbor_lookup()
            
            # Step 7: Populate wildfire data
            wildfire_count = self.populate_wildfire_data()
            
            # Step 8: Add metadata
            self.add_database_metadata(stations_count, weather_count, wildfire_count, distance_count, neighbor_count)
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info("🎉 OPTIMIZED Database Creation Complete!")
            logger.info("=" * 60)
            logger.info(f"📊 Final Results:")
            logger.info(f"   Stations: {stations_count:,}")
            logger.info(f"   Weather records: {weather_count:,} (with enhanced features)")
            logger.info(f"   Wildfire records: {wildfire_count:,}")
            logger.info(f"   Station distances: {distance_count:,}")
            logger.info(f"   Neighbor relationships: {neighbor_count:,}")
            logger.info(f"⏱️ Total time: {duration:.1f} seconds")
            logger.info(f"🚀 Optimizations: Wide format, enhanced features, pre-computed distances")
            logger.info(f"💾 Database: {self.db_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database creation failed: {e}")
            return False

def main():
    """Main entry point"""
    creator = OptimizedRawWeatherDatabaseCreator()
    success = creator.run_optimized_creation()
    
    if success:
        print("✅ Optimized raw weather database created successfully!")
    else:
        print("❌ Database creation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
