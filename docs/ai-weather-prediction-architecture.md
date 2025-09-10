# AI Weather Prediction Architecture

## Overview

The Cirrus Project is building an AI system to predict dangerous weather events across Canada, specifically focusing on wildfires and severe storms (hail, tornadoes, etc.). This document outlines the data architecture and collection strategy for training the predictive AI.

## 3D Weather Data Grid

### Concept
We're building a 3D data grid with three dimensions:
- **X, Y**: Geographic coordinates (10,000 grid points across Canada)
- **Z**: Time dimension (daily weather data slices)

### Grid Specifications
- **Spatial Coverage**: 10,000 points across Canada (~10 million km²)
- **Point Density**: 1 point per 1,000 km²
- **Grid Spacing**: ~32km between points
- **Time Resolution**: 24-hour intervals (daily slices)

### Data Collection Strategy
- **Current Data**: Collect comprehensive weather data for all 10,000 points daily
- **Historical Backfill**: 1 year of historical data (365 daily slices)
- **Continuous Updates**: Add new daily slices indefinitely
- **API Usage**: ~18,250 API calls for 1-year backfill (well within 1M/month limit)

## Weather Data Parameters

### Source: GEM API (Canadian Meteorological Center)
The GEM API provides comprehensive weather data optimized for North America, including:

#### Basic Weather Parameters
- `temperature_2m`, `relative_humidity_2m`, `dewpoint_2m`, `apparent_temperature`
- `precipitation`, `rain`, `showers`, `snowfall`, `weather_code`
- `pressure_msl`, `surface_pressure`
- `cloud_cover_total`, `cloud_cover_low`, `cloud_cover_mid`, `cloud_cover_high`

#### Wind Data (Multiple Altitudes)
- `wind_speed_10m`, `wind_speed_40m`, `wind_speed_80m`, `wind_speed_120m`
- `wind_direction_10m`, `wind_direction_40m`, `wind_direction_80m`, `wind_direction_120m`
- `wind_gusts_10m`

#### Atmospheric Profiles
- `temperature_40m`, `temperature_80m`, `temperature_120m`
- Pressure level data (1000hPa down to 10hPa)
- `geopotential_height` at each pressure level

#### Critical for Dangerous Weather Prediction
- **CAPE** (Convective Available Potential Energy) - Essential for severe storm prediction
- `soil_temperature_0_10cm`, `soil_moisture_0_10cm` - Critical for fire risk assessment
- `wet_bulb_temperature_2m` - Important for heat stress and fire weather
- `is_day`, `sunshine_duration` - Fire risk factors

#### Solar Radiation
- `shortwave_radiation`, `direct_radiation`, `diffuse_radiation`
- `direct_normal_irradiance`, `global_tilted_irradiance`

## AI Training Approach

### Input Data
- Weather conditions across the 3D grid for the past N days
- All comprehensive GEM parameters for each grid point
- Spatial-temporal relationships between weather patterns

### Output Predictions
- Probability of dangerous weather events in the next 1-7 days
- Specific predictions for:
  - Wildfire risk and potential fire spread
  - Severe storm development (hail, tornadoes)
  - Flash flood risk
  - Extreme temperature events

### Training Data
- Historical sequences where we know what dangerous weather occurred
- Weather patterns that preceded major fires and storms
- Seasonal variations and year-to-year climate patterns

## Data Storage Structure

### Database Schema
```sql
weather_data_3d (
    latitude REAL,
    longitude REAL,
    timestamp DATE,
    temperature_2m REAL,
    relative_humidity_2m REAL,
    dewpoint_2m REAL,
    apparent_temperature REAL,
    precipitation REAL,
    rain REAL,
    showers REAL,
    snowfall REAL,
    weather_code INTEGER,
    pressure_msl REAL,
    surface_pressure REAL,
    cloud_cover_total REAL,
    cloud_cover_low REAL,
    cloud_cover_mid REAL,
    cloud_cover_high REAL,
    wind_speed_10m REAL,
    wind_speed_40m REAL,
    wind_speed_80m REAL,
    wind_speed_120m REAL,
    wind_direction_10m REAL,
    wind_direction_40m REAL,
    wind_direction_80m REAL,
    wind_direction_120m REAL,
    wind_gusts_10m REAL,
    temperature_40m REAL,
    temperature_80m REAL,
    temperature_120m REAL,
    soil_temperature_0_10cm REAL,
    soil_moisture_0_10cm REAL,
    cape REAL,
    wet_bulb_temperature_2m REAL,
    is_day BOOLEAN,
    sunshine_duration REAL,
    shortwave_radiation REAL,
    direct_radiation REAL,
    diffuse_radiation REAL,
    direct_normal_irradiance REAL,
    global_tilted_irradiance REAL,
    -- Additional pressure level data as needed
    PRIMARY KEY (latitude, longitude, timestamp)
)
```

## Implementation Phases

### Phase 1: Current Data Collection
- Update API client to collect all GEM parameters
- Implement daily data collection for all 10,000 points
- Establish continuous update system

### Phase 2: Historical Backfill
- Collect 1 year of historical data (365 daily slices)
- Total: ~3.65M data points
- API usage: ~18,250 calls (within monthly limits)

### Phase 3: AI Development
- Build 3D spatial-temporal AI model
- Train on historical weather sequences
- Implement dangerous weather prediction algorithms

### Phase 4: Continuous Operation
- Daily updates to maintain current data
- Model retraining with new data
- Performance monitoring and improvement

## Coverage Analysis

### Spatial Coverage
- **Canada's area**: ~10 million km²
- **Point density**: 1 point per 1,000 km²
- **Grid spacing**: ~32km between points
- **Comparison**: Similar to Environment Canada's regional models (10-25km spacing)

### Temporal Coverage
- **Daily resolution**: Sufficient for weather pattern evolution
- **1-year history**: Captures full seasonal cycles
- **Continuous updates**: Maintains current conditions

### AI Training Sufficiency
- **Pattern Recognition**: 10,000 points excellent for learning weather patterns
- **Spatial Relationships**: Sufficient to understand regional weather movement
- **Temporal Evolution**: 24-hour slices perfect for daily weather progression
- **Dangerous Weather**: Can identify patterns leading to fires/storms

## API Strategy

### Open-Meteo GEM API
- **Base URL**: `https://customer-api.open-meteo.com/v1/gem`
- **Authentication**: API key required for paid tier
- **Rate Limits**: 1M calls/month (sufficient for our needs)
- **Batch Requests**: Up to 200 points per request (payload limit)

### Data Collection Efficiency
- **Single API Call**: All parameters in one request per location
- **No Additional Cost**: Comprehensive data doesn't increase API usage
- **Optimal Coverage**: GEM API specifically optimized for North America

## Future Considerations

### Scalability
- **Point Density**: Can increase from 10,000 to 20,000+ points if needed
- **Time Resolution**: Could move to 12-hour or 6-hour intervals
- **Historical Depth**: Can backfill additional years as needed

### AI Model Evolution
- **Deep Learning**: 3D convolutional neural networks for spatial-temporal data
- **Ensemble Methods**: Multiple models for different weather types
- **Real-time Updates**: Continuous model retraining with new data

### Integration
- **Frontend Visualization**: Real-time dangerous weather risk maps
- **Alert System**: Automated warnings for high-risk areas
- **API Endpoints**: External access to predictions and risk assessments

---

*This architecture provides a solid foundation for building a comprehensive AI weather prediction system focused on dangerous weather events across Canada.*
