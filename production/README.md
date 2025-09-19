# Cirrus Wildfire Prediction System - Production

## Overview
Complete wildfire risk prediction system with weather AI, wildfire AI, and interactive frontend map visualization.

## Geographic Coverage
**Southern Canada Only** (below northern territories):
- **Latitude**: 41.75°N to 60.0°N
- **Longitude**: -137.72°W to -52.67°W
- **Excludes**: Yukon, Northwest Territories, Nunavut
- **Focus**: Provinces only (BC, AB, SK, MB, ON, QC, NB, NS, PE, NL)

## System Architecture

### 1. Data Pipeline (`scripts/data_pipeline/`)
- **Raw Weather Data**: Fetch from NOAA API
- **Weather Interpolation**: Convert station data to grid cells
- **Weather AI Evolution**: Evolve optimal AI models using genetic algorithms
- **Weather AI Predictions**: Fill gaps and predict future weather
- **Wildfire AI Predictions**: Generate daily risk maps

**Note**: Temporary scripts go in `scripts/temp/` and should be deleted after use.

### 2. Weather AI Framework (`weather_ai/`)
- **Evolution Engine**: Genetic algorithm for optimal model discovery
- **Feature Generation**: Evolves temporal windows, derived features, seasonal patterns
- **Model Training**: XGBoost with evolved parameters
- **Production API**: Clean interface for weather predictions

### 3. AI Models (`scripts/ai_models/`)
- **Wildfire AI**: Predicts fire probability and risk levels
- **Model Training**: Evolutionary optimization for best performance

### 4. Frontend (`frontend/`)
- **Interactive Map**: SVG-based wildfire risk visualization
- **Time Slider**: Daily increments for full year ahead
- **Real-time Updates**: Live data from prediction database

### 5. Data Storage (`data/`)
- **Raw Weather**: Station observations from NOAA
- **Interpolated Weather**: Grid cell weather data
- **Predictions**: Daily wildfire risk predictions
- **Models**: Trained AI model files

## Complete Workflow

1. **Stage 1: Historical Data Collection** (`stage_1_collect_historical_data.py`)
   - Download and filter NOAA GHCN-Daily historical weather data
   - Spatial filtering for Southern Canada (41.75°N to 60.0°N)
   - Temporal filtering for 2022-2025
   - Output: Raw weather CSV files

2. **Stage 2: Wildfire Data Collection** (`stage_2_collect_wildfire_data.py`)
   - Download and filter Canadian wildfire data
   - Spatial filtering for Southern Canada
   - Temporal filtering for 2022-2025
   - Output: Wildfire CSV files

3. **Stage 3: Data Validation** (`stage_3_validate_raw_data.py`)
   - Validate weather and wildfire data quality
   - Remove corrupted records
   - Output wide-format CSV files
   - Output: Validated data CSV files

4. **Stage 4: Raw Database Creation** (`stage_4_create_raw_weather_db.py`)
   - Create optimized raw weather database
   - Wide-format weather data (no pivot needed)
   - Pre-computed station distances and neighbors
   - Enhanced features for AI training
   - Output: `raw_weather_db.db`

5. **Stage 5: Interpolated Grid Creation** (`stage_5_create_interpolated_grid_db.py`)
   - Create curvature-adjusted 10km grid
   - Adaptive processing for different hardware
   - Memory-safe parallel processing
   - Weather interpolation with real data
   - Smart wildfire assignment
   - Output: `interpolated_grid_db.db`

6. **Stage 6: AI Training** (`stage_6_evolution_weather_ai.py`)
   - Evolutionary weather AI training
   - Feature optimization and model selection
   - Multi-objective optimization
   - Output: Trained AI models

## Quick Start

### Test Weather AI System (Quick Test)
```bash
cd scripts/data_pipeline
python3 stage_6_evolution_weather_ai.py --test
```

### Run Full Weather AI Evolution
```bash
cd scripts/data_pipeline
python3 stage_6_evolution_weather_ai.py
```

### Customize Evolution Parameters
```bash
cd scripts/data_pipeline
python3 stage_6_evolution_weather_ai.py --help
python3 stage_6_evolution_weather_ai.py --population 30 --generations 100
```

### Run Complete Data Pipeline
```bash
cd scripts/data_pipeline
python3 stage_1_collect_historical_data.py
python3 stage_2_collect_wildfire_data.py
python3 stage_3_validate_raw_data.py
python3 stage_4_create_raw_weather_db.py
python3 stage_5_create_interpolated_grid_db.py
python3 stage_6_evolution_weather_ai.py
```

## Key Features
- **Real-time Updates**: Weekly NOAA data refresh
- **AI-Powered**: Machine learning for weather and fire prediction
- **Interactive**: User-friendly map interface
- **Production-Ready**: Robust error handling and logging
- **Scalable**: Handles large datasets efficiently

## Getting Started
1. Set up environment and dependencies
2. Run data pipeline to collect and process weather data
3. Train AI models on historical data
4. Start frontend server for visualization
5. Set up automated data updates

## File Structure
```
production/
├── data/                    # All databases and data files
├── models/                  # Trained AI model files
├── scripts/
│   ├── data_pipeline/      # Data collection and processing
│   ├── ai_models/          # AI training and prediction
│   └── frontend/           # Frontend build and deployment
├── frontend/               # Frontend source code
└── logs/                   # System logs
```
