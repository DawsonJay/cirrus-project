-- NOAA Weather Station Database Schema (Simplified)
-- Core tables only, no complex triggers or views

-- Weather stations table
CREATE TABLE weather_stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    elevation REAL,
    province VARCHAR(50),
    country VARCHAR(50) DEFAULT 'CA',
    source VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily weather data table
CREATE TABLE daily_weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    temperature_max REAL,
    temperature_min REAL,
    precipitation REAL,
    wind_speed_max REAL,
    pressure_mean REAL,
    humidity_mean REAL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES weather_stations(station_id),
    UNIQUE(station_id, date)
);

-- API calls tracking
CREATE TABLE api_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_source VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    response_status INTEGER,
    records_collected INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_weather_stations_location ON weather_stations(latitude, longitude);
CREATE INDEX idx_daily_weather_station_date ON daily_weather_data(station_id, date);
CREATE INDEX idx_daily_weather_date ON daily_weather_data(date);

