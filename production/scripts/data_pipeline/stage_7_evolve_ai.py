#!/usr/bin/env python3
"""
Stage 7: Evolve AI
=================
Evolve AIs through competitive evolution to find optimal configurations.
This is Stage 7 of the Cirrus data pipeline.

Usage:
    python3 stage_7_evolve_ai.py [--generations 10] [--population 20] [--samples 50]
"""

import argparse
import logging
import time
import sys
from pathlib import Path

# Add ai folder to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'ai'))
from evolution_framework import EvolutionFramework, EvolutionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../production/logs/stage_7_evolve_ai.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run AI evolution"""
    parser = argparse.ArgumentParser(description='Stage 7: Evolve AI through competition')
    parser.add_argument('--generations', type=int, default=10,
                       help='Number of generations to evolve (default: 10)')
    parser.add_argument('--population', type=int, default=20,
                       help='Population size (default: 20)')
    parser.add_argument('--samples', type=int, default=50,
                       help='Test samples per generation (default: 50)')
    parser.add_argument('--db', type=str, default='../../databases/interpolated_grid_db.db',
                       help='Path to interpolated grid database')
    parser.add_argument('--seed', type=str, default='../../ai/seed_ai.pkl',
                       help='Path to seed AI model')
    parser.add_argument('--output', type=str, default='../../ai/evolved_ai.pkl',
                       help='Output file for best evolved AI')
    
    args = parser.parse_args()
    
    logger.info("🧬 Stage 7: AI Evolution - Competitive Evolution")
    logger.info("=" * 60)
    logger.info(f"📊 Generations: {args.generations}")
    logger.info(f"📊 Population: {args.population}")
    logger.info(f"📊 Test samples: {args.samples}")
    logger.info(f"📊 Database: {args.db}")
    logger.info(f"📊 Seed AI: {args.seed}")
    logger.info(f"📊 Output: {args.output}")
    logger.info("")
    
    # Check if database exists
    if not Path(args.db).exists():
        logger.error(f"❌ Database not found: {args.db}")
        logger.error("   Run Stage 5 (interpolation) first")
        return False
    
    # Check if seed AI exists
    if not Path(args.seed).exists():
        logger.error(f"❌ Seed AI not found: {args.seed}")
        logger.error("   Run Stage 6 (train seed AI) first")
        return False
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure evolution
    evolution_config = EvolutionConfig(
        population_size=args.population,
        test_samples_per_generation=args.samples,
        max_generations=args.generations
    )
    
    # Create evolution framework
    logger.info("🧬 Initializing evolution framework...")
    evolution = EvolutionFramework(
        db_path=args.db,
        evolution_config=evolution_config,
        seed_ai_path=args.seed
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
    logger.info(f"⏱️ Total time: {summary['total_time']:.2f}s ({summary['total_time']/60:.1f} min)")
    logger.info(f"👥 Population: {summary['population_size']}")
    logger.info(f"📊 Test samples: {summary['test_samples']}")
    logger.info(f"💾 Best AI saved: {args.output}")
    
    # Test the evolved AI
    logger.info("")
    logger.info("🔮 Testing evolved AI...")
    if evolution.best_ai:
        test_prediction = evolution.best_ai.predict("1", "2024-06-15")
        if test_prediction:
            logger.info("✅ Evolved AI test successful!")
            logger.info(f"   Weather: Tmax={test_prediction['weather']['tmax']:.1f}°C, "
                       f"Tmin={test_prediction['weather']['tmin']:.1f}°C")
            logger.info(f"   Wildfire: {test_prediction['wildfire']['fire_probability']:.3f} probability")
            logger.info(f"   Time: {test_prediction['prediction_time']:.3f}s")
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

