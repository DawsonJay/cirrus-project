#!/usr/bin/env python3
"""
Generate Comprehensive Test Pool
================================
Creates a large, diverse test pool to thoroughly validate AI performance.
This generates many more test samples across different scenarios.

Usage:
    python3 generate_comprehensive_test_pool.py [--samples 5000] [--output ../../ai/training/comprehensive_test_pool.csv]
"""

import argparse
import logging
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestPoolGenerator:
    """Generates a comprehensive test pool for AI validation."""
    
    def __init__(self, 
                 database_path: str = '../../databases/interpolated_grid_db.db',
                 output_path: str = '../../ai/training/comprehensive_test_pool.csv',
                 target_samples: int = 5000,
                 fire_ratio: float = 0.05,  # 5% fire samples
                 terrain_distribution: dict = None):
        
        self.database_path = database_path
        self.output_path = output_path
        self.target_samples = target_samples
        self.fire_ratio = fire_ratio
        self.terrain_distribution = terrain_distribution or {
            'forest': 0.40,
            'tundra': 0.25, 
            'urban': 0.15,
            'water': 0.20
        }
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🎯 Comprehensive Test Pool Generator")
        logger.info(f"Target samples: {target_samples}")
        logger.info(f"Fire ratio: {fire_ratio:.1%}")
        logger.info(f"Terrain distribution: {self.terrain_distribution}")
    
    def _get_database_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.database_path)
    
    def _select_diverse_cells(self) -> pd.DataFrame:
        """Select a diverse set of cells for testing."""
        with self._get_database_connection() as conn:
            query = """
            SELECT DISTINCT 
                gc.cell_id,
                gc.center_lat as latitude,
                gc.center_lon as longitude,
                gc.terrain_type,
                COUNT(wd.date) as data_days,
                AVG(wd.confidence_score) as avg_confidence
            FROM grid_cells gc
            LEFT JOIN weather_data wd ON gc.cell_id = wd.cell_id
            GROUP BY gc.cell_id, gc.center_lat, gc.center_lon, gc.terrain_type
            HAVING data_days >= 50  -- Lower threshold for more diversity
            ORDER BY RANDOM()
            """
            
            cells_df = pd.read_sql_query(query, conn)
            logger.info(f"Found {len(cells_df)} cells with sufficient data")
            
            # Ensure terrain diversity
            selected_cells = []
            for terrain, ratio in self.terrain_distribution.items():
                terrain_cells = cells_df[cells_df['terrain_type'] == terrain]
                needed = int(self.target_samples * ratio)
                if len(terrain_cells) >= needed:
                    selected = terrain_cells.sample(n=needed, random_state=42)
                else:
                    selected = terrain_cells
                    logger.warning(f"Only found {len(terrain_cells)} {terrain} cells, using all")
                selected_cells.append(selected)
            
            result = pd.concat(selected_cells, ignore_index=True)
            logger.info(f"Selected {len(result)} diverse cells")
            return result
    
    def _get_fire_cells(self) -> set:
        """Get cells that have had fires."""
        with self._get_database_connection() as conn:
            query = """
            SELECT DISTINCT cfr.cell_id
            FROM cell_fire_relationships cfr
            JOIN fire_events fe ON cfr.fire_id = fe.fire_id
            """
            fire_cells_df = pd.read_sql_query(query, conn)
            return set(fire_cells_df['cell_id'].tolist())
    
    def _generate_test_samples(self, cells_df: pd.DataFrame) -> pd.DataFrame:
        """Generate test samples from selected cells."""
        fire_cells = self._get_fire_cells()
        logger.info(f"Found {len(fire_cells)} cells with fire history")
        
        samples = []
        fire_samples_needed = int(self.target_samples * self.fire_ratio)
        no_fire_samples_needed = self.target_samples - fire_samples_needed
        
        logger.info(f"Target: {fire_samples_needed} fire samples, {no_fire_samples_needed} no-fire samples")
        
        # Generate fire samples
        fire_cells_available = cells_df[cells_df['cell_id'].isin(fire_cells)]
        if len(fire_cells_available) > 0:
            fire_samples = self._generate_cell_samples(
                fire_cells_available, 
                fire_samples_needed, 
                fire_required=True
            )
            samples.extend(fire_samples)
            logger.info(f"Generated {len(fire_samples)} fire samples")
        
        # Generate no-fire samples (mix of cells with and without fire history)
        no_fire_samples = self._generate_cell_samples(
            cells_df, 
            no_fire_samples_needed, 
            fire_required=False
        )
        samples.extend(no_fire_samples)
        logger.info(f"Generated {len(no_fire_samples)} no-fire samples")
        
        # Shuffle and limit to target
        random.shuffle(samples)
        samples = samples[:self.target_samples]
        
        logger.info(f"Final test pool: {len(samples)} samples")
        return pd.DataFrame(samples)
    
    def _generate_cell_samples(self, cells_df: pd.DataFrame, num_samples: int, fire_required: bool) -> list:
        """Generate samples for a set of cells."""
        samples = []
        
        for _, cell in cells_df.iterrows():
            if len(samples) >= num_samples:
                break
                
            # Generate multiple samples per cell for diversity
            samples_per_cell = min(3, num_samples - len(samples))
            
            for _ in range(samples_per_cell):
                sample = self._generate_single_sample(cell, fire_required)
                if sample:
                    samples.append(sample)
        
        return samples
    
    def _generate_single_sample(self, cell: pd.Series, fire_required: bool) -> dict:
        """Generate a single test sample."""
        try:
            # Generate a random date in 2024 for testing
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 12, 31)
            random_days = random.randint(0, (end_date - start_date).days)
            target_date = start_date + timedelta(days=random_days)
            
            # Generate features (simplified for test pool)
            features = self._generate_simple_features(cell, target_date)
            
            # Determine if this should be a fire sample
            if fire_required:
                fire_occurred = 1.0
            else:
                fire_occurred = 0.0
            
            sample = {
                'cell_id': cell['cell_id'],
                'target_date': target_date.strftime('%Y-%m-%d'),
                'fire_occurred': fire_occurred,
                'terrain_type': cell['terrain_type'],
                **features
            }
            
            return sample
            
        except Exception as e:
            logger.warning(f"Failed to generate sample for cell {cell['cell_id']}: {e}")
            return None
    
    def _generate_simple_features(self, cell: pd.Series, target_date: datetime) -> dict:
        """Generate simplified features for testing."""
        # For water cells, return simplified features
        if cell['terrain_type'] == 'water':
            return {
                'temp_avg': 0.0,
                'temp_min': 0.0,
                'temp_max': 0.0,
                'humidity_avg': 0.0,
                'wind_speed_avg': 0.0,
                'precipitation': 0.0,
                'pressure_avg': 0.0,
                'visibility_avg': 0.0,
                'cloud_cover_avg': 0.0,
                'uv_index_avg': 0.0,
                'dew_point_avg': 0.0,
                'heat_index_avg': 0.0,
                'wind_chill_avg': 0.0,
                'fire_weather_index': 0.0,
                'drought_index': 0.0,
                'vegetation_index': 0.0,
                'elevation': 0.0,
                'slope': 0.0,
                'aspect': 0.0,
                'distance_to_water': 0.0,
                'distance_to_road': 0.0,
                'distance_to_urban': 0.0,
                'population_density': 0.0,
                'land_use_diversity': 0.0,
                'fire_history_density': 0.0,
                'fire_frequency': 0.0,
                'last_fire_days': 9999,
                'seasonal_fire_risk': 0.0,
                'monthly_fire_risk': 0.0,
                'yearly_fire_risk': 0.0,
                'confidence_score': 0.1
            }
        
        # For land cells, generate realistic features
        features = {}
        
        # Weather features (realistic ranges)
        features['temp_avg'] = random.uniform(-20, 35)
        features['temp_min'] = features['temp_avg'] - random.uniform(5, 15)
        features['temp_max'] = features['temp_avg'] + random.uniform(5, 15)
        features['humidity_avg'] = random.uniform(20, 90)
        features['wind_speed_avg'] = random.uniform(0, 30)
        features['precipitation'] = random.uniform(0, 50)
        features['pressure_avg'] = random.uniform(950, 1050)
        features['visibility_avg'] = random.uniform(1, 50)
        features['cloud_cover_avg'] = random.uniform(0, 100)
        features['uv_index_avg'] = random.uniform(0, 12)
        features['dew_point_avg'] = features['temp_avg'] - random.uniform(0, 10)
        features['heat_index_avg'] = features['temp_avg'] + random.uniform(0, 5)
        features['wind_chill_avg'] = features['temp_avg'] - random.uniform(0, 10)
        
        # Fire-related features
        features['fire_weather_index'] = random.uniform(0, 100)
        features['drought_index'] = random.uniform(0, 100)
        features['vegetation_index'] = random.uniform(0, 1)
        
        # Geographic features
        features['elevation'] = random.uniform(0, 3000)
        features['slope'] = random.uniform(0, 45)
        features['aspect'] = random.uniform(0, 360)
        features['distance_to_water'] = random.uniform(0, 10000)
        features['distance_to_road'] = random.uniform(0, 5000)
        features['distance_to_urban'] = random.uniform(0, 20000)
        features['population_density'] = random.uniform(0, 1000)
        features['land_use_diversity'] = random.uniform(0, 1)
        
        # Fire history features
        features['fire_history_density'] = random.uniform(0, 10)
        features['fire_frequency'] = random.uniform(0, 1)
        features['last_fire_days'] = random.randint(0, 3650)
        features['seasonal_fire_risk'] = random.uniform(0, 1)
        features['monthly_fire_risk'] = random.uniform(0, 1)
        features['yearly_fire_risk'] = random.uniform(0, 1)
        
        # Confidence score
        features['confidence_score'] = random.uniform(0.1, 1.0)
        
        return features
    
    def generate_test_pool(self) -> bool:
        """Generate the comprehensive test pool."""
        try:
            logger.info("🚀 Starting comprehensive test pool generation...")
            
            # Select diverse cells
            cells_df = self._select_diverse_cells()
            if len(cells_df) == 0:
                logger.error("No cells found for test pool generation")
                return False
            
            # Generate test samples
            test_pool_df = self._generate_test_samples(cells_df)
            if len(test_pool_df) == 0:
                logger.error("No test samples generated")
                return False
            
            # Save test pool
            test_pool_df.to_csv(self.output_path, index=False)
            logger.info(f"✅ Comprehensive test pool saved: {self.output_path}")
            
            # Generate summary statistics
            self._generate_summary_stats(test_pool_df)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test pool generation failed: {e}")
            return False
    
    def _generate_summary_stats(self, test_pool_df: pd.DataFrame):
        """Generate summary statistics for the test pool."""
        logger.info("📊 Test Pool Summary:")
        logger.info(f"  Total samples: {len(test_pool_df)}")
        logger.info(f"  Fire samples: {test_pool_df['fire_occurred'].sum()}")
        logger.info(f"  No-fire samples: {len(test_pool_df) - test_pool_df['fire_occurred'].sum()}")
        logger.info(f"  Fire rate: {test_pool_df['fire_occurred'].mean():.1%}")
        
        # Terrain distribution
        terrain_counts = test_pool_df['terrain_type'].value_counts()
        logger.info("  Terrain distribution:")
        for terrain, count in terrain_counts.items():
            logger.info(f"    {terrain}: {count} ({count/len(test_pool_df):.1%})")
        
        # Feature statistics
        numeric_cols = test_pool_df.select_dtypes(include=[np.number]).columns
        logger.info(f"  Features: {len(numeric_cols)}")
        logger.info(f"  Date range: {test_pool_df['target_date'].min()} to {test_pool_df['target_date'].max()}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate Comprehensive Test Pool')
    parser.add_argument('--samples', type=int, default=5000,
                        help='Number of test samples to generate (default: 5000)')
    parser.add_argument('--output', type=str, default='../../ai/training/comprehensive_test_pool.csv',
                        help='Output file path (default: ../../ai/training/comprehensive_test_pool.csv)')
    parser.add_argument('--fire-ratio', type=float, default=0.05,
                        help='Ratio of fire samples (default: 0.05)')
    parser.add_argument('--database', type=str, default='../../databases/interpolated_grid_db.db',
                        help='Path to interpolated grid database')
    
    args = parser.parse_args()
    
    logger.info("🎯 Comprehensive Test Pool Generator")
    logger.info("=" * 50)
    logger.info(f"Target samples: {args.samples}")
    logger.info(f"Fire ratio: {args.fire_ratio:.1%}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Database: {args.database}")
    logger.info("")
    
    # Create generator
    generator = ComprehensiveTestPoolGenerator(
        database_path=args.database,
        output_path=args.output,
        target_samples=args.samples,
        fire_ratio=args.fire_ratio
    )
    
    # Generate test pool
    success = generator.generate_test_pool()
    
    if success:
        logger.info("")
        logger.info("🎉 Comprehensive test pool generation complete!")
        logger.info("   Ready for thorough AI validation testing.")
    else:
        logger.error("❌ Test pool generation failed")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
