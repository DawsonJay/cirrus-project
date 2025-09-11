# Data Pool Architecture - Cirrus Project

**Last Updated:** January 9, 2025  
**Purpose:** Document the weather data collection and storage system  

## Overview

The Cirrus Project uses a comprehensive data pool system to collect, store, and serve weather data from multiple APIs across a regular grid of 19,008 points covering Canada.

## Grid System

### **Grid Generation**
- **File**: `weather-data-service/app/services/grid_generator.py`
- **Spacing**: 50km between points
- **Coverage**: Canada (41°N to 84°N, 141°W to 52°W)
- **Total Points**: 19,008 coordinate points
- **Regions**: 16 Canadian regions with accurate bounds

### **Coordinate System**
- **Projection**: Mercator projection for map display
- **Reference Points**: 23 calibrated reference points
- **Transformation**: `geoToSvg()` function for pixel coordinates
- **Accuracy**: High precision for map alignment

## API Integration

### **Supported APIs**
1. **Open-Meteo** (Primary)
   - **Rate Limit**: Daily limit (currently exceeded)
   - **Coverage**: Global weather data
   - **Method**: Batch requests (200 points per request)
   - **Status**: Blocked until reset

2. **Environment Canada**
   - **Rate Limit**: None
   - **Coverage**: Canada-specific data
   - **Method**: Individual requests
   - **Status**: Connectivity issues

3. **OpenWeather** (Optional)
   - **Rate Limit**: Per API key
   - **Coverage**: Global weather data
   - **Method**: Individual requests
   - **Status**: Requires API key configuration

4. **Weather Unlocked** (Disabled)
   - **Rate Limit**: Per API key
   - **Coverage**: Global weather data
   - **Method**: Individual requests
   - **Status**: Disabled due to connectivity issues

### **Data Collection Process**
1. **Grid Population**: Generate 19,008 coordinate points
2. **Batch Processing**: Split coordinates into batches of 200
3. **API Requests**: Send batch requests to weather APIs
4. **Data Processing**: Parse and normalize weather data
5. **Database Storage**: Store in SQLite database
6. **Error Handling**: Retry failed requests and log errors

## Database Schema

### **Grid Points Table**
```sql
CREATE TABLE grid_points (
    id INTEGER PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    region_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### **Current Weather Table**
```sql
CREATE TABLE current_weather (
    id INTEGER PRIMARY KEY,
    grid_point_id INTEGER NOT NULL,
    temperature REAL,
    humidity REAL,
    wind_speed REAL,
    wind_direction REAL,
    pressure REAL,
    precipitation REAL,
    cloud_cover REAL,
    visibility REAL,
    weather_code INTEGER,
    weather_description TEXT,
    apparent_temperature REAL,
    dew_point REAL,
    uv_index REAL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grid_point_id) REFERENCES grid_points(id)
);
```

### **Forecast Data Table**
```sql
CREATE TABLE forecast_data (
    id INTEGER PRIMARY KEY,
    grid_point_id INTEGER NOT NULL,
    forecast_date DATE NOT NULL,
    temperature_max REAL,
    temperature_min REAL,
    precipitation REAL,
    wind_speed REAL,
    wind_direction REAL,
    weather_code INTEGER,
    weather_description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grid_point_id) REFERENCES grid_points(id)
);
```

## Data Flow

### **Collection Process**
1. **Grid Generation**: Create 19,008 coordinate points
2. **Batch Creation**: Split into 200-point batches
3. **API Requests**: Send requests to weather APIs
4. **Data Parsing**: Extract weather parameters
5. **Database Insert**: Store in SQLite database
6. **Error Handling**: Log failures and retry

### **Serving Process**
1. **API Request**: Frontend requests weather data
2. **Database Query**: Query grid_points and current_weather
3. **Data Sampling**: Return evenly distributed sample
4. **JSON Response**: Format data for frontend consumption
5. **Caching**: Consider caching for performance

## Current Data Status

### **Coverage Statistics**
- **Total Grid Points**: 19,008
- **Weather Data Points**: 400 (2.1% coverage)
- **Data Regions**: US-Border (12.1%), Ontario (5.6%), Maritime (22.8%)
- **Temperature Range**: 5.1°C to 26.0°C (average 16.1°C)

### **Regional Breakdown**
| Region | Total Points | Data Points | Coverage |
|--------|-------------|-------------|----------|
| NU | 3,817 | 0 | 0.0% |
| NT | 2,520 | 0 | 0.0% |
| Arctic | 2,059 | 0 | 0.0% |
| US-Border | 1,740 | 210 | 12.1% |
| QC | 1,689 | 0 | 0.0% |
| ON | 1,656 | 92 | 5.6% |
| BC | 1,539 | 0 | 0.0% |
| Maritime | 430 | 98 | 22.8% |
| Others | 3,558 | 0 | 0.0% |

## API Endpoints

### **Grid Data**
- **`GET /api/weather/grid`**: Sampled data (default 1000 points)
- **`GET /api/weather/grid/full`**: All 19,008 points
- **`GET /api/weather/stats`**: Coverage statistics

### **Parameters**
- **`sample_size`**: Number of points to return (default 1000)
- **`region`**: Filter by specific region
- **`temperature_min/max`**: Filter by temperature range

## Error Handling

### **API Errors**
- **Rate Limiting**: 429 errors with retry logic
- **Timeout**: Request timeout handling
- **Network**: Connection error recovery
- **Data Validation**: Invalid response handling

### **Database Errors**
- **Foreign Key**: Constraint violation handling
- **Connection**: Database connection recovery
- **Transaction**: Rollback on failure
- **Logging**: Comprehensive error logging

## Performance Considerations

### **Batch Processing**
- **Batch Size**: 200 points per request (optimized)
- **Rate Limiting**: 1 second delay between batches
- **Memory Usage**: Efficient data structures
- **Progress Tracking**: Real-time status updates

### **Database Optimization**
- **Indexes**: Spatial and temporal indexes
- **Query Optimization**: Efficient JOIN operations
- **Connection Pooling**: Reuse database connections
- **Caching**: Consider Redis for frequent queries

## Future Enhancements

### **Data Sources**
- **Additional APIs**: Integrate more weather sources
- **Historical Data**: Add historical weather data
- **Real-time Updates**: Implement live data streaming
- **Data Validation**: Cross-reference multiple sources

### **Performance**
- **Parallel Processing**: Concurrent API requests
- **Caching Layer**: Redis for frequently accessed data
- **CDN Integration**: Distribute data globally
- **Compression**: Reduce data transfer size

### **Monitoring**
- **Health Checks**: API and database monitoring
- **Alerting**: Error and performance alerts
- **Metrics**: Data collection statistics
- **Logging**: Comprehensive audit trail

## Conclusion

The data pool system provides a robust foundation for weather data collection and storage. Current limitations are due to API rate limits rather than system design. Once API limits reset, the system can populate the full 19,008 point dataset and support advanced UI experiments and AI development.

**Key Dependencies**: API rate limits, network connectivity, database performance
**Next Steps**: Wait for API reset, populate full dataset, begin UI experiments
