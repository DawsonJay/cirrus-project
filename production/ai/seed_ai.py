#!/usr/bin/env python3
"""
Seed AI for Wildfire Prediction
===============================
Base AI model using XGBoost for wildfire probability prediction.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import sqlite3
import time
import signal
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from ai_config import AIConfig

logger = logging.getLogger(__name__)


class SeedAI:
    """Base AI model for wildfire prediction using XGBoost"""
    
    def __init__(self, config: AIConfig = None, model_id: str = "seed_ai_v1"):
        self.config = config or AIConfig()
        self.model_id = model_id
        self.model = None
        self.is_trained = False
        self.training_data = None
        self.feature_columns = None
        
        # Performance tracking
        self.training_time = 0.0
        self.prediction_times = []
        
    def load_training_data(self, training_data_path: str) -> bool:
        """Load training data from CSV file"""
        try:
            self.training_data = pd.read_csv(training_data_path)
            logger.info(f"Loaded training data: {len(self.training_data)} samples")
            
            # Separate features and target
            self.feature_columns = [col for col in self.training_data.columns 
                                  if col not in ['cell_id', 'target_date', 'fire_occurred']]
            
            logger.info(f"Feature columns: {len(self.feature_columns)}")
            logger.info(f"Features: {self.feature_columns[:10]}...")  # Show first 10
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
            return False
    
    def train(self) -> bool:
        """Train the XGBoost model"""
        if self.training_data is None:
            logger.error("No training data loaded")
            return False
        
        try:
            start_time = time.time()
            
            # Prepare features and target
            X = self.training_data[self.feature_columns].copy()
            y = self.training_data['fire_occurred']
            
            # Handle categorical features
            categorical_columns = X.select_dtypes(include=['object']).columns
            for col in categorical_columns:
                # Simple label encoding for categorical features
                X[col] = X[col].astype('category').cat.codes
            
            # Handle missing values
            X = X.fillna(0.0)
            
            # Check class distribution
            fire_count = y.sum()
            total_count = len(y)
            fire_ratio = fire_count / total_count if total_count > 0 else 0
            
            logger.info(f"Training data: {fire_count}/{total_count} fire samples ({fire_ratio:.1%})")
            
            # Create XGBoost classifier with timeout
            def timeout_handler(signum, frame):
                raise TimeoutError("Training timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(self.config.training_timeout))
            
            try:
                # Handle class imbalance
                if fire_count == 0 or fire_count == total_count:
                    logger.warning("No class diversity - using simple model")
                    self.model = xgb.XGBClassifier(
                        n_estimators=10,
                        max_depth=3,
                        random_state=self.config.random_state,
                        n_jobs=self.config.n_jobs
                    )
                else:
                    # Calculate scale_pos_weight for class imbalance
                    scale_pos_weight = (total_count - fire_count) / fire_count if fire_count > 0 else 1.0
                    scale_pos_weight = min(scale_pos_weight, 5.0)  # Cap at 5x
                    
                    self.model = xgb.XGBClassifier(
                        max_depth=self.config.max_depth,
                        n_estimators=self.config.n_estimators,
                        learning_rate=self.config.learning_rate,
                        subsample=self.config.subsample,
                        colsample_bytree=self.config.colsample_bytree,
                        reg_alpha=self.config.reg_alpha,
                        reg_lambda=self.config.reg_lambda,
                        scale_pos_weight=scale_pos_weight,
                        random_state=self.config.random_state,
                        n_jobs=self.config.n_jobs,
                        eval_metric='logloss',
                        verbosity=0
                    )
                
                # Train the model with validation split for early stopping
                from sklearn.model_selection import train_test_split
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=0.2, random_state=self.config.random_state, stratify=y
                )
                
                self.model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=self.config.early_stopping_rounds,
                    verbose=False
                )
                self.is_trained = True
                
                signal.alarm(0)  # Cancel timeout
                
                self.training_time = time.time() - start_time
                logger.info(f"Model trained successfully in {self.training_time:.2f}s")
                
                return True
                
            except TimeoutError:
                signal.alarm(0)  # Cancel timeout
                logger.error("Training timeout - using fallback model")
                
                # Create simple fallback model
                self.model = xgb.XGBClassifier(
                    n_estimators=10,
                    max_depth=3,
                    random_state=self.config.random_state,
                    n_jobs=self.config.n_jobs
                )
                self.model.fit(X, y)
                self.is_trained = True
                
                self.training_time = time.time() - start_time
                logger.warning(f"Fallback model trained in {self.training_time:.2f}s")
                return True
                
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def predict(self, cell_id: str, target_date: str) -> Optional[Dict[str, Any]]:
        """Predict wildfire probability for a cell-date combination"""
        if not self.is_trained:
            logger.error("Model not trained")
            return None
        
        try:
            start_time = time.time()
            
            # Create timeout handler
            def timeout_handler(signum, frame):
                raise TimeoutError("Prediction timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(self.config.prediction_timeout))
            
            try:
                # For now, create a simple prediction based on training data
                # In a real implementation, this would generate features from the database
                
                # Find similar samples in training data
                similar_samples = self.training_data[
                    (self.training_data['cell_id'] == int(cell_id)) |
                    (self.training_data['terrain_type'] == 'forest')  # Default to forest if no match
                ]
                
                if len(similar_samples) == 0:
                    # Use average of all samples
                    similar_samples = self.training_data
                
                # Calculate average fire probability
                avg_fire_prob = similar_samples['fire_occurred'].mean()
                
                # Add some randomness based on date (seasonal effect)
                month = int(target_date.split('-')[1])
                seasonal_factor = 1.0 + 0.3 * np.sin(2 * np.pi * (month - 6) / 12)  # Peak in summer
                
                fire_probability = min(0.95, max(0.05, avg_fire_prob * seasonal_factor))
                
                signal.alarm(0)  # Cancel timeout
                
                prediction_time = time.time() - start_time
                self.prediction_times.append(prediction_time)
                
                return {
                    'fire_probability': fire_probability,
                    'prediction_time': prediction_time,
                    'model_id': self.model_id,
                    'confidence': 0.8  # Placeholder confidence
                }
                
            except TimeoutError:
                signal.alarm(0)  # Cancel timeout
                logger.error("Prediction timeout")
                return None
                
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None
    
    def evaluate(self, test_data: pd.DataFrame) -> Dict[str, float]:
        """Evaluate model performance on test data"""
        if not self.is_trained:
            return {'error': 'Model not trained'}
        
        try:
            # Prepare test features
            X_test = test_data[self.feature_columns].copy()
            y_test = test_data['fire_occurred']
            
            # Handle categorical features (same as training)
            categorical_columns = X_test.select_dtypes(include=['object']).columns
            for col in categorical_columns:
                X_test[col] = X_test[col].astype('category').cat.codes
            
            X_test = X_test.fillna(0.0)
            
            # Make predictions
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]  # Probability of fire
            
            # Calculate metrics
            from sklearn.metrics import log_loss, roc_auc_score, precision_score, recall_score, f1_score
            
            # Log loss (primary metric)
            logloss = log_loss(y_test, y_pred_proba)
            
            # ROC AUC
            try:
                roc_auc = roc_auc_score(y_test, y_pred_proba)
            except ValueError:
                roc_auc = 0.5  # Random performance if only one class
            
            # Precision, Recall, F1
            y_pred = (y_pred_proba > 0.5).astype(int)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            return {
                'log_loss': logloss,
                'roc_auc': roc_auc,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'fire_rate': y_test.mean(),
                'avg_prediction_time': np.mean(self.prediction_times) if self.prediction_times else 0.0
            }
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {'error': str(e)}
    
    def save(self, filepath: str) -> bool:
        """Save the trained model"""
        try:
            import pickle
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'config': self.config,
                    'model_id': self.model_id,
                    'feature_columns': self.feature_columns,
                    'is_trained': self.is_trained
                }, f)
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    @classmethod
    def load(cls, filepath: str) -> Optional['SeedAI']:
        """Load a trained model"""
        try:
            import pickle
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            ai = cls(config=data['config'], model_id=data['model_id'])
            ai.model = data['model']
            ai.feature_columns = data['feature_columns']
            ai.is_trained = data['is_trained']
            
            logger.info(f"Model loaded from {filepath}")
            return ai
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get model summary information"""
        return {
            'model_id': self.model_id,
            'is_trained': self.is_trained,
            'training_time': self.training_time,
            'config': self.config.to_dict(),
            'feature_count': len(self.feature_columns) if self.feature_columns else 0,
            'avg_prediction_time': np.mean(self.prediction_times) if self.prediction_times else 0.0
        }
