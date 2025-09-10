-- Cirrus Project Data Pool Schema v2
-- Designed for AI Weather Prediction with Data Protection

-- ==============================================
-- PROTECTED DATA POOL (Real Weather Data Only)
-- ==============================================

-- Grid points table (spatial coordinates)
CREATE TABLE IF NOT EXISTS grid_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    region TEXT NOT NULL, -- 'arctic', 'northern', 'central', 'southern'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(latitude, longitude)
);

-- Real weather data (3D grid: spatial + temporal)
CREATE TABLE IF NOT EXISTS weather_data_3d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grid_point_id INTEGER NOT NULL,
    date_slice DATE NOT NULL, -- 24-hour time slices
    timestamp_utc TIMESTAMP NOT NULL, -- When data was collected
    
    -- Surface weather (GEM API parameters)
    temperature_2m REAL,
    relative_humidity_2m REAL,
    dewpoint_2m REAL,
    apparent_temperature REAL,
    precipitation REAL,
    rain REAL,
    showers REAL,
    snowfall REAL,
    snow_depth REAL,
    weather_code INTEGER,
    pressure_msl REAL,
    surface_pressure REAL,
    cloud_cover REAL,
    cloud_cover_low REAL,
    cloud_cover_mid REAL,
    cloud_cover_high REAL,
    visibility REAL,
    evapotranspiration REAL,
    vapour_pressure_deficit REAL,
    wind_speed_10m REAL,
    wind_speed_100m REAL,
    wind_direction_10m REAL,
    wind_direction_100m REAL,
    wind_gusts_10m REAL,
    
    -- Soil conditions
    soil_temperature_0cm REAL,
    soil_temperature_6cm REAL,
    soil_temperature_18cm REAL,
    soil_temperature_54cm REAL,
    soil_moisture_0_1cm REAL,
    soil_moisture_1_3cm REAL,
    soil_moisture_3_9cm REAL,
    soil_moisture_9_27cm REAL,
    soil_moisture_27_81cm REAL,
    
    -- Atmospheric profiles (multi-level)
    temperature_1000hpa REAL,
    temperature_925hpa REAL,
    temperature_850hpa REAL,
    temperature_700hpa REAL,
    temperature_500hpa REAL,
    temperature_300hpa REAL,
    temperature_250hpa REAL,
    temperature_200hpa REAL,
    temperature_150hpa REAL,
    temperature_100hpa REAL,
    temperature_70hpa REAL,
    temperature_50hpa REAL,
    
    wind_speed_u_1000hpa REAL,
    wind_speed_u_925hpa REAL,
    wind_speed_u_850hpa REAL,
    wind_speed_u_700hpa REAL,
    wind_speed_u_500hpa REAL,
    wind_speed_u_300hpa REAL,
    wind_speed_u_250hpa REAL,
    wind_speed_u_200hpa REAL,
    wind_speed_u_150hpa REAL,
    wind_speed_u_100hpa REAL,
    wind_speed_u_70hpa REAL,
    wind_speed_u_50hpa REAL,
    
    wind_speed_v_1000hpa REAL,
    wind_speed_v_925hpa REAL,
    wind_speed_v_850hpa REAL,
    wind_speed_v_700hpa REAL,
    wind_speed_v_500hpa REAL,
    wind_speed_v_300hpa REAL,
    wind_speed_v_250hpa REAL,
    wind_speed_v_200hpa REAL,
    wind_speed_v_150hpa REAL,
    wind_speed_v_100hpa REAL,
    wind_speed_v_70hpa REAL,
    wind_speed_v_50hpa REAL,
    
    -- Atmospheric stability indices
    cape REAL, -- Convective Available Potential Energy
    cin REAL,  -- Convective Inhibition
    lifted_index REAL,
    showalter_index REAL,
    
    -- Metadata
    data_source TEXT DEFAULT 'gem_api', -- 'gem_api', 'historical_api'
    api_call_id TEXT, -- Track which API call this data came from
    quality_score REAL DEFAULT 1.0, -- Data quality indicator
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (grid_point_id) REFERENCES grid_points(id),
    UNIQUE(grid_point_id, date_slice)
);

-- API call tracking (for monitoring usage)
CREATE TABLE IF NOT EXISTS api_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    api_endpoint TEXT NOT NULL,
    batch_size INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    response_code INTEGER,
    error_message TEXT,
    points_collected INTEGER DEFAULT 0,
    api_key_used TEXT -- Track which API key was used
);

-- ==============================================
-- AI PREDICTION SYSTEM (Separate from Real Data)
-- ==============================================

-- AI model metadata
CREATE TABLE IF NOT EXISTS ai_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL UNIQUE,
    model_version TEXT NOT NULL,
    model_type TEXT NOT NULL, -- 'wildfire_prediction', 'hail_prediction', 'general_weather'
    training_data_start DATE,
    training_data_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE
);

-- AI predictions (separate from real data)
CREATE TABLE IF NOT EXISTS weather_predictions_3d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grid_point_id INTEGER NOT NULL,
    prediction_date DATE NOT NULL, -- Date being predicted
    prediction_timestamp TIMESTAMP NOT NULL, -- When prediction was made
    model_id INTEGER NOT NULL,
    
    -- Predicted weather parameters (same structure as real data)
    temperature_2m REAL,
    relative_humidity_2m REAL,
    dewpoint_2m REAL,
    precipitation REAL,
    wind_speed_10m REAL,
    wind_direction_10m REAL,
    pressure_msl REAL,
    cloud_cover REAL,
    cape REAL,
    cin REAL,
    -- ... (all same parameters as weather_data_3d)
    
    -- Prediction metadata
    confidence_score REAL, -- Model confidence (0-1)
    prediction_horizon_hours INTEGER, -- How far into future (24, 48, 72, etc.)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (grid_point_id) REFERENCES grid_points(id),
    FOREIGN KEY (model_id) REFERENCES ai_models(id),
    UNIQUE(grid_point_id, prediction_date, model_id, prediction_horizon_hours)
);

-- Prediction validation (compare predictions vs reality)
CREATE TABLE IF NOT EXISTS prediction_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    actual_data_id INTEGER NOT NULL,
    validation_date DATE NOT NULL,
    
    -- Accuracy metrics
    temperature_mae REAL, -- Mean Absolute Error
    precipitation_mae REAL,
    wind_speed_mae REAL,
    overall_accuracy REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (prediction_id) REFERENCES weather_predictions_3d(id),
    FOREIGN KEY (actual_data_id) REFERENCES weather_data_3d(id)
);

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Grid points indexes
CREATE INDEX IF NOT EXISTS idx_grid_points_lat_lon ON grid_points(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_grid_points_region ON grid_points(region);

-- Weather data indexes
CREATE INDEX IF NOT EXISTS idx_weather_3d_grid_date ON weather_data_3d(grid_point_id, date_slice);
CREATE INDEX IF NOT EXISTS idx_weather_3d_date ON weather_data_3d(date_slice);
CREATE INDEX IF NOT EXISTS idx_weather_3d_timestamp ON weather_data_3d(timestamp_utc);

-- Predictions indexes
CREATE INDEX IF NOT EXISTS idx_predictions_grid_date ON weather_predictions_3d(grid_point_id, prediction_date);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON weather_predictions_3d(model_id);
CREATE INDEX IF NOT EXISTS idx_predictions_horizon ON weather_predictions_3d(prediction_horizon_hours);

-- API calls indexes
CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON api_calls(call_timestamp);
CREATE INDEX IF NOT EXISTS idx_api_calls_success ON api_calls(success);

-- ==============================================
-- VIEWS FOR EASY DATA ACCESS
-- ==============================================

-- Current weather view (latest data for each grid point)
CREATE VIEW IF NOT EXISTS current_weather AS
SELECT 
    gp.id as grid_point_id,
    gp.latitude,
    gp.longitude,
    gp.region,
    wd.*
FROM grid_points gp
LEFT JOIN weather_data_3d wd ON gp.id = wd.grid_point_id
WHERE wd.date_slice = (
    SELECT MAX(date_slice) 
    FROM weather_data_3d wd2 
    WHERE wd2.grid_point_id = gp.id
);

-- Data coverage view (shows which grid points have data for which dates)
CREATE VIEW IF NOT EXISTS data_coverage AS
SELECT 
    gp.id as grid_point_id,
    gp.latitude,
    gp.longitude,
    gp.region,
    COUNT(wd.date_slice) as data_points,
    MIN(wd.date_slice) as earliest_data,
    MAX(wd.date_slice) as latest_data
FROM grid_points gp
LEFT JOIN weather_data_3d wd ON gp.id = wd.grid_point_id
GROUP BY gp.id, gp.latitude, gp.longitude, gp.region;
