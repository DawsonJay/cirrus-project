#!/usr/bin/env python3
"""
AI Configuration Classes
========================
Configuration classes for XGBoost parameters and AI behavior.
"""

import random
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class AIConfig:
    """Configuration for XGBoost parameters and AI behavior"""
    
    # XGBoost parameters (evolvable)
    max_depth: int = 6
    n_estimators: int = 100
    learning_rate: float = 0.1
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_alpha: float = 0.0
    reg_lambda: float = 0.0
    early_stopping_rounds: int = 20
    
    # Performance constraints
    prediction_timeout: float = 3.0  # seconds
    training_timeout: float = 30.0   # seconds
    
    # Model behavior
    random_state: int = 42
    n_jobs: int = 1  # Single-threaded for parallel evolution
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization"""
        return {
            'max_depth': self.max_depth,
            'n_estimators': self.n_estimators,
            'learning_rate': self.learning_rate,
            'subsample': self.subsample,
            'colsample_bytree': self.colsample_bytree,
            'reg_alpha': self.reg_alpha,
            'reg_lambda': self.reg_lambda,
            'early_stopping_rounds': self.early_stopping_rounds,
            'prediction_timeout': self.prediction_timeout,
            'training_timeout': self.training_timeout,
            'random_state': self.random_state,
            'n_jobs': self.n_jobs
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AIConfig':
        """Create config from dictionary"""
        return cls(**config_dict)
    
    @classmethod
    def random_config(cls) -> 'AIConfig':
        """Generate random configuration within valid ranges"""
        return cls(
            max_depth=random.randint(3, 15),
            n_estimators=random.randint(50, 500),
            learning_rate=random.uniform(0.01, 0.3),
            subsample=random.uniform(0.6, 1.0),
            colsample_bytree=random.uniform(0.6, 1.0),
            reg_alpha=random.uniform(0.0, 10.0),
            reg_lambda=random.uniform(0.0, 10.0),
            early_stopping_rounds=random.randint(10, 50)
        )
    
    @classmethod
    def smart_defaults(cls) -> 'AIConfig':
        """Generate smart default configuration"""
        return cls(
            max_depth=6,
            n_estimators=100,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.0,
            reg_lambda=0.0,
            early_stopping_rounds=20
        )
    
    def mutate(self, mutation_rate: float = 0.1) -> 'AIConfig':
        """Apply mutation to configuration"""
        new_config = AIConfig.from_dict(self.to_dict())
        
        if random.random() < mutation_rate:
            new_config.max_depth = max(3, min(15, new_config.max_depth + random.randint(-2, 2)))
        
        if random.random() < mutation_rate:
            new_config.n_estimators = max(50, min(500, new_config.n_estimators + random.randint(-50, 50)))
        
        if random.random() < mutation_rate:
            new_config.learning_rate = max(0.01, min(0.3, new_config.learning_rate + random.uniform(-0.05, 0.05)))
        
        if random.random() < mutation_rate:
            new_config.subsample = max(0.6, min(1.0, new_config.subsample + random.uniform(-0.1, 0.1)))
        
        if random.random() < mutation_rate:
            new_config.colsample_bytree = max(0.6, min(1.0, new_config.colsample_bytree + random.uniform(-0.1, 0.1)))
        
        if random.random() < mutation_rate:
            new_config.reg_alpha = max(0.0, min(10.0, new_config.reg_alpha + random.uniform(-1.0, 1.0)))
        
        if random.random() < mutation_rate:
            new_config.reg_lambda = max(0.0, min(10.0, new_config.reg_lambda + random.uniform(-1.0, 1.0)))
        
        if random.random() < mutation_rate:
            new_config.early_stopping_rounds = max(10, min(50, new_config.early_stopping_rounds + random.randint(-5, 5)))
        
        return new_config
    
    @classmethod
    def crossover(cls, parent1: 'AIConfig', parent2: 'AIConfig') -> 'AIConfig':
        """Create offspring through blend crossover"""
        return cls(
            max_depth=random.choice([parent1.max_depth, parent2.max_depth]),
            n_estimators=random.choice([parent1.n_estimators, parent2.n_estimators]),
            learning_rate=random.uniform(parent1.learning_rate, parent2.learning_rate),
            subsample=random.uniform(parent1.subsample, parent2.subsample),
            colsample_bytree=random.uniform(parent1.colsample_bytree, parent2.colsample_bytree),
            reg_alpha=random.uniform(parent1.reg_alpha, parent2.reg_alpha),
            reg_lambda=random.uniform(parent1.reg_lambda, parent2.reg_lambda),
            early_stopping_rounds=random.choice([parent1.early_stopping_rounds, parent2.early_stopping_rounds])
        )


@dataclass
class EvolutionConfig:
    """Configuration for evolution process"""
    
    population_size: int = 50
    max_generations: int = 10
    test_samples_per_generation: int = 200
    elite_count: int = 5
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    early_stopping_patience: int = 3
    
    # Training data paths
    training_data_path: str = "training/training_dataset.csv"
    test_pool_path: str = "training/test_pool.csv"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization"""
        return {
            'population_size': self.population_size,
            'max_generations': self.max_generations,
            'test_samples_per_generation': self.test_samples_per_generation,
            'elite_count': self.elite_count,
            'mutation_rate': self.mutation_rate,
            'crossover_rate': self.crossover_rate,
            'early_stopping_patience': self.early_stopping_patience,
            'training_data_path': self.training_data_path,
            'test_pool_path': self.test_pool_path
        }

