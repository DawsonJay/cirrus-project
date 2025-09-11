# Weather Data Service

A comprehensive weather data collection and API service for Canadian weather stations, built for the Cirrus Project - an AI system for predicting dangerous weather events across Canada.

## Features

- **8,912+ Canadian Weather Stations** - Complete database of active weather stations
- **Automated Data Collection** - Daily collection from NOAA Climate Data Online API
- **REST API** - FastAPI-based API for data access and collection control
- **PostgreSQL Database** - Scalable cloud database for weather data storage
- **Docker Support** - Containerized deployment for any platform
- **Health Monitoring** - Comprehensive health checks and logging
- **Rate Limiting** - Robust API retry logic with exponential backoff

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/weather-data-service.git
   cd weather-data-service
   ```

2. **Set up environment**
   ```bash
   cp env.template .env
   # Edit .env and add your NOAA_CDO_TOKEN
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python3 init_database.py
   ```

5. **Run the service**
   ```bash
   python3 api.py
   ```

### Docker Deployment

1. **Build and run**
   ```bash
   docker build -t weather-data-service .
   docker run -p 8000:8000 -e NOAA_CDO_TOKEN=your_token weather-data-service
   ```

2. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## API Endpoints

- `GET /health` - Service health check
- `GET /stations` - List all weather stations
- `GET /stations/{station_id}` - Get specific station details
- `GET /weather-data` - Get weather data summary
- `POST /collect/year` - Trigger manual data collection
- `GET /status` - Get collection status
- `GET /docs` - Interactive API documentation

## Environment Variables

- `NOAA_CDO_TOKEN` - NOAA Climate Data Online API token (required)
- `DATABASE_URL` - PostgreSQL connection string (for cloud deployment)
- `DATABASE_PATH` - SQLite database path (for local development)
- `ENVIRONMENT` - Environment (development/production)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)

## Data Collection

The service automatically collects weather data from:
- **Daily Summaries (GHCND)** - Temperature, precipitation, wind, pressure
- **Hourly Precipitation (PRECIP_HLY)** - Detailed precipitation data
- **Daily Normals (NORMAL_DLY)** - Historical averages and extremes

## Deployment

### Railway (Recommended)

1. **Connect to Railway**
   - Go to [railway.app](https://railway.app)
   - Connect your GitHub account
   - Deploy from this repository

2. **Add PostgreSQL database**
   - Add PostgreSQL service in Railway dashboard
   - Set `DATABASE_URL` environment variable

3. **Set environment variables**
   - `NOAA_CDO_TOKEN` - Your NOAA API token
   - `ENVIRONMENT=production`

### Other Platforms

- **Docker** - Use the included Dockerfile
- **Heroku** - Use the Procfile
- **AWS/GCP** - Use Docker containers

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   NOAA API      │───▶│  Weather Service │───▶│   PostgreSQL    │
│   (Data Source) │    │   (Collection)   │    │   (Storage)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   FastAPI        │
                       │   (REST API)     │
                       └──────────────────┘
```

## Development

### Project Structure

```
weather-data-service/
├── api.py                 # FastAPI application
├── collection.py          # Data collection logic
├── station.py            # Single station data retrieval
├── stations_database.py  # Station database operations
├── weather_database.py   # Weather data operations
├── main.py              # Daily collection entry point
├── init_database.py     # Database initialization
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── railway.json        # Railway deployment config
└── README.md           # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Cirrus Project for Canadian weather prediction.

## Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the logs for error details
- Open an issue on GitHub

---

**Built for the Cirrus Project - AI Weather Prediction System**