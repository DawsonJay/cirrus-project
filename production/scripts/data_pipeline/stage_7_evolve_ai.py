#!/usr/bin/env python3
"""
Stage 7: Evolve AI
=================
Evolve AIs through competitive evolution to find optimal configurations.
This is Stage 7 of the Cirrus data pipeline.

Usage:
    python3 stage_7_evolve_ai.py [--generations 10] [--population 50] [--samples 200]
"""

import argparse
import logging
import time
import sys
from pathlib import Path

# Add ai folder to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'ai'))
from evolution_framework import EvolutionFramework
from ai_config import EvolutionConfig
from seed_ai import SeedAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run AI evolution"""
    parser = argparse.ArgumentParser(description='Stage 7: Evolve AI through competition')
    parser.add_argument('--generations', type=int, default=10,
                       help='Number of generations to evolve (default: 10)')
    parser.add_argument('--population', type=int, default=50,
                       help='Population size (default: 50)')
    parser.add_argument('--samples', type=int, default=200,
                       help='Test samples per generation (default: 200)')
    parser.add_argument('--training-data', type=str, default='../../ai/training/training_dataset.csv',
                       help='Path to training data')
    parser.add_argument('--test-pool', type=str, default='../../ai/training/test_pool.csv',
                       help='Path to test pool')
    parser.add_argument('--output', type=str, default='../../ai/evolved_ai.pkl',
                       help='Output file for best evolved AI')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (small population, few generations)')
    
    args = parser.parse_args()
    
    # Override for test mode
    if args.test:
        logger.info("🧪 Running in TEST MODE")
        args.population = 10
        args.generations = 3
        args.samples = 50
    
    logger.info("🧬 Stage 7: AI Evolution - Competitive Evolution")
    logger.info("=" * 60)
    logger.info(f"📊 Generations: {args.generations}")
    logger.info(f"📊 Population: {args.population}")
    logger.info(f"📊 Test samples: {args.samples}")
    logger.info(f"📊 Training data: {args.training_data}")
    logger.info(f"📊 Test pool: {args.test_pool}")
    logger.info(f"📊 Output: {args.output}")
    logger.info("")
    
    # Check if training data exists
    if not Path(args.training_data).exists():
        logger.error(f"❌ Training data not found: {args.training_data}")
        logger.error("   Run Stage 6 (generate training data) first")
        return False
    
    if not Path(args.test_pool).exists():
        logger.error(f"❌ Test pool not found: {args.test_pool}")
        logger.error("   Run Stage 6 (generate training data) first")
        return False
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure evolution
    evolution_config = EvolutionConfig(
        population_size=args.population,
        test_samples_per_generation=args.samples,
        max_generations=args.generations,
        training_data_path=args.training_data,
        test_pool_path=args.test_pool
    )
    
    # Create evolution framework
    logger.info("🧬 Initializing evolution framework...")
    evolution = EvolutionFramework(
        evolution_config=evolution_config,
        training_data_path=args.training_data
    )
    
    # Run evolution
    logger.info("🚀 Starting evolution process...")
    start_time = time.time()
    
    success = evolution.run_evolution()
    
    total_time = time.time() - start_time
    
    if not success:
        logger.error("❌ Evolution failed")
        return False
    
    # Save best AI
    logger.info("💾 Saving best evolved AI...")
    if not evolution.save_best_ai(args.output):
        logger.error("❌ Failed to save best AI")
        return False
    
    # Print results
    summary = evolution.get_evolution_summary()
    logger.info("")
    logger.info("📊 STAGE 7 COMPLETE!")
    logger.info("=" * 40)
    logger.info(f"🧬 Generations: {summary['generations']}")
    logger.info(f"🏆 Best fitness: {summary['best_fitness']:.4f}")
    logger.info(f"⏱️ Total training time: {summary['total_training_time']:.2f}s")
    logger.info(f"⏱️ Total evaluation time: {summary['total_evaluation_time']:.2f}s")
    logger.info(f"👥 Population: {summary['population_size']}")
    logger.info(f"📊 Test samples: {summary['test_samples']}")
    logger.info(f"💾 Best AI saved: {args.output}")
    
    # Test the evolved AI
    logger.info("")
    logger.info("🔮 Testing evolved AI...")
    if evolution.best_ai:
        test_prediction = evolution.best_ai.predict("12345", "2024-06-15")
        if test_prediction:
            logger.info("✅ Evolved AI test successful!")
            logger.info(f"   Fire probability: {test_prediction['fire_probability']:.3f}")
            logger.info(f"   Prediction time: {test_prediction['prediction_time']:.3f}s")
            logger.info(f"   Model ID: {test_prediction['model_id']}")
        else:
            logger.warning("⚠️ Evolved AI test failed")
    
    logger.info("")
    logger.info("🎉 Stage 7 complete!")
    logger.info("   Evolved AI ready for production use.")
    logger.info("   Next: Deploy evolved AI or run additional evolution cycles.")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)

