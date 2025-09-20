#!/usr/bin/env python3
"""
Stage 6: AI Training Data Generator
==================================
Generates high-quality training and testing datasets for AI wildfire prediction.

Key Features:
- Fixed comprehensive dataset (no data selection evolution)
- Historical patterns (1+ years older than target date)
- Geographic stratification across terrain types
- Balanced fire/no-fire examples
- Feature aggregation by pattern type
- Realistic prediction scenario simulation
"""

import sqlite3
import pandas as pd
import numpy as np
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json
import math
from typing import Dict, List, Tuple, Optional
import time
import warnings

warnings.filterwarnings('ignore')

def log_progress(message: str):
    """Simple progress logging"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")
    logger.info(message)

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrainingDataGenerator:
    """Generates training and testing datasets for AI wildfire prediction"""
    
    def __init__(self, db_path: str, output_dir: str = "../../ai/training"):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Training configuration
        self.training_targets = 500
        self.test_pool_size = 5000
        self.test_per_generation = 200
        
        # Geographic stratification
        self.terrain_stratification = {
            'forest': 0.40,    # 40% - most important for wildfires
            'land': 0.25,      # 25% - mixed terrain
            'urban': 0.20,     # 20% - urban areas
            'water': 0.15      # 15% - water cells (always no-fire, teaches AI water = no fire)
        }
        
        # Confidence thresholds by terrain
        self.confidence_thresholds = {
            'forest': 0.4,
            'land': 0.3,
            'urban': 0.7,
            'water': 0.1  # Much lower threshold since water cells are far from stations
        }
        
        # Pattern specifications
        self.yearly_window_days = 7  # ±7 days around same date
        self.spatial_neighbors = 8   # 8 surrounding cells
        self.historical_years = 3    # 3 years of historical data
        
        log_progress(f"🎯 Training Data Generator initialized")
        log_progress(f"   Database: {self.db_path}")
        log_progress(f"   Output: {self.output_dir}")
    
    def generate_training_data(self) -> bool:
        """Generate complete training and testing datasets"""
        start_time = time.time()
        
        log_progress("🚀 Starting Stage 6: AI Training Data Generation")
        
        try:
            # Step 1: Analyze database and select target cells
            log_progress("📊 Analyzing database and selecting target cells...")
            target_cells = self._select_target_cells()
            log_progress(f"   Selected {len(target_cells)} target cells")
            
            # Step 2: Generate training dataset
            log_progress("🎯 Generating training dataset...")
            training_data = self._generate_dataset(target_cells, dataset_type="training")
            log_progress(f"   Generated {len(training_data)} training samples")
            
            # Step 3: Generate testing pool
            log_progress("🧪 Generating testing pool...")
            test_pool = self._generate_dataset(target_cells, dataset_type="testing")
            log_progress(f"   Generated {len(test_pool)} test samples")
            
            # Step 4: Save datasets
            log_progress("💾 Saving datasets...")
            self._save_datasets(training_data, test_pool)
            
            # Step 5: Generate summary statistics
            log_progress("📈 Generating summary statistics...")
            self._generate_summary_stats(training_data, test_pool)
            
            processing_time = time.time() - start_time
            log_progress(f"✅ Stage 6 Complete: Training data generated in {processing_time:.1f}s")
            
            return True
            
        except Exception as e:
            log_progress(f"❌ Stage 6 Failed: {e}")
            logger.error(f"Training data generation failed: {e}", exc_info=True)
            return False
    
    def _select_target_cells(self) -> List[Dict]:
        """Select diverse target cells across terrain types with balanced fire/no-fire"""
        conn = sqlite3.connect(self.db_path)
        
        # Get cells with fire data first
        fire_cells_df = pd.read_sql_query("""
            SELECT DISTINCT
                gc.cell_id,
                gc.center_lat,
                gc.center_lon,
                gc.terrain_type,
                gc.is_water,
                gc.urban_flag,
                AVG(wd.confidence_score) as avg_confidence,
                COUNT(DISTINCT wd.date) as data_days,
                COUNT(DISTINCT cfr.fire_id) as fire_count
            FROM grid_cells gc
            JOIN cell_fire_relationships cfr ON gc.cell_id = cfr.cell_id
            LEFT JOIN weather_data wd ON gc.cell_id = wd.cell_id
            WHERE gc.terrain_type IN ('forest', 'land', 'urban', 'water')
            GROUP BY gc.cell_id, gc.center_lat, gc.center_lon, gc.terrain_type, gc.is_water, gc.urban_flag
            HAVING data_days >= 100
        """, conn)
        
        # Get cells without fire data (including water cells with no weather data requirement)
        # Split into two queries for better performance
        no_fire_land_cells_df = pd.read_sql_query("""
            SELECT 
                gc.cell_id,
                gc.center_lat,
                gc.center_lon,
                gc.terrain_type,
                gc.is_water,
                gc.urban_flag,
                AVG(wd.confidence_score) as avg_confidence,
                COUNT(DISTINCT wd.date) as data_days,
                0 as fire_count
            FROM grid_cells gc
            LEFT JOIN weather_data wd ON gc.cell_id = wd.cell_id
            LEFT JOIN cell_fire_relationships cfr ON gc.cell_id = cfr.cell_id
            WHERE gc.terrain_type IN ('forest', 'land', 'urban')
            AND cfr.cell_id IS NULL
            GROUP BY gc.cell_id, gc.center_lat, gc.center_lon, gc.terrain_type, gc.is_water, gc.urban_flag
            HAVING data_days >= 100
        """, conn)
        
        # Get water cells separately (no weather data requirement)
        # Just take the first 50 water cells - they're all the same anyway
        no_fire_water_cells_df = pd.read_sql_query("""
            SELECT 
                gc.cell_id,
                gc.center_lat,
                gc.center_lon,
                gc.terrain_type,
                gc.is_water,
                gc.urban_flag,
                0.0 as avg_confidence,
                0 as data_days,
                0 as fire_count
            FROM grid_cells gc
            WHERE gc.terrain_type = 'water'
            LIMIT 50  -- Just take first 50 - they're all identical for training
        """, conn)
        
        # Combine the results
        no_fire_cells_df = pd.concat([no_fire_land_cells_df, no_fire_water_cells_df], ignore_index=True)
        
        conn.close()
        
        log_progress(f"   Found {len(fire_cells_df)} cells with fires")
        log_progress(f"   Found {len(no_fire_cells_df)} cells without fires")
        
        if len(fire_cells_df) == 0:
            raise ValueError("No cells with fire data found in database")
        
        # Apply confidence filtering
        fire_cells_filtered = []
        no_fire_cells_filtered = []
        
        for terrain_type, threshold in self.confidence_thresholds.items():
            # Filter fire cells
            terrain_fire = fire_cells_df[fire_cells_df['terrain_type'] == terrain_type]
            terrain_fire = terrain_fire[terrain_fire['avg_confidence'] >= threshold]
            fire_cells_filtered.append(terrain_fire)
            
            # Filter no-fire cells (special handling for water cells)
            terrain_no_fire = no_fire_cells_df[no_fire_cells_df['terrain_type'] == terrain_type]
            if terrain_type == 'water':
                # Water cells don't need confidence filtering - they have no weather data
                pass  # Keep all water cells
            else:
                terrain_no_fire = terrain_no_fire[terrain_no_fire['avg_confidence'] >= threshold]
            no_fire_cells_filtered.append(terrain_no_fire)
        
        fire_df = pd.concat(fire_cells_filtered, ignore_index=True)
        no_fire_df = pd.concat(no_fire_cells_filtered, ignore_index=True)
        
        log_progress(f"   After filtering - Fire cells: {len(fire_df)}, No-fire cells: {len(no_fire_df)}")
        
        # Stratified sampling with balanced fire/no-fire
        target_cells = []
        for terrain_type, proportion in self.terrain_stratification.items():
            terrain_fire = fire_df[fire_df['terrain_type'] == terrain_type]
            terrain_no_fire = no_fire_df[no_fire_df['terrain_type'] == terrain_type]
            
            if len(terrain_fire) == 0 and len(terrain_no_fire) == 0:
                if terrain_type == 'water':
                    log_progress(f"   ℹ️ No water cells found - this is unexpected, water cells should be available")
                else:
                    log_progress(f"   ⚠️ No cells found for terrain type: {terrain_type}")
                continue
            
            # Calculate samples per terrain type
            n_samples = int(self.training_targets * proportion)
            
            # Ensure at least some fire samples if available
            n_fire = min(n_samples // 2, len(terrain_fire))
            n_no_fire = min(n_samples - n_fire, len(terrain_no_fire))
            
            # If we don't have enough fire samples, take more no-fire samples
            if n_fire < n_samples // 4:  # At least 25% fire samples
                n_fire = min(len(terrain_fire), n_samples // 4)
                n_no_fire = min(n_samples - n_fire, len(terrain_no_fire))
            
            if n_fire > 0:
                fire_sample = terrain_fire.sample(n=n_fire, random_state=42)
                target_cells.append(fire_sample)
            
            if n_no_fire > 0:
                no_fire_sample = terrain_no_fire.sample(n=n_no_fire, random_state=42)
                target_cells.append(no_fire_sample)
            
            log_progress(f"   {terrain_type}: {n_fire} fire + {n_no_fire} no-fire = {n_fire + n_no_fire} cells")
        
        if len(target_cells) == 0:
            raise ValueError("No target cells selected after filtering")
        
        # Combine and return
        result_df = pd.concat(target_cells, ignore_index=True)
        log_progress(f"   Total selected cells: {len(result_df)}")
        log_progress(f"   Fire cells: {len(result_df[result_df['fire_count'] > 0])}")
        log_progress(f"   No-fire cells: {len(result_df[result_df['fire_count'] == 0])}")
        
        return result_df.to_dict('records')
    
    def _generate_dataset(self, target_cells: List[Dict], dataset_type: str) -> List[Dict]:
        """Generate training or testing dataset from target cells"""
        conn = sqlite3.connect(self.db_path)
        
        dataset = []
        processed = 0
        
        for cell in target_cells:
            try:
                # Generate samples for this cell
                cell_samples = self._generate_cell_samples(cell, conn, dataset_type)
                dataset.extend(cell_samples)
                processed += 1
                
                if processed % 50 == 0:
                    log_progress(f"   Processed {processed}/{len(target_cells)} cells ({len(dataset)} samples)")
                    
            except Exception as e:
                log_progress(f"   ⚠️ Error processing cell {cell['cell_id']}: {e}")
                continue
        
        conn.close()
        return dataset
    
    def _generate_cell_samples(self, cell: Dict, conn: sqlite3.Connection, dataset_type: str) -> List[Dict]:
        """Generate samples for a single target cell"""
        cell_id = cell['cell_id']
        terrain_type = cell['terrain_type']
        
        # Special handling for water cells - they don't have weather data
        if terrain_type == 'water':
            # Generate samples for water cells using synthetic dates
            if dataset_type == "training":
                # Use 2022-2023 dates for training
                dates = pd.date_range('2022-06-01', '2023-08-31', freq='D')
            else:
                # Use 2024 dates for testing
                dates = pd.date_range('2024-06-01', '2024-08-31', freq='D')
            
            # Sample a few dates
            n_samples = min(10 if dataset_type == "training" else 20, len(dates))
            sampled_dates = dates.to_series().sample(n=n_samples, random_state=42)
            
            samples = []
            for date in sampled_dates:
                features = self._generate_features(cell_id, date.strftime('%Y-%m-%d'), conn)
                if features:
                    samples.append(features)
            
            return samples
        
        # Get available dates for this cell
        dates_df = pd.read_sql_query("""
            SELECT DISTINCT date FROM weather_data 
            WHERE cell_id = ? 
            ORDER BY date
        """, conn, params=(cell_id,))
        
        if len(dates_df) == 0:
            return []
        
        # For training: use 2022-2023 data
        # For testing: use 2024 data
        if dataset_type == "training":
            date_filter = "date >= '2022-01-01' AND date <= '2023-12-31'"
        else:
            date_filter = "date >= '2024-01-01' AND date <= '2024-12-31'"
        
        available_dates = dates_df[dates_df['date'].str.match(r'202[2-4]-\d{2}-\d{2}')]
        if len(available_dates) == 0:
            return []
        
        # Sample dates strategically to get fire samples
        if dataset_type == "training":
            n_samples = min(10, len(available_dates))  # More samples for training
        else:
            n_samples = min(20, len(available_dates))  # 20 samples per cell for testing
        
        # For fire cells, prioritize dates that might have fires
        if cell['fire_count'] > 0:
            # Get dates when this cell had fires
            fire_dates = pd.read_sql_query("""
                SELECT DISTINCT fire_start_date, fire_end_date
                FROM cell_fire_relationships 
                WHERE cell_id = ?
            """, conn, params=(cell_id,))
            
            if len(fire_dates) > 0:
                # Sample some fire dates and some random dates
                fire_sample_dates = []
                for _, fire_row in fire_dates.iterrows():
                    start_dt = pd.to_datetime(fire_row['fire_start_date'])
                    end_dt = pd.to_datetime(fire_row['fire_end_date'])
                    # Add a few dates from the fire period
                    fire_period_dates = pd.date_range(start_dt, end_dt, freq='D')
                    fire_sample_dates.extend(fire_period_dates.strftime('%Y-%m-%d'))
                
                # Filter to available dates
                fire_sample_dates = [d for d in fire_sample_dates if d in available_dates['date'].values]
                
                # Take up to half from fire dates, rest random
                n_fire_samples = min(len(fire_sample_dates), n_samples // 2)
                n_random_samples = n_samples - n_fire_samples
                
                if n_fire_samples > 0:
                    fire_dates_df = pd.DataFrame({'date': fire_sample_dates[:n_fire_samples]})
                else:
                    fire_dates_df = pd.DataFrame(columns=['date'])
                
                if n_random_samples > 0:
                    random_dates = available_dates.sample(n=n_random_samples, random_state=42)
                else:
                    random_dates = pd.DataFrame(columns=['date'])
                
                sampled_dates = pd.concat([fire_dates_df, random_dates], ignore_index=True)
            else:
                sampled_dates = available_dates.sample(n=n_samples, random_state=42)
        else:
            # For no-fire cells, just sample randomly
            sampled_dates = available_dates.sample(n=n_samples, random_state=42)
        
        samples = []
        for _, row in sampled_dates.iterrows():
            target_date = row['date']
            
            # Generate features for this target date
            features = self._generate_features(cell_id, target_date, conn)
            if features is None:
                continue
            
            # Get fire status for this cell-date combination
            fire_status = self._get_fire_status(cell_id, target_date, conn)
            
            sample = {
                'cell_id': cell_id,
                'target_date': target_date,
                'terrain_type': terrain_type,
                'fire_occurred': fire_status,
                **features
            }
            samples.append(sample)
        
        return samples
    
    def _generate_features(self, cell_id: int, target_date: str, conn: sqlite3.Connection) -> Optional[Dict]:
        """Generate features for a target cell-date combination"""
        try:
            target_dt = pd.to_datetime(target_date)
            
            # Check if this is a water cell - special handling
            cell_info = pd.read_sql_query("""
                SELECT terrain_type, is_water, urban_flag FROM grid_cells WHERE cell_id = ?
            """, conn, params=(cell_id,))
            
            if len(cell_info) == 0:
                return None
                
            cell_type = cell_info.iloc[0]['terrain_type']
            
            # Special handling for water cells - they have no weather data
            if cell_type == 'water':
                return {
                    'cell_id': cell_id,
                    'terrain_type': cell_type,
                    'is_water': 1,
                    'urban_flag': cell_info.iloc[0]['urban_flag'],
                    'target_date': target_date,
                    'year_1_avg_temp': 0.0,
                    'year_1_max_temp': 0.0,
                    'year_1_total_precip': 0.0,
                    'year_1_dry_days': 0.0,
                    'year_1_fire_occurred': 0.0,
                    'year_2_avg_temp': 0.0,
                    'year_2_max_temp': 0.0,
                    'year_2_total_precip': 0.0,
                    'year_2_dry_days': 0.0,
                    'year_2_fire_occurred': 0.0,
                    'year_3_avg_temp': 0.0,
                    'year_3_max_temp': 0.0,
                    'year_3_total_precip': 0.0,
                    'year_3_dry_days': 0.0,
                    'year_3_fire_occurred': 0.0,
                    'neighbor_avg_temp': 0.0,
                    'neighbor_max_temp': 0.0,
                    'neighbor_total_precip': 0.0,
                    'neighbor_fire_frequency': 0.0,
                    'historical_fire_frequency': 0.0,
                    'area_km2': 100.0,  # Standard cell area
                    'elevation_m': 0.0,  # Water level
                    'distance_to_urban_km': 50.0,  # Assume far from urban
                    'fire_occurred': 0.0  # Water cells never have fires
                }
            
            # Get target cell weather data
            target_weather = self._get_cell_weather(cell_id, target_date, conn)
            if target_weather is None:
                return None
            
            features = {}
            
            # 1. Same cell yearly patterns (15 features)
            yearly_features = self._generate_yearly_patterns(cell_id, target_dt, conn)
            features.update(yearly_features)
            
            # 2. Neighbor spatial patterns (6 features)
            spatial_features = self._generate_spatial_patterns(cell_id, target_dt, conn)
            features.update(spatial_features)
            
            # 3. Target cell features (4 features)
            cell_features = self._generate_cell_features(cell_id, conn)
            features.update(cell_features)
            
            return features
            
        except Exception as e:
            log_progress(f"   Error generating features for cell {cell_id}, date {target_date}: {e}")
            return None
    
    def _generate_yearly_patterns(self, cell_id: int, target_dt: pd.Timestamp, conn: sqlite3.Connection) -> Dict:
        """Generate yearly pattern features (15 features)"""
        features = {}
        
        # Get 3 years of historical data
        for year_offset in range(1, 4):  # 1, 2, 3 years ago
            historical_year = target_dt.year - year_offset
            historical_date = target_dt.replace(year=historical_year)
            
            # Get ±7 days window around historical date
            start_date = historical_date - timedelta(days=self.yearly_window_days)
            end_date = historical_date + timedelta(days=self.yearly_window_days)
            
            # Query weather data for this period
            weather_data = pd.read_sql_query("""
                SELECT wd.tmax, wd.tmin, wd.tavg, wd.prcp, wd.snwd,
                       CASE WHEN cfr.fire_id IS NOT NULL THEN 1 ELSE 0 END as fire_occurred
                FROM weather_data wd
                LEFT JOIN cell_fire_relationships cfr ON wd.cell_id = cfr.cell_id 
                    AND wd.date >= cfr.fire_start_date 
                    AND wd.date <= cfr.fire_end_date
                WHERE wd.cell_id = ? AND wd.date >= ? AND wd.date <= ?
            """, conn, params=(cell_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            
            if len(weather_data) > 0:
                # Aggregate weather features
                features[f'year_{year_offset}_avg_temp'] = weather_data['tavg'].mean()
                features[f'year_{year_offset}_max_temp'] = weather_data['tmax'].max()
                features[f'year_{year_offset}_total_precip'] = weather_data['prcp'].sum()
                features[f'year_{year_offset}_dry_days'] = (weather_data['prcp'] < 1.0).sum()
                features[f'year_{year_offset}_fire_occurred'] = weather_data['fire_occurred'].max()
            else:
                # Fill with defaults if no data
                features[f'year_{year_offset}_avg_temp'] = 0.0
                features[f'year_{year_offset}_max_temp'] = 0.0
                features[f'year_{year_offset}_total_precip'] = 0.0
                features[f'year_{year_offset}_dry_days'] = 0
                features[f'year_{year_offset}_fire_occurred'] = 0
        
        # Calculate aggregated trends
        temp_values = [features[f'year_{i}_avg_temp'] for i in range(1, 4)]
        fire_values = [features[f'year_{i}_fire_occurred'] for i in range(1, 4)]
        
        features['avg_temp_trend'] = np.polyfit(range(3), temp_values, 1)[0] if len(temp_values) == 3 else 0.0
        features['fire_frequency'] = sum(fire_values) / len(fire_values) if fire_values else 0.0
        features['avg_fire_size'] = 0.0  # Placeholder - would need fire size data
        
        return features
    
    def _generate_spatial_patterns(self, cell_id: int, target_dt: pd.Timestamp, conn: sqlite3.Connection) -> Dict:
        """Generate spatial pattern features (6 features)"""
        features = {}
        
        # Get neighbor cells (simplified - would need proper neighbor calculation)
        # For now, use cells within a small radius
        neighbor_cells = pd.read_sql_query("""
            SELECT cell_id FROM grid_cells 
            WHERE cell_id != ? 
            ORDER BY ABS(center_lat - (SELECT center_lat FROM grid_cells WHERE cell_id = ?)) + 
                     ABS(center_lon - (SELECT center_lon FROM grid_cells WHERE cell_id = ?))
            LIMIT 8
        """, conn, params=(cell_id, cell_id, cell_id))
        
        if len(neighbor_cells) > 0:
            neighbor_ids = neighbor_cells['cell_id'].tolist()
            placeholders = ','.join(['?'] * len(neighbor_ids))
            
            # Get neighbor weather data for target date
            neighbor_data = pd.read_sql_query(f"""
                SELECT wd.tmax, wd.tmin, wd.prcp,
                       CASE WHEN cfr.fire_id IS NOT NULL THEN 1 ELSE 0 END as fire_occurred
                FROM weather_data wd
                LEFT JOIN cell_fire_relationships cfr ON wd.cell_id = cfr.cell_id 
                    AND wd.date >= cfr.fire_start_date 
                    AND wd.date <= cfr.fire_end_date
                WHERE wd.cell_id IN ({placeholders}) AND wd.date = ?
            """, conn, params=neighbor_ids + [target_dt.strftime('%Y-%m-%d')])
            
            if len(neighbor_data) > 0:
                features['neighbor_avg_temp'] = neighbor_data['tmax'].mean()
                features['neighbor_max_temp'] = neighbor_data['tmax'].max()
                features['neighbor_total_precip'] = neighbor_data['prcp'].sum()
                features['neighbor_dry_days'] = (neighbor_data['prcp'] < 1.0).sum()
                features['neighbor_fire_frequency'] = neighbor_data['fire_occurred'].mean()
                features['neighbor_terrain_types'] = 1.0  # Placeholder
            else:
                # Fill with defaults
                features['neighbor_avg_temp'] = 0.0
                features['neighbor_max_temp'] = 0.0
                features['neighbor_total_precip'] = 0.0
                features['neighbor_dry_days'] = 0
                features['neighbor_fire_frequency'] = 0.0
                features['neighbor_terrain_types'] = 0.0
        else:
            # No neighbors found
            features['neighbor_avg_temp'] = 0.0
            features['neighbor_max_temp'] = 0.0
            features['neighbor_total_precip'] = 0.0
            features['neighbor_dry_days'] = 0
            features['neighbor_fire_frequency'] = 0.0
            features['neighbor_terrain_types'] = 0.0
        
        return features
    
    def _generate_cell_features(self, cell_id: int, conn: sqlite3.Connection) -> Dict:
        """Generate target cell features (4 features)"""
        # Get cell characteristics
        cell_data = pd.read_sql_query("""
            SELECT terrain_type, center_lat, center_lon, is_water, urban_flag
            FROM grid_cells WHERE cell_id = ?
        """, conn, params=(cell_id,))
        
        if len(cell_data) == 0:
            return {
                'terrain_type_encoded': 0,
                'area_km2': 0.0,
                'historical_fire_frequency': 0.0,
                'elevation': 0.0
            }
        
        cell = cell_data.iloc[0]
        
        # Encode terrain type
        terrain_encoding = {'forest': 1, 'land': 2, 'urban': 3, 'water': 4}.get(cell['terrain_type'], 0)
        
        # Calculate area (simplified - 10km x 10km grid)
        area_km2 = 100.0  # 10km x 10km = 100 km²
        
        # Get historical fire frequency
        fire_data = pd.read_sql_query("""
            SELECT COUNT(*) as fire_count
            FROM cell_fire_relationships 
            WHERE cell_id = ?
        """, conn, params=(cell_id,))
        
        fire_count = fire_data['fire_count'].iloc[0] if len(fire_data) > 0 else 0
        historical_fire_frequency = fire_count / 3.0  # 3 years of data
        
        # Elevation (placeholder - would need elevation data)
        elevation = 0.0
        
        return {
            'terrain_type_encoded': terrain_encoding,
            'area_km2': area_km2,
            'historical_fire_frequency': historical_fire_frequency,
            'elevation': elevation
        }
    
    def _get_cell_weather(self, cell_id: int, date: str, conn: sqlite3.Connection) -> Optional[Dict]:
        """Get weather data for a specific cell-date"""
        weather_data = pd.read_sql_query("""
            SELECT tmax, tmin, tavg, prcp, snwd, confidence_score
            FROM weather_data 
            WHERE cell_id = ? AND date = ?
        """, conn, params=(cell_id, date))
        
        if len(weather_data) == 0:
            return None
        
        return weather_data.iloc[0].to_dict()
    
    def _get_fire_status(self, cell_id: int, date: str, conn: sqlite3.Connection) -> int:
        """Get fire status for a specific cell-date combination"""
        fire_data = pd.read_sql_query("""
            SELECT COUNT(*) as fire_count
            FROM cell_fire_relationships 
            WHERE cell_id = ? AND ? >= fire_start_date AND ? <= fire_end_date
        """, conn, params=(cell_id, date, date))
        
        return 1 if fire_data['fire_count'].iloc[0] > 0 else 0
    
    def _save_datasets(self, training_data: List[Dict], test_pool: List[Dict]):
        """Save training and testing datasets"""
        # Save training data
        training_df = pd.DataFrame(training_data)
        training_path = self.output_dir / "training_dataset.csv"
        training_df.to_csv(training_path, index=False)
        log_progress(f"   Saved training dataset: {training_path} ({len(training_df)} samples)")
        
        # Save test pool
        test_df = pd.DataFrame(test_pool)
        test_path = self.output_dir / "test_pool.csv"
        test_df.to_csv(test_path, index=False)
        log_progress(f"   Saved test pool: {test_path} ({len(test_df)} samples)")
        
        # Save metadata
        metadata = {
            'generation_date': datetime.now().isoformat(),
            'training_samples': len(training_data),
            'test_samples': len(test_pool),
            'features': list(training_df.columns) if len(training_data) > 0 else [],
            'terrain_distribution': training_df['terrain_type'].value_counts().to_dict() if len(training_data) > 0 else {},
            'fire_distribution': training_df['fire_occurred'].value_counts().to_dict() if len(training_data) > 0 else {}
        }
        
        metadata_path = self.output_dir / "dataset_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        log_progress(f"   Saved metadata: {metadata_path}")
    
    def _generate_summary_stats(self, training_data: List[Dict], test_pool: List[Dict]):
        """Generate summary statistics"""
        if len(training_data) == 0:
            log_progress("   ⚠️ No training data to analyze")
            return
        
        training_df = pd.DataFrame(training_data)
        
        log_progress("   📊 Training Dataset Summary:")
        log_progress(f"      Total samples: {len(training_df)}")
        log_progress(f"      Fire samples: {training_df['fire_occurred'].sum()}")
        log_progress(f"      No-fire samples: {len(training_df) - training_df['fire_occurred'].sum()}")
        log_progress(f"      Fire rate: {training_df['fire_occurred'].mean():.1%}")
        
        # Data quality validation
        fire_rate = training_df['fire_occurred'].mean()
        if fire_rate < 0.05:
            log_progress("      ⚠️ WARNING: Very low fire rate - may need more fire samples")
        elif fire_rate > 0.5:
            log_progress("      ⚠️ WARNING: Very high fire rate - may need more no-fire samples")
        else:
            log_progress("      ✅ Fire rate looks balanced")
        
        log_progress("   📊 Terrain Distribution:")
        terrain_counts = training_df['terrain_type'].value_counts()
        for terrain, count in terrain_counts.items():
            log_progress(f"      {terrain}: {count} ({count/len(training_df):.1%})")
        
        log_progress("   📊 Feature Quality Check:")
        numeric_features = training_df.select_dtypes(include=[np.number]).columns
        
        # Check for constant features
        constant_features = []
        for feature in numeric_features:
            if training_df[feature].nunique() <= 1:
                constant_features.append(feature)
        
        if constant_features:
            log_progress(f"      ⚠️ Constant features: {len(constant_features)}")
        else:
            log_progress("      ✅ No constant features")
        
        # Check for missing values
        missing_data = training_df.isnull().sum()
        missing_cols = missing_data[missing_data > 0]
        if len(missing_cols) > 0:
            log_progress(f"      ⚠️ Missing values in {len(missing_cols)} features")
        else:
            log_progress("      ✅ No missing values")
        
        log_progress("   📊 Feature Statistics (first 10 features):")
        for feature in numeric_features[:10]:
            mean_val = training_df[feature].mean()
            std_val = training_df[feature].std()
            log_progress(f"      {feature}: {mean_val:.3f} ± {std_val:.3f}")

def main():
    parser = argparse.ArgumentParser(description='Generate AI training datasets')
    parser.add_argument('--db-path', default='../../databases/interpolated_grid_db.db',
                       help='Path to interpolated grid database')
    parser.add_argument('--output-dir', default='../../ai/training',
                       help='Output directory for training data')
    parser.add_argument('--test', action='store_true', help='Run in test mode with smaller datasets')
    parser.add_argument('--test-pool-size', type=int, default=200, help='Size of test pool (default: 200)')
    
    args = parser.parse_args()
    
    # Adjust parameters for test mode
    if args.test:
        log_progress("🧪 Running in test mode")
    
    # Create generator
    generator = TrainingDataGenerator(args.db_path, args.output_dir)
    
    if args.test:
        generator.training_targets = 50
        generator.test_pool_size = 200
        generator.test_per_generation = 20
    
    # Override test pool size if specified
    generator.test_pool_size = args.test_pool_size
    
    # Generate training data
    success = generator.generate_training_data()
    
    if success:
        log_progress("✅ Training data generation completed successfully!")
        return 0
    else:
        log_progress("❌ Training data generation failed!")
        return 1

if __name__ == "__main__":
    exit(main())
