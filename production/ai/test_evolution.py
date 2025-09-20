#!/usr/bin/env python3
"""
Test Evolution Framework
=======================
Test the EvolutionFramework class with a small population.
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from evolution_framework import EvolutionFramework
from ai_config import EvolutionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_evolution_framework():
    """Test the EvolutionFramework class"""
    logger.info("🧬 Testing EvolutionFramework class")
    
    # Test 1: Create evolution config
    logger.info("Test 1: Creating evolution config")
    config = EvolutionConfig(
        population_size=10,  # Small population for testing
        max_generations=3,   # Few generations for testing
        test_samples_per_generation=50,  # Small test set
        elite_count=3,
        mutation_rate=0.2,
        crossover_rate=0.8
    )
    
    logger.info(f"Config: {config.population_size} AIs, {config.max_generations} generations")
    
    # Test 2: Create evolution framework
    logger.info("\nTest 2: Creating evolution framework")
    evolution = EvolutionFramework(
        evolution_config=config,
        training_data_path="training/training_dataset.csv"
    )
    
    logger.info("Evolution framework created successfully")
    
    # Test 3: Load test pool
    logger.info("\nTest 3: Loading test pool")
    if not evolution.load_test_pool():
        logger.error("Failed to load test pool")
        return False
    
    logger.info(f"Test pool loaded: {len(evolution.test_pool)} samples")
    
    # Test 4: Create initial population
    logger.info("\nTest 4: Creating initial population")
    population = evolution.create_initial_population()
    logger.info(f"Created {len(population)} AIs")
    
    # Test 5: Train population
    logger.info("\nTest 5: Training population")
    trained_population = evolution.train_population(population)
    successful_count = sum(1 for ai in trained_population if ai.is_trained)
    logger.info(f"Training complete: {successful_count}/{len(trained_population)} successful")
    
    # Test 6: Select test samples
    logger.info("\nTest 6: Selecting test samples")
    test_samples = evolution.select_test_samples()
    logger.info(f"Selected {len(test_samples)} test samples")
    
    # Test 7: Evaluate population
    logger.info("\nTest 7: Evaluating population")
    results = evolution.evaluate_population(trained_population)
    
    logger.info("Evaluation results:")
    for i, (ai, fitness) in enumerate(results[:5]):  # Show top 5
        logger.info(f"  {i+1}. {ai.model_id}: {fitness:.4f}")
    
    # Test 8: Select elite
    logger.info("\nTest 8: Selecting elite")
    elite = evolution.select_elite(results)
    logger.info(f"Selected {len(elite)} elite AIs")
    
    # Test 9: Create offspring
    logger.info("\nTest 9: Creating offspring")
    offspring = evolution.create_offspring(elite)
    logger.info(f"Created {len(offspring)} offspring")
    
    # Test 10: Run one generation
    logger.info("\nTest 10: Running one generation")
    evolution.population = trained_population
    if evolution.run_generation():
        logger.info("Generation completed successfully")
        logger.info(f"Best fitness: {evolution.best_fitness:.4f}")
    else:
        logger.error("Generation failed")
        return False
    
    # Test 11: Run full evolution (small scale)
    logger.info("\nTest 11: Running full evolution (small scale)")
    evolution.generation = 0  # Reset generation counter
    evolution.best_fitness = float('inf')  # Reset best fitness
    
    if evolution.run_evolution():
        logger.info("Evolution completed successfully!")
        
        # Get summary
        summary = evolution.get_evolution_summary()
        logger.info("\nEvolution Summary:")
        for key, value in summary.items():
            if key != 'fitness_history':
                logger.info(f"  {key}: {value}")
        
        # Test 12: Save best AI
        logger.info("\nTest 12: Saving best AI")
        if evolution.best_ai:
            save_path = "test_best_ai.pkl"
            if evolution.save_best_ai(save_path):
                logger.info(f"Best AI saved to {save_path}")
            else:
                logger.error("Failed to save best AI")
        else:
            logger.warning("No best AI to save")
    
    else:
        logger.error("Evolution failed")
        return False
    
    logger.info("\n✅ All evolution tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_evolution_framework()
    if not success:
        sys.exit(1)

