#!/bin/bash

# Weather Data Service - Management Script
# This script provides easy management commands for the weather data service

set -e

COMPOSE_FILE="docker-compose.prod.yml"

case "$1" in
    "start")
        echo "🚀 Starting weather data services..."
        docker-compose -f $COMPOSE_FILE up -d
        echo "✅ Services started"
        ;;
    "stop")
        echo "🛑 Stopping weather data services..."
        docker-compose -f $COMPOSE_FILE down
        echo "✅ Services stopped"
        ;;
    "restart")
        echo "🔄 Restarting weather data services..."
        docker-compose -f $COMPOSE_FILE restart
        echo "✅ Services restarted"
        ;;
    "status")
        echo "📊 Service Status:"
        docker-compose -f $COMPOSE_FILE ps
        ;;
    "logs")
        echo "📝 Viewing logs (Ctrl+C to exit)..."
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    "health")
        echo "🔍 Checking service health..."
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API service is healthy"
        else
            echo "❌ API service is not responding"
        fi
        ;;
    "collect")
        echo "🌤️  Triggering manual data collection..."
        curl -X POST http://localhost:8000/collect/year \
          -H "Content-Type: application/json" \
          -d '{"year": 2024, "limit": 10}'
        echo ""
        echo "✅ Collection triggered (check status with: ./manage.sh status)"
        ;;
    "stats")
        echo "📊 Weather Data Statistics:"
        curl -s http://localhost:8000/weather-data | python3 -m json.tool
        ;;
    "stations")
        echo "📡 Weather Stations:"
        curl -s http://localhost:8000/stations | python3 -m json.tool | head -20
        echo "... (truncated, use API directly for full list)"
        ;;
    "backup")
        echo "💾 Creating database backup..."
        BACKUP_FILE="data/weather_pool_backup_$(date +%Y%m%d_%H%M%S).db"
        cp data/weather_pool.db "$BACKUP_FILE"
        echo "✅ Backup created: $BACKUP_FILE"
        ;;
    "update")
        echo "🔄 Updating services..."
        docker-compose -f $COMPOSE_FILE pull
        docker-compose -f $COMPOSE_FILE build
        docker-compose -f $COMPOSE_FILE up -d
        echo "✅ Services updated"
        ;;
    *)
        echo "🌤️  Weather Data Service Management"
        echo "=================================="
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  start     - Start all services"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status"
        echo "  logs      - View service logs"
        echo "  health    - Check service health"
        echo "  collect   - Trigger manual data collection"
        echo "  stats     - Show weather data statistics"
        echo "  stations  - List weather stations"
        echo "  backup    - Create database backup"
        echo "  update    - Update and restart services"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs"
        echo "  $0 collect"
        ;;
esac
