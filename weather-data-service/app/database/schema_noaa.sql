-- NOAA Weather Station Database Schema
-- Designed for irregular weather station data from NOAA/Environment Canada
-- Replaces the 3D grid-based schema with station-based approach

-- Weather stations table (irregular spatial points)
CREATE TABLE weather_stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id VARCHAR(50) UNIQUE NOT NULL,  -- NOAA/EC station identifier
    name VARCHAR(255) NOT NULL,              -- Human-readable station name
    latitude REAL NOT NULL,                  -- Station latitude
    longitude REAL NOT NULL,                 -- Station longitude
    elevation REAL,                          -- Station elevation in meters
    province VARCHAR(50),                    -- Canadian province or US state
    country VARCHAR(50) DEFAULT 'CA',        -- Country code
    source VARCHAR(50) NOT NULL,             -- 'environment_canada', 'us_weather'
    station_type VARCHAR(50),                -- 'airport', 'weather_station', etc.
    data_start_date DATE,                    -- When this station started collecting data
    data_end_date DATE,                      -- When this station stopped collecting data (if applicable)
    is_active BOOLEAN DEFAULT TRUE,          -- Whether station is currently active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily weather data (irregular temporal points)
CREATE TABLE daily_weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id VARCHAR(50) NOT NULL,         -- References weather_stations.station_id
    date DATE NOT NULL,                      -- Date of weather observation
    temperature_max REAL,                    -- Maximum temperature (°C)
    temperature_min REAL,                    -- Minimum temperature (°C)
    temperature_mean REAL,                   -- Mean temperature (°C)
    precipitation REAL,                      -- Total precipitation (mm)
    snow_depth REAL,                         -- Snow depth (cm)
    snow_fall REAL,                          -- Snow fall (cm)
    wind_speed_max REAL,                     -- Maximum wind speed (km/h)
    wind_speed_mean REAL,                    -- Mean wind speed (km/h)
    wind_direction REAL,                     -- Wind direction (degrees)
    pressure_max REAL,                       -- Maximum atmospheric pressure (hPa)
    pressure_min REAL,                       -- Minimum atmospheric pressure (hPa)
    pressure_mean REAL,                      -- Mean atmospheric pressure (hPa)
    humidity_max REAL,                       -- Maximum relative humidity (%)
    humidity_min REAL,                       -- Minimum relative humidity (%)
    humidity_mean REAL,                      -- Mean relative humidity (%)
    visibility REAL,                         -- Visibility (km)
    cloud_cover REAL,                        -- Cloud cover (%)
    sunshine_duration REAL,                  -- Sunshine duration (hours)
    source VARCHAR(50) NOT NULL,             -- 'environment_canada', 'us_weather'
    data_quality VARCHAR(20) DEFAULT 'good', -- 'good', 'questionable', 'missing'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (station_id) REFERENCES weather_stations(station_id),
    UNIQUE(station_id, date)
);

-- API call tracking (for monitoring data collection)
CREATE TABLE api_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_source VARCHAR(50) NOT NULL,         -- 'environment_canada', 'us_weather'
    endpoint VARCHAR(255) NOT NULL,          -- API endpoint called
    request_params TEXT,                     -- JSON of request parameters
    response_status INTEGER,                 -- HTTP response status
    response_size INTEGER,                   -- Response size in bytes
    records_collected INTEGER DEFAULT 0,     -- Number of weather records collected
    execution_time_ms INTEGER,               -- API call execution time
    error_message TEXT,                      -- Error message if call failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data collection jobs (for tracking bulk operations)
CREATE TABLE data_collection_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type VARCHAR(50) NOT NULL,           -- 'historical_bulk', 'daily_update', 'station_discovery'
    status VARCHAR(20) DEFAULT 'pending',    -- 'pending', 'running', 'completed', 'failed'
    start_date DATE,                         -- Start date for data collection
    end_date DATE,                           -- End date for data collection
    stations_processed INTEGER DEFAULT 0,    -- Number of stations processed
    records_collected INTEGER DEFAULT 0,     -- Number of weather records collected
    errors_count INTEGER DEFAULT 0,          -- Number of errors encountered
    started_at TIMESTAMP,                    -- When job started
    completed_at TIMESTAMP,                  -- When job completed
    error_message TEXT,                      -- Error message if job failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_weather_stations_location ON weather_stations(latitude, longitude);
CREATE INDEX idx_weather_stations_source ON weather_stations(source);
CREATE INDEX idx_weather_stations_active ON weather_stations(is_active);

CREATE INDEX idx_daily_weather_station_date ON daily_weather_data(station_id, date);
CREATE INDEX idx_daily_weather_date ON daily_weather_data(date);
CREATE INDEX idx_daily_weather_source ON daily_weather_data(source);
CREATE INDEX idx_daily_weather_quality ON daily_weather_data(data_quality);

CREATE INDEX idx_api_calls_source ON api_calls(api_source);
CREATE INDEX idx_api_calls_created ON api_calls(created_at);

CREATE INDEX idx_collection_jobs_status ON data_collection_jobs(status);
CREATE INDEX idx_collection_jobs_type ON data_collection_jobs(job_type);

-- Views for common queries

-- View: Active weather stations with latest data
CREATE VIEW active_stations_with_data AS
SELECT 
    ws.station_id,
    ws.name,
    ws.latitude,
    ws.longitude,
    ws.elevation,
    ws.province,
    ws.source,
    MAX(dwd.date) as latest_data_date,
    COUNT(dwd.id) as total_records
FROM weather_stations ws
LEFT JOIN daily_weather_data dwd ON ws.station_id = dwd.station_id
WHERE ws.is_active = TRUE
GROUP BY ws.station_id, ws.name, ws.latitude, ws.longitude, ws.elevation, ws.province, ws.source;

-- View: Daily weather summary (all stations for a given date)
CREATE VIEW daily_weather_summary AS
SELECT 
    dwd.date,
    COUNT(DISTINCT dwd.station_id) as stations_with_data,
    AVG(dwd.temperature_max) as avg_temp_max,
    AVG(dwd.temperature_min) as avg_temp_min,
    AVG(dwd.precipitation) as avg_precipitation,
    AVG(dwd.wind_speed_max) as avg_wind_speed_max,
    AVG(dwd.pressure_mean) as avg_pressure,
    AVG(dwd.humidity_mean) as avg_humidity
FROM daily_weather_data dwd
WHERE dwd.data_quality = 'good'
GROUP BY dwd.date
ORDER BY dwd.date DESC;

-- View: Station coverage by province
CREATE VIEW station_coverage_by_province AS
SELECT 
    ws.province,
    COUNT(*) as total_stations,
    COUNT(CASE WHEN ws.is_active = TRUE THEN 1 END) as active_stations,
    AVG(ws.latitude) as avg_latitude,
    AVG(ws.longitude) as avg_longitude,
    MIN(ws.data_start_date) as earliest_data,
    MAX(ws.data_end_date) as latest_data
FROM weather_stations ws
GROUP BY ws.province
ORDER BY total_stations DESC;

-- Triggers for updated_at timestamps
CREATE TRIGGER update_weather_stations_timestamp 
    AFTER UPDATE ON weather_stations
    FOR EACH ROW
    BEGIN
        UPDATE weather_stations 
        SET updated_at = CURRENT_TIMESTAMP 
        WHERE id = NEW.id;
    END;

CREATE TRIGGER update_daily_weather_timestamp 
    AFTER UPDATE ON daily_weather_data
    FOR EACH ROW
    BEGIN
        UPDATE daily_weather_data 
        SET updated_at = CURRENT_TIMESTAMP 
        WHERE id = NEW.id;
    END;

