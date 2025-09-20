#!/usr/bin/env python3
"""
Run AI Evolution - Production Script
===================================
Production script for running AI evolution with configurable parameters.
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from evolution_framework import EvolutionFramework
from ai_config import EvolutionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evolution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function for running AI evolution"""
    parser = argparse.ArgumentParser(description='Run AI Evolution for Wildfire Prediction')
    
    # Evolution parameters
    parser.add_argument('--population-size', type=int, default=50,
                       help='Population size (default: 50)')
    parser.add_argument('--max-generations', type=int, default=10,
                       help='Maximum generations (default: 10)')
    parser.add_argument('--test-samples', type=int, default=200,
                       help='Test samples per generation (default: 200)')
    parser.add_argument('--elite-count', type=int, default=5,
                       help='Number of elite AIs to keep (default: 5)')
    parser.add_argument('--mutation-rate', type=float, default=0.1,
                       help='Mutation rate (default: 0.1)')
    parser.add_argument('--crossover-rate', type=float, default=0.8,
                       help='Crossover rate (default: 0.8)')
    
    # Data paths
    parser.add_argument('--training-data', type=str, default='training/training_dataset.csv',
                       help='Path to training data (default: training/training_dataset.csv)')
    parser.add_argument('--test-pool', type=str, default='training/test_pool.csv',
                       help='Path to test pool (default: training/test_pool.csv)')
    
    # Output
    parser.add_argument('--output-dir', type=str, default='.',
                       help='Output directory for results (default: current directory)')
    parser.add_argument('--save-best', type=str, default='best_ai.pkl',
                       help='Filename for best AI (default: best_ai.pkl)')
    
    # Test mode
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (small population, few generations)')
    
    args = parser.parse_args()
    
    # Override for test mode
    if args.test:
        logger.info("🧪 Running in TEST MODE")
        args.population_size = 10
        args.max_generations = 3
        args.test_samples = 50
        args.elite_count = 3
        args.mutation_rate = 0.2
    
    # Create evolution config
    config = EvolutionConfig(
        population_size=args.population_size,
        max_generations=args.max_generations,
        test_samples_per_generation=args.test_samples,
        elite_count=args.elite_count,
        mutation_rate=args.mutation_rate,
        crossover_rate=args.crossover_rate,
        training_data_path=args.training_data,
        test_pool_path=args.test_pool
    )
    
    # Log configuration
    logger.info("🚀 Starting AI Evolution")
    logger.info("=" * 60)
    logger.info(f"Population size: {config.population_size}")
    logger.info(f"Max generations: {config.max_generations}")
    logger.info(f"Test samples per generation: {config.test_samples_per_generation}")
    logger.info(f"Elite count: {config.elite_count}")
    logger.info(f"Mutation rate: {config.mutation_rate}")
    logger.info(f"Crossover rate: {config.crossover_rate}")
    logger.info(f"Training data: {config.training_data_path}")
    logger.info(f"Test pool: {config.test_pool_path}")
    logger.info("")
    
    # Check if training data exists
    if not Path(config.training_data_path).exists():
        logger.error(f"Training data not found: {config.training_data_path}")
        return 1
    
    if not Path(config.test_pool_path).exists():
        logger.error(f"Test pool not found: {config.test_pool_path}")
        return 1
    
    # Create evolution framework
    try:
        evolution = EvolutionFramework(
            evolution_config=config,
            training_data_path=config.training_data_path
        )
    except Exception as e:
        logger.error(f"Failed to create evolution framework: {e}")
        return 1
    
    # Run evolution
    try:
        start_time = datetime.now()
        success = evolution.run_evolution()
        end_time = datetime.now()
        
        if not success:
            logger.error("Evolution failed")
            return 1
        
        # Log final results
        duration = end_time - start_time
        logger.info(f"\n🏆 Evolution completed successfully in {duration}")
        logger.info(f"Best fitness: {evolution.best_fitness:.4f}")
        logger.info(f"Best AI: {evolution.best_ai.model_id if evolution.best_ai else 'None'}")
        
        # Save best AI
        if evolution.best_ai:
            output_path = Path(args.output_dir) / args.save_best
            if evolution.save_best_ai(str(output_path)):
                logger.info(f"Best AI saved to: {output_path}")
            else:
                logger.error("Failed to save best AI")
                return 1
        
        # Save evolution summary
        summary = evolution.get_evolution_summary()
        summary_path = Path(args.output_dir) / f"evolution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Evolution summary saved to: {summary_path}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Evolution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Evolution failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

