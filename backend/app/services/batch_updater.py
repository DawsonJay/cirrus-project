"""
Batch updater for weather data using Open-Meteo API
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from app.services.open_meteo_client import OpenMeteoClient
from app.services.grid_generator import GridGenerator
from app.database.connection import db_manager

logger = logging.getLogger(__name__)

class BatchUpdater:
    """Updates weather data for all grid points using batch API calls"""
    
    def __init__(self, batch_size: int = 540):
        self.batch_size = batch_size
        self.grid_generator = GridGenerator()
        self.open_meteo = OpenMeteoClient()
    
    async def update_all_current_weather(self) -> Dict[str, Any]:
        """Update current weather for all grid points"""
        try:
            # Get all coordinates
            coordinates = self.grid_generator.get_coordinates_for_batch()
            total_points = len(coordinates)
            
            logger.info(f"Updating current weather for {total_points} grid points")
            
            # Split into batches if needed
            batches = self._split_into_batches(coordinates)
            updated_count = 0
            failed_count = 0
            
            for i, batch_coords in enumerate(batches):
                logger.info(f"Processing batch {i+1}/{len(batches)} ({len(batch_coords)} points)")
                
                try:
                    # Make batch API call
                    batch_data = await self._get_batch_current_weather(batch_coords)
                    
                    if batch_data:
                        # Update database
                        batch_updated = await self._update_current_weather_batch(batch_data, batch_coords)
                        updated_count += batch_updated
                    else:
                        failed_count += len(batch_coords)
                    
                    # Add delay to respect rate limits (1 second between batches)
                    if i < len(batches) - 1:  # Don't delay after the last batch
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Failed to process batch {i+1}: {e}")
                    failed_count += len(batch_coords)
            
            # Log update results
            await self._log_update("current_weather", updated_count, failed_count, total_points)
            
            return {
                "success": True,
                "updated": updated_count,
                "failed": failed_count,
                "total": total_points
            }
            
        except Exception as e:
            logger.error(f"Failed to update current weather: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_all_forecasts(self) -> Dict[str, Any]:
        """Update forecast data for all grid points"""
        try:
            coordinates = self.grid_generator.get_coordinates_for_batch()
            total_points = len(coordinates)
            
            logger.info(f"Updating forecasts for {total_points} grid points")
            
            batches = self._split_into_batches(coordinates)
            updated_count = 0
            failed_count = 0
            
            for i, batch_coords in enumerate(batches):
                logger.info(f"Processing forecast batch {i+1}/{len(batches)}")
                
                try:
                    batch_data = await self._get_batch_forecast(batch_coords)
                    
                    if batch_data:
                        batch_updated = await self._update_forecast_batch(batch_data, batch_coords)
                        updated_count += batch_updated
                    else:
                        failed_count += len(batch_coords)
                        
                except Exception as e:
                    logger.error(f"Failed to process forecast batch {i+1}: {e}")
                    failed_count += len(batch_coords)
            
            await self._log_update("forecast", updated_count, failed_count, total_points)
            
            return {
                "success": True,
                "updated": updated_count,
                "failed": failed_count,
                "total": total_points
            }
            
        except Exception as e:
            logger.error(f"Failed to update forecasts: {e}")
            return {"success": False, "error": str(e)}
    
    def _split_into_batches(self, coordinates: List[Tuple[float, float]]) -> List[List[Tuple[float, float]]]:
        """Split coordinates into batches of specified size"""
        batches = []
        for i in range(0, len(coordinates), self.batch_size):
            batch = coordinates[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    async def _get_batch_current_weather(self, coordinates: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Get current weather data for a batch of coordinates"""
        try:
            async with self.open_meteo:
                params = {
                    "latitude": [coord[0] for coord in coordinates],
                    "longitude": [coord[1] for coord in coordinates],
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility,uv_index",
                    "timezone": "auto"
                }
                
                # Use POST for large batches to avoid URL length limits
                use_post = len(coordinates) > 50
                response = await self.open_meteo.make_request("/forecast", params, use_post=use_post)
                return response if isinstance(response, list) else []
                
        except Exception as e:
            logger.error(f"Failed to get batch current weather: {e}")
            return []
    
    async def _get_batch_forecast(self, coordinates: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Get forecast data for a batch of coordinates"""
        try:
            async with self.open_meteo:
                params = {
                    "latitude": [coord[0] for coord in coordinates],
                    "longitude": [coord[1] for coord in coordinates],
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,showers_sum,snowfall_sum,weather_code,wind_speed_10m_max,wind_direction_10m_dominant",
                    "timezone": "auto",
                    "forecast_days": 5
                }
                
                # Use POST for large batches to avoid URL length limits
                use_post = len(coordinates) > 50
                response = await self.open_meteo.make_request("/forecast", params, use_post=use_post)
                return response if isinstance(response, list) else []
                
        except Exception as e:
            logger.error(f"Failed to get batch forecast: {e}")
            return []
    
    async def _update_current_weather_batch(self, batch_data: List[Dict[str, Any]], coordinates: List[Tuple[float, float]]) -> int:
        """Update current weather data in database for a batch"""
        try:
            with db_manager as conn:
                updated_count = 0
                
                for i, data in enumerate(batch_data):
                    if i >= len(coordinates):
                        break
                    
                    lat, lon = coordinates[i]
                    
                    # Find grid point ID
                    cursor = conn.execute(
                        "SELECT id FROM grid_points WHERE latitude = ? AND longitude = ?",
                        (lat, lon)
                    )
                    grid_point = cursor.fetchone()
                    
                    if not grid_point:
                        continue
                    
                    grid_point_id = grid_point["id"]
                    current = data.get("current", {})
                    
                    # Insert or update current weather data
                    conn.execute("""
                        INSERT OR REPLACE INTO current_weather (
                            grid_point_id, temperature, humidity, wind_speed, wind_direction,
                            pressure, precipitation, cloud_cover, visibility, weather_code,
                            weather_description, apparent_temperature, dew_point, uv_index,
                            updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        grid_point_id,
                        current.get("temperature_2m"),
                        current.get("relative_humidity_2m"),
                        current.get("wind_speed_10m"),
                        current.get("wind_direction_10m"),
                        current.get("pressure_msl"),
                        current.get("precipitation"),
                        current.get("cloud_cover"),
                        current.get("visibility"),
                        current.get("weather_code"),
                        self._get_weather_description(current.get("weather_code")),
                        current.get("apparent_temperature"),
                        None,  # dew_point not available from Open-Meteo
                        current.get("uv_index"),
                        datetime.utcnow()
                    ))
                    
                    updated_count += 1
                
                return updated_count
                
        except Exception as e:
            logger.error(f"Failed to update current weather batch: {e}")
            return 0
    
    async def _update_forecast_batch(self, batch_data: List[Dict[str, Any]], coordinates: List[Tuple[float, float]]) -> int:
        """Update forecast data in database for a batch"""
        try:
            with db_manager as conn:
                updated_count = 0
                
                for i, data in enumerate(batch_data):
                    if i >= len(coordinates):
                        break
                    
                    lat, lon = coordinates[i]
                    
                    # Find grid point ID
                    cursor = conn.execute(
                        "SELECT id FROM grid_points WHERE latitude = ? AND longitude = ?",
                        (lat, lon)
                    )
                    grid_point = cursor.fetchone()
                    
                    if not grid_point:
                        continue
                    
                    grid_point_id = grid_point["id"]
                    daily = data.get("daily", {})
                    
                    # Get forecast dates
                    dates = daily.get("time", [])
                    max_temps = daily.get("temperature_2m_max", [])
                    min_temps = daily.get("temperature_2m_min", [])
                    precipitations = daily.get("precipitation_sum", [])
                    wind_speeds = daily.get("wind_speed_10m_max", [])
                    weather_codes = daily.get("weather_code", [])
                    
                    # Clear existing forecasts for this grid point
                    conn.execute("DELETE FROM forecast_data WHERE grid_point_id = ?", (grid_point_id,))
                    
                    # Insert new forecast data
                    for j, date in enumerate(dates):
                        if j < len(max_temps):
                            conn.execute("""
                                INSERT INTO forecast_data (
                                    grid_point_id, forecast_date, temperature_max, temperature_min,
                                    precipitation, wind_speed, weather_code, weather_description,
                                    updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                grid_point_id,
                                date,
                                max_temps[j] if j < len(max_temps) else None,
                                min_temps[j] if j < len(min_temps) else None,
                                precipitations[j] if j < len(precipitations) else None,
                                wind_speeds[j] if j < len(wind_speeds) else None,
                                weather_codes[j] if j < len(weather_codes) else None,
                                self._get_weather_description(weather_codes[j] if j < len(weather_codes) else None),
                                datetime.utcnow()
                            ))
                    
                    updated_count += 1
                
                return updated_count
                
        except Exception as e:
            logger.error(f"Failed to update forecast batch: {e}")
            return 0
    
    def _get_weather_description(self, weather_code: int) -> str:
        """Convert weather code to description"""
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return weather_descriptions.get(weather_code, "Unknown")
    
    async def _log_update(self, update_type: str, updated: int, failed: int, total: int):
        """Log update results to database"""
        try:
            with db_manager as conn:
                conn.execute("""
                    INSERT INTO update_log (update_type, grid_points_updated, success, error_message, duration_seconds)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    update_type,
                    updated,
                    failed == 0,
                    f"Updated {updated}, failed {failed}" if failed > 0 else None,
                    0.0  # Duration not tracked for now
                ))
        except Exception as e:
            logger.error(f"Failed to log update: {e}")
