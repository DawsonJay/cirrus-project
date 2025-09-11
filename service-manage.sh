#!/bin/bash

# Weather Data Service - Systemd Service Management Script
# This script provides easy management commands for the systemd service

set -e

SERVICE_NAME="weather-data-service"

case "$1" in
    "start")
        echo "🚀 Starting weather data service..."
        sudo systemctl start $SERVICE_NAME
        echo "✅ Service started"
        ;;
    "stop")
        echo "🛑 Stopping weather data service..."
        sudo systemctl stop $SERVICE_NAME
        echo "✅ Service stopped"
        ;;
    "restart")
        echo "🔄 Restarting weather data service..."
        sudo systemctl restart $SERVICE_NAME
        echo "✅ Service restarted"
        ;;
    "status")
        echo "📊 Service Status:"
        sudo systemctl status $SERVICE_NAME
        ;;
    "logs")
        echo "📝 Viewing service logs (Ctrl+C to exit)..."
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    "enable")
        echo "🔧 Enabling weather data service to start on boot..."
        sudo systemctl enable $SERVICE_NAME
        echo "✅ Service enabled"
        ;;
    "disable")
        echo "🔧 Disabling weather data service from starting on boot..."
        sudo systemctl disable $SERVICE_NAME
        echo "✅ Service disabled"
        ;;
    "health")
        echo "🔍 Checking service health..."
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API service is healthy"
        else
            echo "❌ API service is not responding"
        fi
        ;;
    "containers")
        echo "🐳 Docker Container Status:"
        sudo docker ps --filter 'name=weather-data'
        ;;
    "collect")
        echo "🌤️  Triggering manual data collection..."
        curl -X POST http://localhost:8000/collect/year \
          -H "Content-Type: application/json" \
          -d '{"year": 2024, "limit": 10}'
        echo ""
        echo "✅ Collection triggered (check status with: ./service-manage.sh status)"
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
    *)
        echo "🌤️  Weather Data Service - Systemd Management"
        echo "=============================================="
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  start      - Start the service"
        echo "  stop       - Stop the service"
        echo "  restart    - Restart the service"
        echo "  status     - Show service status"
        echo "  logs       - View service logs"
        echo "  enable     - Enable service to start on boot"
        echo "  disable    - Disable service from starting on boot"
        echo "  health     - Check API health"
        echo "  containers - Show Docker container status"
        echo "  collect    - Trigger manual data collection"
        echo "  stats      - Show weather data statistics"
        echo "  stations   - List weather stations"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs"
        echo "  $0 collect"
        echo ""
        echo "Service will automatically start on boot when enabled."
        ;;
esac
