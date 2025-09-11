# Weather Data Service - Docker Setup

This document explains how to run the Weather Data Service using Docker.

## Architecture

The Weather Data Service consists of two main components:

### 1. **Weather Data API** (`weather-data-api`)
- **Purpose**: Provides REST API endpoints for data collection and access
- **Command**: `python3 api.py`
- **Port**: 8000
- **Behavior**: Runs continuously, serves API requests

### 2. **Weather Data Collector** (`weather-data-collector`)
- **Purpose**: Runs daily data collection automatically
- **Command**: `python3 main.py` (via cron)
- **Schedule**: Daily at 2:00 AM
- **Behavior**: Runs once per day, collects data for current year

## Quick Start

### 1. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Get your token from https://www.ncdc.noaa.gov/cdo-web/token
NOAA_CDO_TOKEN=your_noaa_token_here

# Optional: Database path (default: data/weather_pool.db)
DATABASE_PATH=data/weather_pool.db

# Optional: Environment (default: development)
ENVIRONMENT=production
```

### 2. Build and Run

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### 3. Test the Services

```bash
# Test API health
curl http://localhost:8000/health

# Test API endpoints
curl http://localhost:8000/stations
curl http://localhost:8000/weather-data

# Check collector logs
docker-compose logs weather-data-collector
```

## Service Details

### Weather Data API

**Endpoints:**
- `GET /health` - Health check
- `GET /stations` - List all stations
- `GET /stations/{station_id}` - Get station details
- `GET /weather-data` - Get weather data summary
- `POST /collect/year` - Trigger collection for specific year
- `POST /collect/years` - Trigger collection for multiple years
- `GET /status` - Get collection status

**Docker Configuration:**
- **Image**: `weather-data-service:latest`
- **Port**: 8000
- **Restart**: `unless-stopped`
- **Health Check**: HTTP GET /health every 30s

### Weather Data Collector

**Functionality:**
- Runs daily at 2:00 AM via cron
- Collects data for current year
- Updates active periods
- Stores weather data
- Runs maintenance checks

**Docker Configuration:**
- **Image**: `weather-data-service:latest` (with cron)
- **Restart**: `unless-stopped`
- **Schedule**: Daily at 2:00 AM
- **Logs**: Written to `/app/logs/cron.log`

## Manual Operations

### Run Collection Manually

```bash
# Run collection for current year
docker-compose exec weather-data-collector python3 main.py

# Run test collection (limited stations)
docker-compose exec weather-data-collector python3 main.py --test

# Run collection for specific year
docker-compose exec weather-data-collector python3 collection.py --year 2023
```

### View Logs

```bash
# View all logs
docker-compose logs -f

# View API logs only
docker-compose logs -f weather-data-api

# View collector logs only
docker-compose logs -f weather-data-collector

# View cron logs
docker-compose exec weather-data-collector cat /app/logs/cron.log
```

### Database Access

```bash
# Access database directly
docker-compose exec weather-data-api sqlite3 /app/data/weather_pool.db

# Run SQL queries
docker-compose exec weather-data-api sqlite3 /app/data/weather_pool.db "SELECT COUNT(*) FROM daily_weather_data;"
```

## Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Kill the process
   sudo kill -9 <PID>
   ```

2. **NOAA API token not set**
   ```bash
   # Check environment variables
   docker-compose exec weather-data-api env | grep NOAA
   
   # Set in .env file
   echo "NOAA_CDO_TOKEN=your_token" >> .env
   ```

3. **Database not found**
   ```bash
   # Check if database exists
   docker-compose exec weather-data-api ls -la /app/data/
   
   # Create database directory
   docker-compose exec weather-data-api mkdir -p /app/data
   ```

4. **Collection not running**
   ```bash
   # Check cron status
   docker-compose exec weather-data-collector crontab -l
   
   # Check cron logs
   docker-compose exec weather-data-collector cat /app/logs/cron.log
   ```

### Debug Mode

```bash
# Run API in debug mode
docker-compose exec weather-data-api python3 api.py --debug

# Run collector with verbose output
docker-compose exec weather-data-collector python3 main.py --test
```

## Production Deployment

### Environment Variables

```bash
# Production .env
NOAA_CDO_TOKEN=your_production_token
DATABASE_PATH=/app/data/weather_pool.db
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Security Considerations

1. **API Token**: Keep NOAA token secure
2. **Database**: Use persistent volumes
3. **Logs**: Rotate logs regularly
4. **Monitoring**: Set up health checks
5. **Backup**: Backup database regularly

### Scaling

- **API Service**: Can be scaled horizontally
- **Collector**: Should run as single instance
- **Database**: Use external database for production

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check collection status
curl http://localhost:8000/status

# Check system resources
docker stats
```

### Log Monitoring

```bash
# Monitor logs in real-time
docker-compose logs -f

# Check specific log files
docker-compose exec weather-data-collector tail -f /app/logs/cron.log
```

## Maintenance

### Database Maintenance

```bash
# Run maintenance manually
docker-compose exec weather-data-api python3 automated_maintenance.py --type daily

# Check maintenance status
docker-compose exec weather-data-api python3 automated_maintenance.py --type check
```

### Updates

```bash
# Update services
docker-compose pull
docker-compose up -d

# Rebuild services
docker-compose build --no-cache
docker-compose up -d
```

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Check the health endpoint: `curl http://localhost:8000/health`
3. Review this documentation
4. Check the main README.md for additional information
