# Weather Data Collection - Main Service

This document describes the `main.py` service for daily weather data collection.

## Overview

The `main.py` script is the main entry point for the weather data collection system. It runs daily collection for the current year and can be scheduled as a cron job or systemd service.

## Features

- **Daily Collection**: Automatically collects data for the current year
- **Robust Error Handling**: Includes retry logic with exponential backoff
- **Logging**: Comprehensive logging to files for monitoring
- **Test Mode**: Test collection with limited stations
- **Environment Validation**: Checks for required environment variables

## Usage

### Basic Usage

```bash
# Run daily collection for current year
python3 main.py

# Run test collection (5 stations)
python3 main.py --test

# Show help
python3 main.py --help
```

### Environment Variables

Required:
- `NOAA_CDO_TOKEN`: NOAA API token for data access

Optional:
- `DATABASE_PATH`: Path to SQLite database (default: `data/weather_pool.db`)
- `ENVIRONMENT`: Environment setting (development/production)

### Example Setup

```bash
# Set environment variables
export NOAA_CDO_TOKEN=your_token_here
export DATABASE_PATH=/path/to/weather_pool.db
export ENVIRONMENT=production

# Test the collection
python3 main.py --test

# Run full collection
python3 main.py
```

## Scheduling

### Option 1: Cron Job

Use the provided setup script:

```bash
# Make setup script executable
chmod +x setup_cron.sh

# Run setup (will prompt for confirmation)
./setup_cron.sh
```

Manual cron setup:
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2:00 AM
0 2 * * * cd /path/to/backend && python3 main.py >> logs/cron.log 2>&1
```

### Option 2: Systemd Service

For more robust scheduling on Linux systems:

```bash
# Copy service files to systemd directory
sudo cp weather-collection.service /etc/systemd/system/
sudo cp weather-collection.timer /etc/systemd/system/

# Edit the service file to set your token and paths
sudo nano /etc/systemd/system/weather-collection.service

# Reload systemd and enable the timer
sudo systemctl daemon-reload
sudo systemctl enable weather-collection.timer
sudo systemctl start weather-collection.timer

# Check status
sudo systemctl status weather-collection.timer
sudo systemctl list-timers weather-collection.timer
```

## Logging

### Log Files

- `logs/daily_collection_YYYY.log`: Daily collection results
- `logs/cron.log`: Cron job output (if using cron)
- `logs/service.log`: Systemd service output (if using systemd)

### Log Format

Success:
```
2025-09-10 23:55:47 - SUCCESS - Year 2025 - Stations: 100 (95 successful, 5 failed) - Records: 50000 collected, 50000 stored - Duration: 120.5s
```

Failure:
```
2025-09-10 23:55:47 - FAILED - Year 2025 - Error: API rate limit exceeded
```

## Monitoring

### Check Collection Status

```bash
# View recent logs
tail -f logs/daily_collection_2025.log

# Check cron job status
tail -f logs/cron.log

# Check systemd service status
sudo systemctl status weather-collection.service
sudo journalctl -u weather-collection.service -f
```

### Health Checks

```bash
# Test collection
python3 main.py --test

# Check database
sqlite3 data/weather_pool.db "SELECT COUNT(*) FROM daily_weather_data WHERE strftime('%Y', date) = '2025';"

# Check API status
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

1. **Missing NOAA Token**
   ```
   Error: NOAA_CDO_TOKEN environment variable is required
   ```
   Solution: Set the token with `export NOAA_CDO_TOKEN=your_token_here`

2. **Database Permission Issues**
   ```
   Error: Permission denied writing to database
   ```
   Solution: Check file permissions and ensure the user has write access

3. **API Rate Limits**
   ```
   Rate limit exceeded (429), retrying in 2.1s
   ```
   Solution: The system will automatically retry with exponential backoff

4. **Connection Timeouts**
   ```
   Request timeout, retrying in 30s
   ```
   Solution: The system will automatically retry with increasing delays

### Debug Mode

For debugging, you can run with verbose output:

```bash
# Set debug environment
export ENVIRONMENT=development

# Run with test mode
python3 main.py --test
```

## Performance

### Expected Performance

- **Test Mode (5 stations)**: ~1-2 minutes
- **Full Collection (8,911 stations)**: ~20-30 hours
- **Daily Collection (current year)**: ~2-4 hours (depending on data availability)

### Resource Usage

- **Memory**: ~100-200 MB during collection
- **Disk**: ~1-2 GB per year of data
- **Network**: Respects NOAA rate limits (5 req/s, 10k/day)

## Security

### Best Practices

1. **Environment Variables**: Store sensitive data in environment variables, not in code
2. **File Permissions**: Ensure log files and database have appropriate permissions
3. **Network Security**: Use HTTPS for API calls (already implemented)
4. **Token Security**: Rotate NOAA API tokens regularly

### Example Secure Setup

```bash
# Create a secure environment file
cat > .env << EOF
NOAA_CDO_TOKEN=your_secure_token_here
DATABASE_PATH=/secure/path/to/weather_pool.db
ENVIRONMENT=production
EOF

# Source the environment
source .env

# Run collection
python3 main.py
```

## Maintenance

### Regular Tasks

1. **Monitor Logs**: Check daily for errors or issues
2. **Database Maintenance**: Periodically vacuum and optimize the database
3. **Token Rotation**: Update NOAA API tokens as needed
4. **Disk Space**: Monitor disk usage for logs and database

### Database Maintenance

```bash
# Optimize database
sqlite3 data/weather_pool.db "VACUUM;"

# Check database size
du -h data/weather_pool.db

# Check record counts
sqlite3 data/weather_pool.db "SELECT strftime('%Y', date) as year, COUNT(*) as records FROM daily_weather_data GROUP BY year ORDER BY year;"
```

## Support

For issues or questions:

1. Check the logs for error messages
2. Verify environment variables are set correctly
3. Test with `--test` mode first
4. Check NOAA API status and rate limits
5. Review the main collection documentation
