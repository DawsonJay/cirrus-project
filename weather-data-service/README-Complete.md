# Weather Data Service - Complete Docker Setup

This document provides a complete guide for running the Weather Data Service using Docker with database initialization.

## 🚀 Quick Start

### 1. Prerequisites

- Docker installed and running
- NOAA API token (get from https://www.ncdc.noaa.gov/cdo-web/token)

### 2. Set Environment Variables

```bash
export NOAA_CDO_TOKEN=your_noaa_token_here
```

### 3. Run the Service

```bash
# Build the image
sudo docker build -t weather-data-service .

# Run with database initialization
sudo docker run -d -p 8000:8000 \
  -e NOAA_CDO_TOKEN=$NOAA_CDO_TOKEN \
  -v $(pwd)/data:/app/data \
  --name weather-data-service \
  weather-data-service
```

### 4. Test the Service

```bash
# Check health
curl http://localhost:8000/health

# List stations
curl http://localhost:8000/stations

# Get weather data summary
curl http://localhost:8000/weather-data

# Trigger data collection
curl -X POST http://localhost:8000/collect/year \
  -H "Content-Type: application/json" \
  -d '{"year": 2024, "limit": 5}'
```

## 📊 What's Included

### Database
- **8,912 Canadian weather stations** with geographic coverage across Canada
- **2,831+ weather records** from historical data collection
- **Date range**: 2010-2024
- **Geographic coverage**: 42.01°N to 82.52°N, 141.00°W to 52.67°W

### API Endpoints
- `GET /health` - Health check
- `GET /stations` - List all stations
- `GET /stations/{station_id}` - Get station details
- `GET /weather-data` - Get weather data summary
- `POST /collect/year` - Trigger collection for specific year
- `POST /collect/years` - Trigger collection for multiple years
- `GET /status` - Get collection status
- `GET /docs` - Interactive API documentation

### Features
- **Automatic database initialization** on first run
- **Persistent data storage** via Docker volumes
- **Rate limiting** and error handling for NOAA API
- **Background data collection** with status tracking
- **Comprehensive logging** and monitoring

## 🔧 Advanced Usage

### Manual Database Initialization

```bash
# Initialize database only
sudo docker run --rm \
  -v $(pwd)/data:/app/data \
  -e NOAA_CDO_TOKEN=$NOAA_CDO_TOKEN \
  weather-data-service \
  python3 init_database.py
```

### Run Data Collection

```bash
# Run daily collection
sudo docker run --rm \
  -v $(pwd)/data:/app/data \
  -e NOAA_CDO_TOKEN=$NOAA_CDO_TOKEN \
  weather-data-service \
  python3 main.py

# Run test collection (limited stations)
sudo docker run --rm \
  -v $(pwd)/data:/app/data \
  -e NOAA_CDO_TOKEN=$NOAA_CDO_TOKEN \
  weather-data-service \
  python3 main.py --test
```

### View Logs

```bash
# View container logs
sudo docker logs weather-data-service

# Follow logs in real-time
sudo docker logs -f weather-data-service
```

## 📁 Data Storage

### Database Location
- **Host**: `./data/weather_pool.db`
- **Container**: `/app/data/weather_pool.db`

### Tables
- `all_canadian_stations` - Weather station metadata
- `daily_weather_data` - Daily weather observations

### Backup
```bash
# Backup database
cp data/weather_pool.db data/weather_pool_backup_$(date +%Y%m%d).db

# Restore database
cp data/weather_pool_backup_20240101.db data/weather_pool.db
```

## 🔍 Monitoring

### Health Checks
```bash
# Check service health
curl http://localhost:8000/health

# Check collection status
curl http://localhost:8000/status

# Check database stats
curl http://localhost:8000/weather-data
```

### Logs
```bash
# View all logs
sudo docker logs weather-data-service

# View specific log files
sudo docker exec weather-data-service cat /app/logs/cron.log
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   
   # Kill the process
   sudo kill -9 <PID>
   ```

2. **Database not found**
   ```bash
   # Check if database exists
   ls -la data/
   
   # Reinitialize database
   sudo docker run --rm \
     -v $(pwd)/data:/app/data \
     -e NOAA_CDO_TOKEN=$NOAA_CDO_TOKEN \
     weather-data-service \
     python3 init_database.py
   ```

3. **NOAA API errors**
   ```bash
   # Check token
   echo $NOAA_CDO_TOKEN
   
   # Test API directly
   curl -H "token: $NOAA_CDO_TOKEN" \
     "https://www.ncei.noaa.gov/cdo-web/api/v2/stations?limit=1"
   ```

### Debug Mode

```bash
# Run in debug mode
sudo docker run --rm -it \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e NOAA_CDO_TOKEN=$NOAA_CDO_TOKEN \
  weather-data-service \
  bash

# Inside container
python3 api.py --debug
```

## 📈 Performance

### Resource Usage
- **Memory**: ~200MB base, +50MB per active collection
- **CPU**: Low during idle, high during data collection
- **Disk**: ~50MB for database, +1MB per 1000 weather records

### Scaling
- **API Service**: Can run multiple instances behind load balancer
- **Data Collection**: Should run as single instance to avoid API conflicts
- **Database**: SQLite supports concurrent reads, single writer

## 🔒 Security

### Environment Variables
- Store `NOAA_CDO_TOKEN` securely
- Use Docker secrets in production
- Rotate API tokens regularly

### Network
- Expose only necessary ports (8000)
- Use reverse proxy for HTTPS
- Implement authentication for production

## 📚 API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation with:
- Request/response schemas
- Example requests
- Try-it-out functionality

## 🎯 Next Steps

1. **Production Deployment**
   - Set up reverse proxy (nginx)
   - Configure SSL certificates
   - Implement monitoring and alerting

2. **Data Collection**
   - Set up automated daily collection
   - Configure cron jobs or Kubernetes CronJobs
   - Monitor collection success rates

3. **Data Analysis**
   - Connect to data visualization tools
   - Build ML models for weather prediction
   - Create dashboards for monitoring

## 📞 Support

For issues or questions:
1. Check the logs: `sudo docker logs weather-data-service`
2. Check the health endpoint: `curl http://localhost:8000/health`
3. Review this documentation
4. Check the main README.md for additional information
