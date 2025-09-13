-- SQLite Database Schema for AI Wildfire Prediction
-- Optimized for Canadian NOAA GHCN-Daily data

-- Stations table: Station metadata and location information
CREATE TABLE stations (
    station_id TEXT PRIMARY KEY,           -- 11-char station ID (e.g., CA001010066)
    name TEXT NOT NULL,                    -- Station name
    latitude REAL NOT NULL,                -- Latitude in decimal degrees
    longitude REAL NOT NULL,               -- Longitude in decimal degrees
    elevation REAL,                        -- Elevation in meters
    country TEXT,                          -- Country code (CA for Canada)
    state TEXT,                            -- Province/state code
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather data table: Daily weather measurements
CREATE TABLE weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT NOT NULL,              -- Foreign key to stations
    date DATE NOT NULL,                    -- Date of measurement (YYYY-MM-DD)
    parameter TEXT NOT NULL,               -- Weather parameter (TMAX, TMIN, PRCP, etc.)
    value REAL,                            -- Measured value (scaled by 10 for temps)
    quality_flag TEXT,                     -- Quality flag (A, B, C, D, E, F, G, H, I)
    measurement_flag TEXT,                 -- Measurement flag (B, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z)
    source_flag TEXT,                      -- Source flag (A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (station_id) REFERENCES stations(station_id),
    UNIQUE(station_id, date, parameter)    -- Prevent duplicate entries
);

-- Station inventory table: What data each station has and when
CREATE TABLE station_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT NOT NULL,              -- Foreign key to stations
    parameter TEXT NOT NULL,               -- Weather parameter
    start_year INTEGER NOT NULL,           -- First year of data
    end_year INTEGER NOT NULL,             -- Last year of data
    latitude REAL NOT NULL,                -- Station latitude (denormalized for queries)
    longitude REAL NOT NULL,               -- Station longitude (denormalized for queries)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (station_id) REFERENCES stations(station_id),
    UNIQUE(station_id, parameter)
);

-- Indexes for optimal AI training performance
CREATE INDEX idx_weather_station_date ON weather_data(station_id, date);
CREATE INDEX idx_weather_parameter ON weather_data(parameter);
CREATE INDEX idx_weather_date ON weather_data(date);
CREATE INDEX idx_weather_station_parameter ON weather_data(station_id, parameter);
CREATE INDEX idx_weather_value ON weather_data(value) WHERE value IS NOT NULL;

-- Geographic indexes for spatial queries
CREATE INDEX idx_stations_location ON stations(latitude, longitude);
CREATE INDEX idx_stations_country ON stations(country);
CREATE INDEX idx_stations_state ON stations(state);

-- Inventory indexes for data availability queries
CREATE INDEX idx_inventory_station ON station_inventory(station_id);
CREATE INDEX idx_inventory_parameter ON station_inventory(parameter);
CREATE INDEX idx_inventory_years ON station_inventory(start_year, end_year);

-- Wildfire-specific parameter view for easy access
CREATE VIEW wildfire_parameters AS
SELECT 
    wd.station_id,
    s.name as station_name,
    s.latitude,
    s.longitude,
    s.elevation,
    s.state,
    wd.date,
    wd.parameter,
    wd.value,
    wd.quality_flag
FROM weather_data wd
JOIN stations s ON wd.station_id = s.station_id
WHERE wd.parameter IN ('TMAX', 'TMIN', 'PRCP', 'SNWD', 'WESD', 'WESF', 'WSFG', 'SNOW', 'TAVG')
  AND wd.value IS NOT NULL
  AND wd.quality_flag IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I');  -- Valid quality flags

-- Daily weather summary view for AI training
CREATE VIEW daily_weather_summary AS
SELECT 
    station_id,
    date,
    MAX(CASE WHEN parameter = 'TMAX' THEN value END) as max_temp,
    MIN(CASE WHEN parameter = 'TMIN' THEN value END) as min_temp,
    AVG(CASE WHEN parameter = 'TAVG' THEN value END) as avg_temp,
    SUM(CASE WHEN parameter = 'PRCP' THEN value END) as precipitation,
    AVG(CASE WHEN parameter = 'SNWD' THEN value END) as snow_depth,
    SUM(CASE WHEN parameter = 'SNOW' THEN value END) as snowfall,
    AVG(CASE WHEN parameter = 'WESD' THEN value END) as snow_water_equivalent_depth,
    SUM(CASE WHEN parameter = 'WESF' THEN value END) as snow_water_equivalent_fall,
    MAX(CASE WHEN parameter = 'WSFG' THEN value END) as peak_gust_wind_speed
FROM weather_data
WHERE parameter IN ('TMAX', 'TMIN', 'TAVG', 'PRCP', 'SNWD', 'SNOW', 'WESD', 'WESF', 'WSFG')
  AND value IS NOT NULL
GROUP BY station_id, date;

-- Station coverage summary for data quality assessment
CREATE VIEW station_coverage AS
SELECT 
    s.station_id,
    s.name,
    s.latitude,
    s.longitude,
    s.state,
    COUNT(DISTINCT wd.date) as total_days,
    MIN(wd.date) as first_date,
    MAX(wd.date) as last_date,
    COUNT(DISTINCT wd.parameter) as parameters_count,
    GROUP_CONCAT(DISTINCT wd.parameter) as available_parameters
FROM stations s
LEFT JOIN weather_data wd ON s.station_id = wd.station_id
GROUP BY s.station_id, s.name, s.latitude, s.longitude, s.state;

-- Data quality summary for AI training validation
CREATE VIEW data_quality_summary AS
SELECT 
    parameter,
    COUNT(*) as total_records,
    COUNT(CASE WHEN value IS NOT NULL THEN 1 END) as non_null_records,
    COUNT(CASE WHEN value IS NULL THEN 1 END) as null_records,
    ROUND(AVG(value), 2) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(DISTINCT station_id) as stations_count,
    COUNT(DISTINCT date) as days_count
FROM weather_data
GROUP BY parameter
ORDER BY total_records DESC;
