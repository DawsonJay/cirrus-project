#!/bin/bash

# Weather Data Collector Runner
# This script runs the daily collection process

echo "🌤️  Weather Data Collector"
echo "=========================="
echo "📅 Date: $(date)"
echo "🔧 Environment: ${ENVIRONMENT:-development}"
echo "🗄️  Database: ${DATABASE_PATH:-data/weather_pool.db}"
echo "=========================="

# Check for required environment variables
if [ -z "$NOAA_CDO_TOKEN" ]; then
    echo "❌ Error: NOAA_CDO_TOKEN environment variable is required"
    echo "   Set it with: export NOAA_CDO_TOKEN=your_token_here"
    exit 1
fi

# Run the collection
echo "🚀 Starting daily collection..."
python3 main.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Collection completed successfully"
else
    echo "❌ Collection failed"
    exit 1
fi
