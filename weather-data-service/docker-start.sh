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

# Initialize database (always run for PostgreSQL, check for SQLite)
if [ -n "$DATABASE_URL" ]; then
    # PostgreSQL (Railway) - always initialize
    echo "🗄️  Initializing PostgreSQL database..."
    python3 init_database.py
else
    # SQLite (local) - check if file exists
    if [ ! -f "data/weather_pool.db" ]; then
        echo "🗄️  Initializing SQLite database..."
        python3 init_database.py
    else
        echo "✅ SQLite database already exists"
    fi
fi

# Load Canadian stations if database is empty
echo "🇨🇦 Checking and loading Canadian stations..."
python3 startup_load_stations.py

# Start the API service
echo "🚀 Starting Weather Data Collection API..."
python3 api.py
