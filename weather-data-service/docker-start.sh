#!/bin/bash

# Weather Data Service - Docker Startup Script
# This script initializes the database and starts the weather data service

set -e  # Exit on any error

echo "🌤️  Weather Data Service - Docker Startup"
echo "=========================================="

# Check for required environment variables
if [ -z "$NOAA_CDO_TOKEN" ]; then
    echo "❌ Error: NOAA_CDO_TOKEN environment variable is required"
    echo "   Set it with: export NOAA_CDO_TOKEN=your_token_here"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Initialize database if it doesn't exist
if [ ! -f "data/weather_pool.db" ]; then
    echo "🗄️  Initializing database..."
    python3 init_database.py
else
    echo "✅ Database already exists"
fi

# Start the API service
echo "🚀 Starting Weather Data Collection API..."
python3 api.py
