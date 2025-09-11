#!/bin/bash

# Weather Data Service - Simple Deployment Script
# This script deploys the weather data service using individual Docker commands

set -e  # Exit on any error

echo "🌤️  Weather Data Service - Simple Deployment"
echo "============================================="

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for required environment variables
if [ -z "$NOAA_CDO_TOKEN" ]; then
    echo "❌ Error: NOAA_CDO_TOKEN environment variable is required"
    echo "   Set it with: export NOAA_CDO_TOKEN=your_token_here"
    echo "   Or create a .env file with your token"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs

# Build Docker images
echo "🐳 Building Docker images..."
sudo docker build -t weather-data-service ./weather-data-service
sudo docker build -f ./weather-data-service/Dockerfile.collector -t weather-data-collector ./weather-data-service

# Stop any existing services
echo "🛑 Stopping existing services..."
sudo docker stop weather-data-api weather-data-collector 2>/dev/null || true
sudo docker rm weather-data-api weather-data-collector 2>/dev/null || true

# Start API service
echo "🚀 Starting API service..."
sudo docker run -d \
  --name weather-data-api \
  -p 8000:8000 \
  -e NOAA_CDO_TOKEN="$NOAA_CDO_TOKEN" \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  --restart unless-stopped \
  weather-data-service

# Wait for API to start
echo "⏳ Waiting for API service to start..."
sleep 10

# Check API health
echo "🔍 Checking API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API service is healthy"
else
    echo "❌ API service health check failed"
    echo "   Check logs with: sudo docker logs weather-data-api"
    exit 1
fi

# Start collector service
echo "🔄 Starting collector service..."
sudo docker run -d \
  --name weather-data-collector \
  -e NOAA_CDO_TOKEN="$NOAA_CDO_TOKEN" \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  --restart unless-stopped \
  weather-data-collector

# Show service status
echo "📊 Service Status:"
sudo docker ps --filter "name=weather-data"

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Service Information:"
echo "  API URL: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo ""
echo "📝 Useful Commands:"
echo "  View logs: sudo docker logs -f weather-data-api"
echo "  Stop services: sudo docker stop weather-data-api weather-data-collector"
echo "  Restart services: sudo docker restart weather-data-api weather-data-collector"
echo "  View status: sudo docker ps --filter 'name=weather-data'"
echo ""
echo "🔄 Data Collection:"
echo "  The collector will run daily at 2:00 AM"
echo "  You can trigger manual collection via the API"
echo "  Check collection status: curl http://localhost:8000/status"
