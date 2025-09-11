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
    
    # NOAA Data Sources (FREE - NO API KEYS REQUIRED)
    # NOAA CDO API Token (optional - for enhanced data access)
    # Get free token from: https://www.ncdc.noaa.gov/cdo-web/token
    NOAA_CDO_TOKEN: Optional[str] = os.getenv("NOAA_CDO_TOKEN")
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/weather_pool.db")
    
    # Data Collection Settings
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    
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
