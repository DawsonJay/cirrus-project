# Weather Data Service - Production Deployment

This document provides complete instructions for deploying the Weather Data Service in production for background data collection.

## 🚀 **Quick Start**

### 1. Prerequisites
- Docker installed and running
- NOAA API token (get from https://www.ncdc.noaa.gov/cdo-web/token)

### 2. Deploy the Service
```bash
# Set your NOAA API token
echo "NOAA_CDO_TOKEN=your_actual_token_here" > .env

# Deploy the service
./deploy-simple.sh
```

### 3. Verify Deployment
```bash
# Check service health
curl http://localhost:8000/health

# View service status
./manage.sh status

# Check data collection
curl http://localhost:8000/status
```

## 📊 **What's Running**

### Services Deployed
- **`weather-data-api`** - REST API service (port 8000)
- **`weather-data-collector`** - Daily data collection (cron at 2:00 AM)

### Data Storage
- **Database**: `./data/weather_pool.db` (8,912+ Canadian weather stations)
- **Logs**: `./logs/` (service and collection logs)

### Automated Collection
- **Schedule**: Daily at 2:00 AM
- **Scope**: All Canadian weather stations
- **Data**: Daily weather summaries, precipitation, normals

## 🔧 **Management Commands**

### Service Management
```bash
# View all commands
./manage.sh

# Start services
./manage.sh start

# Stop services
./manage.sh stop

# Restart services
./manage.sh restart

# View logs
./manage.sh logs

# Check health
./manage.sh health
```

### Data Collection
```bash
# Trigger manual collection
./manage.sh collect

# View collection status
curl http://localhost:8000/status

# View weather data stats
./manage.sh stats

# List stations
./manage.sh stations
```

### Monitoring
```bash
# View service status
./manage.sh status

# View API logs
sudo docker logs -f weather-data-api

# View collector logs
sudo docker logs -f weather-data-collector

# View cron logs
sudo docker exec weather-data-collector cat /app/logs/cron.log
```

## 📈 **Background Data Collection**

### How It Works
1. **Daily Collection**: Runs automatically at 2:00 AM
2. **Station Processing**: Collects data from all 8,912+ Canadian stations
3. **Data Storage**: Stores daily weather records in SQLite database
4. **Error Handling**: Robust retry logic with exponential backoff
5. **Logging**: Comprehensive logging for monitoring and debugging

### Collection Process
1. **Station Discovery**: Loads all Canadian weather stations
2. **Data Retrieval**: Fetches daily weather data from NOAA API
3. **Data Processing**: Converts and validates weather parameters
4. **Database Storage**: Stores processed data with upsert operations
5. **Active Periods**: Updates station activity tracking

### Data Types Collected
- **Daily Summaries (GHCND)**: Temperature, precipitation, wind, pressure
- **Hourly Precipitation (PRECIP_HLY)**: Detailed precipitation data
- **Daily Normals (NORMAL_DLY)**: Historical averages and extremes

## 🔍 **Monitoring & Troubleshooting**

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Service status
./manage.sh status

# Collection status
curl http://localhost:8000/status
```

### Logs
```bash
# All service logs
./manage.sh logs

# API service logs
sudo docker logs weather-data-api

# Collector service logs
sudo docker logs weather-data-collector

# Cron job logs
sudo docker exec weather-data-collector cat /app/logs/cron.log
```

### Common Issues

#### Service Won't Start
```bash
# Check if port 8000 is in use
sudo lsof -i :8000

# Kill process using port 8000
sudo kill -9 <PID>

# Restart services
./manage.sh restart
```

#### Database Issues
```bash
# Check database exists
ls -la data/weather_pool.db

# Reinitialize database
sudo docker run --rm \
  -v $(pwd)/data:/app/data \
  -e NOAA_CDO_TOKEN=$NOAA_CDO_TOKEN \
  weather-data-service \
  python3 init_database.py
```

#### Collection Not Working
```bash
# Check collector status
sudo docker logs weather-data-collector

# Test manual collection
./manage.sh collect

# Check API token
echo $NOAA_CDO_TOKEN
```

## 📊 **Data Access**

### API Endpoints
- `GET /health` - Service health check
- `GET /stations` - List all weather stations
- `GET /stations/{station_id}` - Get specific station details
- `GET /weather-data` - Get weather data summary
- `POST /collect/year` - Trigger manual data collection
- `GET /status` - Get collection status
- `GET /docs` - Interactive API documentation

### Database Access
```bash
# Access database directly
sudo docker exec -it weather-data-api sqlite3 /app/data/weather_pool.db

# Query stations
sudo docker exec weather-data-api sqlite3 /app/data/weather_pool.db \
  "SELECT COUNT(*) FROM all_canadian_stations;"

# Query weather data
sudo docker exec weather-data-api sqlite3 /app/data/weather_pool.db \
  "SELECT COUNT(*) FROM daily_weather_data;"
```

## 🔒 **Security & Maintenance**

### Environment Variables
- Store `NOAA_CDO_TOKEN` securely
- Use Docker secrets in production
- Rotate API tokens regularly

### Backups
```bash
# Create database backup
./manage.sh backup

# Restore from backup
cp data/weather_pool_backup_YYYYMMDD_HHMMSS.db data/weather_pool.db
```

### Updates
```bash
# Update services
./manage.sh update

# Or manually
sudo docker-compose -f docker-compose.prod.yml pull
sudo docker-compose -f docker-compose.prod.yml build
sudo docker-compose -f docker-compose.prod.yml up -d
```

## 📈 **Performance & Scaling**

### Resource Usage
- **Memory**: ~200MB base, +50MB per active collection
- **CPU**: Low during idle, high during data collection
- **Disk**: ~50MB for database, +1MB per 1000 weather records

### Scaling Options
- **API Service**: Can run multiple instances behind load balancer
- **Data Collection**: Should run as single instance to avoid API conflicts
- **Database**: SQLite supports concurrent reads, single writer

## 🎯 **Next Steps**

### Immediate
1. **Monitor Collection**: Check logs and collection status
2. **Verify Data**: Ensure data is being collected and stored
3. **Set Up Alerts**: Configure monitoring for service health

### Short-term
1. **Data Analysis**: Build tools to analyze collected data
2. **Dashboard**: Create web interface for monitoring
3. **API Integration**: Connect with other applications

### Long-term
1. **ML Models**: Develop weather prediction algorithms
2. **Alerting System**: Implement dangerous weather detection
3. **Data Pipeline**: Build ETL processes for data processing

## 📞 **Support**

### Getting Help
1. Check logs: `./manage.sh logs`
2. Check health: `./manage.sh health`
3. Review this documentation
4. Check the main README.md

### Useful Commands
```bash
# Quick status check
./manage.sh status && ./manage.sh health

# View recent logs
sudo docker logs --tail 50 weather-data-api

# Test data collection
./manage.sh collect && sleep 10 && ./manage.sh stats
```

---

**🎉 Your Weather Data Service is now running in the background and collecting data automatically!**

The system will:
- ✅ Collect data daily at 2:00 AM
- ✅ Store data in persistent database
- ✅ Handle errors and retries automatically
- ✅ Provide API access to collected data
- ✅ Log all activities for monitoring

You can now work on other things while the system gathers weather data in the background!
