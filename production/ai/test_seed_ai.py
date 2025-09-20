#!/usr/bin/env python3
"""
Test Seed AI
============
Test the SeedAI class with the generated training data.
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from seed_ai import SeedAI
from ai_config import AIConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_seed_ai():
    """Test the SeedAI class"""
    logger.info("🧪 Testing SeedAI class")
    
    # Test 1: Create AI with default config
    logger.info("Test 1: Creating AI with default config")
    config = AIConfig.smart_defaults()
    ai = SeedAI(config=config, model_id="test_ai_001")
    
    logger.info(f"AI created: {ai.model_id}")
    logger.info(f"Config: max_depth={config.max_depth}, n_estimators={config.n_estimators}")
    
    # Test 2: Load training data
    logger.info("\nTest 2: Loading training data")
    training_path = "training/training_dataset.csv"
    
    if not Path(training_path).exists():
        logger.error(f"Training data not found: {training_path}")
        return False
    
    if not ai.load_training_data(training_path):
        logger.error("Failed to load training data")
        return False
    
    logger.info(f"Training data loaded: {len(ai.training_data)} samples")
    logger.info(f"Features: {len(ai.feature_columns)} columns")
    
    # Test 3: Train the model
    logger.info("\nTest 3: Training the model")
    if not ai.train():
        logger.error("Failed to train model")
        return False
    
    logger.info(f"Model trained successfully in {ai.training_time:.2f}s")
    
    # Test 4: Make predictions
    logger.info("\nTest 4: Making predictions")
    test_cases = [
        ("12345", "2024-06-15"),
        ("67890", "2024-07-20"),
        ("11111", "2024-08-10")
    ]
    
    for cell_id, date in test_cases:
        prediction = ai.predict(cell_id, date)
        if prediction:
            logger.info(f"Cell {cell_id} on {date}: {prediction['fire_probability']:.3f} probability")
        else:
            logger.error(f"Prediction failed for cell {cell_id}")
    
    # Test 5: Evaluate on test data
    logger.info("\nTest 5: Evaluating on test data")
    test_path = "training/test_pool.csv"
    
    if Path(test_path).exists():
        import pandas as pd
        test_data = pd.read_csv(test_path)
        logger.info(f"Test data loaded: {len(test_data)} samples")
        
        # Evaluate on subset for speed
        test_subset = test_data.sample(n=min(100, len(test_data)), random_state=42)
        metrics = ai.evaluate(test_subset)
        
        logger.info("Evaluation metrics:")
        for metric, value in metrics.items():
            if isinstance(value, float):
                logger.info(f"  {metric}: {value:.4f}")
            else:
                logger.info(f"  {metric}: {value}")
    
    # Test 6: Save and load model
    logger.info("\nTest 6: Save and load model")
    save_path = "test_model.pkl"
    
    if ai.save(save_path):
        logger.info("Model saved successfully")
        
        # Load the model
        loaded_ai = SeedAI.load(save_path)
        if loaded_ai:
            logger.info("Model loaded successfully")
            logger.info(f"Loaded model ID: {loaded_ai.model_id}")
            logger.info(f"Loaded model trained: {loaded_ai.is_trained}")
        else:
            logger.error("Failed to load model")
    
    # Test 7: Get summary
    logger.info("\nTest 7: Model summary")
    summary = ai.get_summary()
    logger.info("Model summary:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_seed_ai()
    if not success:
        sys.exit(1)

