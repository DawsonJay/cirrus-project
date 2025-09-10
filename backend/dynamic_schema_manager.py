#!/usr/bin/env python3
"""
Dynamic Schema Manager for NOAA Weather Data
Automatically expands database schema when new data types are encountered
"""

import sqlite3
import logging
from typing import Dict, List, Set
from app.config import settings

logger = logging.getLogger(__name__)

class DynamicSchemaManager:
    """Manages dynamic expansion of the weather data schema"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        
        # Known NOAA data types and their database column mappings
        self.known_data_types = {
            # Temperature
            'TMAX': 'temperature_max',
            'TMIN': 'temperature_min', 
            'TAVG': 'temperature_avg',
            
            # Precipitation
            'PRCP': 'precipitation',
            'SNOW': 'snowfall',
            'SNWD': 'snow_depth',
            
            # Wind
            'AWND': 'wind_speed_avg',
            'WSF2': 'wind_speed_max_2min',
            'WSF5': 'wind_speed_max_5min',
            'WSFG': 'wind_speed_gust',
            'WDF2': 'wind_direction_2min',
            'WDF5': 'wind_direction_5min',
            'WDFG': 'wind_direction_gust',
            
            # Sunshine
            'PSUN': 'sunshine_percent',
            'TSUN': 'sunshine_minutes',
            
            # Pressure
            'PRES': 'pressure',
            'SLP': 'sea_level_pressure',
            
            # Humidity
            'RHUM': 'relative_humidity',
            
            # Weather Types (WT codes)
            'WT01': 'weather_fog',
            'WT02': 'weather_heavy_fog',
            'WT03': 'weather_thunder',
            'WT04': 'weather_ice_pellets',
            'WT05': 'weather_hail',
            'WT06': 'weather_glaze',
            'WT07': 'weather_dust',
            'WT08': 'weather_smoke',
            'WT09': 'weather_blowing_snow',
            'WT10': 'weather_tornado',
            'WT11': 'weather_high_winds',
            'WT12': 'weather_blowing_spray',
            'WT13': 'weather_mist',
            'WT14': 'weather_drizzle',
            'WT15': 'weather_freezing_drizzle',
            'WT16': 'weather_rain',
            'WT17': 'weather_freezing_rain',
            'WT18': 'weather_snow',
            'WT19': 'weather_unknown_precipitation',
            'WT21': 'weather_ground_fog',
            'WT22': 'weather_ice_fog'
        }
        
        # Data type categories for organization
        self.data_categories = {
            'temperature': ['TMAX', 'TMIN', 'TAVG'],
            'precipitation': ['PRCP', 'SNOW', 'SNWD'],
            'wind': ['AWND', 'WSF2', 'WSF5', 'WSFG', 'WDF2', 'WDF5', 'WDFG'],
            'sunshine': ['PSUN', 'TSUN'],
            'pressure': ['PRES', 'SLP'],
            'humidity': ['RHUM'],
            'weather_types': [f'WT{i:02d}' for i in range(1, 23) if i not in [20]]  # WT01-WT22 except WT20
        }
    
    def get_column_name(self, data_type: str) -> str:
        """Get the database column name for a NOAA data type"""
        return self.known_data_types.get(data_type, f"data_{data_type.lower()}")
    
    def get_column_type(self, data_type: str) -> str:
        """Get the appropriate SQLite column type for a data type"""
        if data_type.startswith('WT'):
            return 'BOOLEAN'  # Weather types are boolean flags
        elif data_type in ['TMAX', 'TMIN', 'TAVG', 'PRCP', 'SNOW', 'SNWD', 'AWND', 'WSF2', 'WSF5', 'WSFG', 'WDF2', 'WDF5', 'WDFG', 'PSUN', 'TSUN', 'PRES', 'SLP', 'RHUM']:
            return 'REAL'  # Numeric values
        else:
            return 'REAL'  # Default to REAL for unknown numeric types
    
    def ensure_column_exists(self, data_type: str) -> bool:
        """Ensure a column exists for the given data type, create if it doesn't"""
        column_name = self.get_column_name(data_type)
        column_type = self.get_column_type(data_type)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute("PRAGMA table_info(daily_weather_data)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if column_name not in columns:
                logger.info(f"🔧 Adding new column: {column_name} ({column_type}) for data type {data_type}")
                cursor.execute(f"ALTER TABLE daily_weather_data ADD COLUMN {column_name} {column_type}")
                conn.commit()
                logger.info(f"✅ Added column {column_name}")
                return True
            else:
                logger.debug(f"✅ Column {column_name} already exists")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"❌ Error adding column {column_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def ensure_columns_for_data_types(self, data_types: Set[str]) -> List[str]:
        """Ensure columns exist for all given data types"""
        added_columns = []
        for data_type in data_types:
            if self.ensure_column_exists(data_type):
                added_columns.append(self.get_column_name(data_type))
        return added_columns
    
    def get_current_schema(self) -> Dict[str, str]:
        """Get the current schema of the daily_weather_data table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(daily_weather_data)")
            columns = {col[1]: col[2] for col in cursor.fetchall()}
            
            return columns
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error getting schema: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def create_comprehensive_schema(self):
        """Create a comprehensive schema with all known data types"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            logger.info("🔧 Creating comprehensive weather data schema...")
            
            # Ensure the table exists with basic structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id VARCHAR(50) NOT NULL,
                    date DATE NOT NULL,
                    source VARCHAR(50) NOT NULL DEFAULT 'noaa_cdo',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (station_id) REFERENCES weather_stations(station_id),
                    UNIQUE (station_id, date)
                )
            """)
            
            # Add all known data type columns
            added_columns = []
            for data_type, column_name in self.known_data_types.items():
                column_type = self.get_column_type(data_type)
                
                try:
                    cursor.execute(f"ALTER TABLE daily_weather_data ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    logger.info(f"✅ Added column: {column_name} ({column_type})")
                except sqlite3.Error as e:
                    if "duplicate column name" in str(e).lower():
                        logger.debug(f"✅ Column {column_name} already exists")
                    else:
                        logger.warning(f"⚠️  Could not add column {column_name}: {e}")
            
            conn.commit()
            logger.info(f"🎉 Comprehensive schema created with {len(added_columns)} new columns")
            
            return added_columns
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error creating comprehensive schema: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def analyze_data_types_in_database(self) -> Dict[str, int]:
        """Analyze what data types are actually being used in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current schema
            cursor.execute("PRAGMA table_info(daily_weather_data)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Count non-null values for each data column
            data_usage = {}
            for column in columns:
                if column not in ['id', 'station_id', 'date', 'source', 'created_at', 'updated_at']:
                    cursor.execute(f"SELECT COUNT(*) FROM daily_weather_data WHERE {column} IS NOT NULL")
                    count = cursor.fetchone()[0]
                    data_usage[column] = count
            
            return data_usage
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error analyzing data types: {e}")
            return {}
        finally:
            if conn:
                conn.close()

def main():
    """Test the dynamic schema manager"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = DynamicSchemaManager()
    
    print("🔧 Dynamic Schema Manager Test")
    print("=" * 50)
    
    # Create comprehensive schema
    added_columns = manager.create_comprehensive_schema()
    print(f"📊 Added {len(added_columns)} columns")
    
    # Show current schema
    schema = manager.get_current_schema()
    print(f"📋 Current schema has {len(schema)} columns")
    
    # Analyze data usage
    usage = manager.analyze_data_types_in_database()
    print(f"📈 Data usage analysis:")
    for column, count in usage.items():
        if count > 0:
            print(f"   {column}: {count} records")

if __name__ == "__main__":
    main()

