#!/bin/bash

# Weather Data Service - Production Deployment Script
# This script deploys the weather data service for background operation

set -e  # Exit on any error

echo "🌤️  Weather Data Service - Production Deployment"
echo "================================================"

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

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp env.production .env
    echo "⚠️  Please edit .env file and add your NOAA_CDO_TOKEN"
    echo "   Then run this script again"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Stop any existing services
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.prod.yml down || true

# Start services
echo "🚀 Starting weather data services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API service is healthy"
else
    echo "❌ API service health check failed"
    echo "   Check logs with: docker-compose -f docker-compose.prod.yml logs"
    exit 1
fi

# Show service status
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Service Information:"
echo "  API URL: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo ""
echo "📝 Useful Commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  View status: docker-compose -f docker-compose.prod.yml ps"
echo ""
echo "🔄 Data Collection:"
echo "  The collector will run daily at 2:00 AM"
echo "  You can trigger manual collection via the API"
echo "  Check collection status: curl http://localhost:8000/status"
