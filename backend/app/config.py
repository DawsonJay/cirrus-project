"""
Configuration settings for the Cirrus Project backend
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # API Configuration
    API_TITLE: str = "Cirrus Project API"
    API_DESCRIPTION: str = "Canadian Weather AI Prediction System"
    API_VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Configuration
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Weather API Keys
    OPEN_METEO_API_KEY: Optional[str] = os.getenv("OPEN_METEO_API_KEY")  # Not required
    ENVIRONMENT_CANADA_API_KEY: Optional[str] = os.getenv("ENVIRONMENT_CANADA_API_KEY")  # Not required
    WEATHER_UNLOCKED_APP_ID: Optional[str] = os.getenv("WEATHER_UNLOCKED_APP_ID")
    WEATHER_UNLOCKED_API_KEY: Optional[str] = os.getenv("WEATHER_UNLOCKED_API_KEY")
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    
    # Data Storage
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    RAW_DATA_DIR: str = os.getenv("RAW_DATA_DIR", "data/raw")
    PROCESSED_DATA_DIR: str = os.getenv("PROCESSED_DATA_DIR", "data/processed")
    
    # Cache Configuration
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes in seconds
    MAX_CACHE_SIZE: int = int(os.getenv("MAX_CACHE_SIZE", "1000"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour in seconds

# Global settings instance
settings = Settings()
