-- Weather Data Pool Database Schema
-- SQLite database for storing grid-based weather data

-- Grid points table - stores all coordinate points in our grid
CREATE TABLE IF NOT EXISTS grid_points (
    id INTEGER PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    region_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Current weather data table
CREATE TABLE IF NOT EXISTS current_weather (
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

-- Forecast data table
CREATE TABLE IF NOT EXISTS forecast_data (
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

-- Weather alerts table
CREATE TABLE IF NOT EXISTS weather_alerts (
    id INTEGER PRIMARY KEY,
    alert_id TEXT UNIQUE,
    title TEXT,
    description TEXT,
    severity TEXT,
    urgency TEXT,
    certainty TEXT,
    event_type TEXT,
    start_time DATETIME,
    end_time DATETIME,
    latitude REAL,
    longitude REAL,
    region_name TEXT,
    source TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Validation data table (for other API sources)
CREATE TABLE IF NOT EXISTS validation_data (
    id INTEGER PRIMARY KEY,
    location_name TEXT,
    latitude REAL,
    longitude REAL,
    temperature REAL,
    humidity REAL,
    wind_speed REAL,
    pressure REAL,
    source TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Update log table
CREATE TABLE IF NOT EXISTS update_log (
    id INTEGER PRIMARY KEY,
    update_type TEXT NOT NULL, -- 'current_weather', 'forecast', 'alerts'
    grid_points_updated INTEGER,
    success BOOLEAN,
    error_message TEXT,
    duration_seconds REAL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_grid_spatial ON grid_points(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_current_weather_grid ON current_weather(grid_point_id);
CREATE INDEX IF NOT EXISTS idx_current_weather_time ON current_weather(updated_at);
CREATE INDEX IF NOT EXISTS idx_forecast_grid ON forecast_data(grid_point_id);
CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_data(forecast_date);
CREATE INDEX IF NOT EXISTS idx_alerts_location ON weather_alerts(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_alerts_time ON weather_alerts(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_validation_location ON validation_data(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_validation_time ON validation_data(updated_at);
