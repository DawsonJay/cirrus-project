#!/usr/bin/env python3
"""
Evolution Framework for AI Competition
=====================================
Competitive evolution system for optimizing wildfire prediction AIs.
"""

import pandas as pd
import numpy as np
import random
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

from seed_ai import SeedAI
from ai_config import AIConfig, EvolutionConfig

logger = logging.getLogger(__name__)


class EvolutionFramework:
    """Competitive evolution framework for AI optimization"""
    
    def __init__(self, evolution_config: EvolutionConfig, training_data_path: str = "training/training_dataset.csv"):
        self.config = evolution_config
        self.training_data_path = training_data_path
        self.test_pool_path = evolution_config.test_pool_path
        
        # Population management
        self.population: List[SeedAI] = []
        self.generation = 0
        self.best_ai: Optional[SeedAI] = None
        self.best_fitness = float('inf')
        self.fitness_history: List[float] = []
        self.generation_times: List[float] = []
        
        # Test data
        self.test_pool: Optional[pd.DataFrame] = None
        self.current_test_samples: Optional[pd.DataFrame] = None
        
        # Performance tracking
        self.total_training_time = 0.0
        self.total_evaluation_time = 0.0
        
    def load_test_pool(self) -> bool:
        """Load the test pool for evaluation"""
        try:
            self.test_pool = pd.read_csv(self.test_pool_path)
            logger.info(f"Loaded test pool: {len(self.test_pool)} samples")
            return True
        except Exception as e:
            logger.error(f"Failed to load test pool: {e}")
            return False
    
    def select_test_samples(self) -> pd.DataFrame:
        """Select random test samples for current generation"""
        if self.test_pool is None:
            raise ValueError("Test pool not loaded")
        
        # Sample random test cases for this generation (different each time)
        n_samples = min(self.config.test_samples_per_generation, len(self.test_pool))
        self.current_test_samples = self.test_pool.sample(n=n_samples, random_state=self.generation)
        
        logger.info(f"Selected {len(self.current_test_samples)} test samples for generation {self.generation}")
        return self.current_test_samples
    
    def create_initial_population(self) -> List[SeedAI]:
        """Create initial population with hybrid strategy"""
        population = []
        
        # Smart defaults (5 AIs)
        for i in range(5):
            config = AIConfig.smart_defaults()
            ai = SeedAI(config=config, model_id=f"ai_{i:03d}_smart")
            population.append(ai)
        
        # Random configurations (remaining AIs)
        for i in range(5, self.config.population_size):
            config = AIConfig.random_config()
            ai = SeedAI(config=config, model_id=f"ai_{i:03d}_random")
            population.append(ai)
        
        logger.info(f"Created initial population: {len(population)} AIs")
        logger.info(f"  Smart defaults: 5 AIs")
        logger.info(f"  Random configs: {len(population) - 5} AIs")
        
        return population
    
    def train_ai_parallel(self, ai: SeedAI) -> Tuple[SeedAI, bool]:
        """Train a single AI with timeout"""
        try:
            # Load training data
            if not ai.load_training_data(self.training_data_path):
                return ai, False
            
            # Train with timeout
            start_time = time.time()
            success = ai.train()
            training_time = time.time() - start_time
            
            if success:
                logger.debug(f"AI {ai.model_id} trained in {training_time:.2f}s")
                return ai, True
            else:
                logger.warning(f"AI {ai.model_id} training failed")
                return ai, False
                
        except Exception as e:
            logger.error(f"AI {ai.model_id} training error: {e}")
            return ai, False
    
    def train_population(self, population: List[SeedAI]) -> List[SeedAI]:
        """Train entire population in parallel"""
        logger.info(f"Training population of {len(population)} AIs...")
        start_time = time.time()
        
        # Use ProcessPoolExecutor for parallel training
        max_workers = min(4, mp.cpu_count())  # Limit to 4 cores for stability
        trained_population = []
        successful_count = 0
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all training tasks
            future_to_ai = {executor.submit(self.train_ai_parallel, ai): ai for ai in population}
            
            # Collect results
            for future in as_completed(future_to_ai):
                ai, success = future.result()
                trained_population.append(ai)
                if success:
                    successful_count += 1
        
        training_time = time.time() - start_time
        self.total_training_time += training_time
        
        logger.info(f"Population training complete: {successful_count}/{len(population)} successful in {training_time:.2f}s")
        
        return trained_population
    
    def evaluate_ai(self, ai: SeedAI) -> float:
        """Evaluate AI fitness using Log Loss"""
        if not ai.is_trained:
            return float('inf')  # Worst possible fitness
        
        try:
            # Use current test samples
            if self.current_test_samples is None:
                self.select_test_samples()
            
            # Evaluate on test samples
            metrics = ai.evaluate(self.current_test_samples)
            
            if 'error' in metrics:
                logger.warning(f"AI {ai.model_id} evaluation error: {metrics['error']}")
                return float('inf')
            
            # Primary metric: Log Loss (lower is better)
            fitness = metrics['log_loss']
            
            # Add penalty for slow predictions
            avg_pred_time = metrics.get('avg_prediction_time', 0.0)
            if avg_pred_time > 1.0:  # Penalty for slow predictions
                fitness += (avg_pred_time - 1.0) * 0.1
            
            logger.debug(f"AI {ai.model_id} fitness: {fitness:.4f} (log_loss: {metrics['log_loss']:.4f})")
            return fitness
            
        except Exception as e:
            logger.error(f"AI {ai.model_id} evaluation failed: {e}")
            return float('inf')
    
    def evaluate_population(self, population: List[SeedAI]) -> List[Tuple[SeedAI, float]]:
        """Evaluate entire population and return sorted results"""
        logger.info(f"Evaluating population of {len(population)} AIs...")
        start_time = time.time()
        
        # Evaluate all AIs
        results = []
        for ai in population:
            fitness = self.evaluate_ai(ai)
            results.append((ai, fitness))
        
        # Sort by fitness (lower is better)
        results.sort(key=lambda x: x[1])
        
        evaluation_time = time.time() - start_time
        self.total_evaluation_time += evaluation_time
        
        # Log results
        best_fitness = results[0][1] if results else float('inf')
        worst_fitness = results[-1][1] if results else float('inf')
        
        logger.info(f"Population evaluation complete in {evaluation_time:.2f}s")
        logger.info(f"  Best fitness: {best_fitness:.4f}")
        logger.info(f"  Worst fitness: {worst_fitness:.4f}")
        logger.info(f"  Average fitness: {np.mean([f for _, f in results]):.4f}")
        
        return results
    
    def select_elite(self, results: List[Tuple[SeedAI, float]]) -> List[SeedAI]:
        """Select elite AIs for next generation"""
        elite_count = min(self.config.elite_count, len(results))
        elite = [ai for ai, fitness in results[:elite_count]]
        
        logger.info(f"Selected {len(elite)} elite AIs")
        return elite
    
    def create_offspring(self, elite: List[SeedAI]) -> List[SeedAI]:
        """Create offspring through crossover and mutation"""
        offspring = []
        
        # Keep elite unchanged
        offspring.extend(elite)
        
        # Create offspring to fill population
        while len(offspring) < self.config.population_size:
            # Select parents (tournament selection)
            parent1 = self.tournament_selection(elite)
            parent2 = self.tournament_selection(elite)
            
            # Crossover
            if random.random() < self.config.crossover_rate:
                child_config = AIConfig.crossover(parent1.config, parent2.config)
            else:
                child_config = random.choice([parent1.config, parent2.config])
            
            # Mutation
            child_config = child_config.mutate(self.config.mutation_rate)
            
            # Create child AI
            child_id = f"ai_{len(offspring):03d}_gen{self.generation}"
            child_ai = SeedAI(config=child_config, model_id=child_id)
            offspring.append(child_ai)
        
        logger.info(f"Created {len(offspring)} offspring (including {len(elite)} elite)")
        return offspring
    
    def tournament_selection(self, population: List[SeedAI], tournament_size: int = 3) -> SeedAI:
        """Tournament selection for parent selection"""
        tournament = random.sample(population, min(tournament_size, len(population)))
        
        # Return best from tournament (lowest fitness)
        best_ai = tournament[0]
        best_fitness = float('inf')
        
        for ai in tournament:
            # Quick fitness check (simplified)
            if hasattr(ai, '_last_fitness'):
                fitness = ai._last_fitness
            else:
                fitness = random.uniform(0, 1)  # Placeholder
            
            if fitness < best_fitness:
                best_fitness = fitness
                best_ai = ai
        
        return best_ai
    
    def run_generation(self) -> bool:
        """Run one generation of evolution"""
        generation_start = time.time()
        
        logger.info(f"\n🧬 Generation {self.generation + 1}/{self.config.max_generations}")
        logger.info("=" * 50)
        
        # Select test samples for this generation
        self.select_test_samples()
        
        # Train population
        self.population = self.train_population(self.population)
        
        # Evaluate population
        results = self.evaluate_population(self.population)
        
        # Update best AI
        if results and results[0][1] < self.best_fitness:
            self.best_ai = results[0][0]
            self.best_fitness = results[0][1]
            logger.info(f"🏆 New best AI: {self.best_ai.model_id} (fitness: {self.best_fitness:.4f})")
        
        # Track fitness history
        self.fitness_history.append(self.best_fitness)
        
        # Select elite and create offspring
        elite = self.select_elite(results)
        self.population = self.create_offspring(elite)
        
        # Track generation time
        generation_time = time.time() - generation_start
        self.generation_times.append(generation_time)
        
        logger.info(f"Generation {self.generation + 1} complete in {generation_time:.2f}s")
        
        self.generation += 1
        return True
    
    def check_convergence(self) -> bool:
        """Check if evolution has converged"""
        if len(self.fitness_history) < self.config.early_stopping_patience:
            return False
        
        # Check if best fitness has improved in last N generations
        recent_fitness = self.fitness_history[-self.config.early_stopping_patience:]
        return len(set([round(f, 4) for f in recent_fitness])) == 1
    
    def run_evolution(self) -> bool:
        """Run complete evolution process"""
        logger.info("🚀 Starting AI Evolution Process")
        logger.info("=" * 60)
        logger.info(f"Population size: {self.config.population_size}")
        logger.info(f"Max generations: {self.config.max_generations}")
        logger.info(f"Test samples per generation: {self.config.test_samples_per_generation}")
        logger.info(f"Elite count: {self.config.elite_count}")
        logger.info("")
        
        # Load test pool
        if not self.load_test_pool():
            logger.error("Failed to load test pool")
            return False
        
        # Create initial population
        self.population = self.create_initial_population()
        
        # Run generations
        for gen in range(self.config.max_generations):
            if not self.run_generation():
                logger.error(f"Generation {gen + 1} failed")
                return False
            
            # Check convergence
            if self.check_convergence():
                logger.info(f"🎯 Convergence detected after {gen + 1} generations")
                break
        
        logger.info("\n🏁 Evolution Complete!")
        logger.info("=" * 40)
        logger.info(f"Total generations: {self.generation}")
        logger.info(f"Best fitness: {self.best_fitness:.4f}")
        logger.info(f"Total training time: {self.total_training_time:.2f}s")
        logger.info(f"Total evaluation time: {self.total_evaluation_time:.2f}s")
        
        return True
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of evolution process"""
        return {
            'generations': self.generation,
            'best_fitness': self.best_fitness,
            'best_ai_id': self.best_ai.model_id if self.best_ai else None,
            'total_training_time': self.total_training_time,
            'total_evaluation_time': self.total_evaluation_time,
            'avg_generation_time': np.mean(self.generation_times) if self.generation_times else 0.0,
            'fitness_history': self.fitness_history,
            'population_size': self.config.population_size,
            'test_samples': self.config.test_samples_per_generation
        }
    
    def save_best_ai(self, filepath: str) -> bool:
        """Save the best evolved AI"""
        if self.best_ai is None:
            logger.error("No best AI to save")
            return False
        
        return self.best_ai.save(filepath)
