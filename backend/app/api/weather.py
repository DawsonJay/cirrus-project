"""
Weather API endpoints for the Cirrus Project
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.database.connection import db_manager
import math

router = APIRouter(prefix="/api/weather", tags=["weather"])


class GridPoint(BaseModel):
    """Represents a single grid point with weather data"""
    id: int
    latitude: float
    longitude: float
    region_name: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    weather_description: Optional[str] = None


class GridDataResponse(BaseModel):
    """Response containing grid points for visualization"""
    points: List[GridPoint]
    total_points: int
    data_coverage: float
    temperature_range: dict


@router.get("/grid", response_model=GridDataResponse)
async def get_grid_data(sample_size: int = 1000):
    """
    Get evenly distributed grid points for map visualization
    
    Args:
        sample_size: Number of points to return (default 1000)
    
    Returns:
        GridDataResponse with evenly distributed points
    """
    try:
        with db_manager as conn:
            # Get total count for coverage calculation
            cursor = conn.execute("SELECT COUNT(*) as total FROM grid_points")
            total_points = cursor.fetchone()["total"]
            
            # Get evenly distributed sample
            # Use modulo to get evenly spaced points
            step = max(1, total_points // sample_size)
            
            cursor = conn.execute("""
                SELECT 
                    gp.id,
                    gp.latitude,
                    gp.longitude,
                    gp.region_name,
                    cw.temperature,
                    cw.humidity,
                    cw.weather_description
                FROM grid_points gp
                LEFT JOIN current_weather cw ON gp.id = cw.grid_point_id
                WHERE gp.id % ? = 0
                ORDER BY gp.id
                LIMIT ?
            """, (step, sample_size))
            
            points_data = cursor.fetchall()
            
            # Convert to GridPoint objects
            points = []
            for row in points_data:
                point = GridPoint(
                    id=row["id"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    region_name=row["region_name"],
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                    weather_description=row["weather_description"]
                )
                points.append(point)
            
            # Calculate data coverage
            points_with_data = sum(1 for p in points if p.temperature is not None)
            data_coverage = (points_with_data / len(points)) * 100 if points else 0
            
            # Calculate temperature range
            temperatures = [p.temperature for p in points if p.temperature is not None]
            temperature_range = {
                "min": min(temperatures) if temperatures else None,
                "max": max(temperatures) if temperatures else None
            }
            
            return GridDataResponse(
                points=points,
                total_points=len(points),
                data_coverage=data_coverage,
                temperature_range=temperature_range
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch grid data: {str(e)}")


@router.get("/grid/full")
async def get_full_grid_data():
    """
    Get all grid points (use with caution - returns 19,008 points)
    """
    try:
        with db_manager as conn:
            cursor = conn.execute("""
                SELECT 
                    gp.id,
                    gp.latitude,
                    gp.longitude,
                    gp.region_name,
                    cw.temperature,
                    cw.humidity,
                    cw.weather_description
                FROM grid_points gp
                LEFT JOIN current_weather cw ON gp.id = cw.grid_point_id
                ORDER BY gp.id
            """)
            
            points_data = cursor.fetchall()
            
            # Convert to dict format for JSON response
            points = []
            for row in points_data:
                points.append({
                    "id": row["id"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "region_name": row["region_name"],
                    "temperature": row["temperature"],
                    "humidity": row["humidity"],
                    "weather_description": row["weather_description"]
                })
            
            return {
                "points": points,
                "total_points": len(points),
                "message": "Full grid data - use /grid endpoint for better performance"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch full grid data: {str(e)}")


@router.get("/stats")
async def get_weather_stats():
    """Get weather data statistics"""
    try:
        with db_manager as conn:
            # Grid statistics
            cursor = conn.execute("SELECT COUNT(*) as total FROM grid_points")
            total_grid_points = cursor.fetchone()["total"]
            
            # Weather data statistics
            cursor = conn.execute("SELECT COUNT(*) as total FROM current_weather")
            weather_points = cursor.fetchone()["total"]
            
            # Temperature statistics
            cursor = conn.execute("""
                SELECT 
                    MIN(temperature) as min_temp,
                    MAX(temperature) as max_temp,
                    AVG(temperature) as avg_temp,
                    COUNT(*) as data_points
                FROM current_weather
            """)
            temp_stats = cursor.fetchone()
            
            # Regional breakdown
            cursor = conn.execute("""
                SELECT 
                    gp.region_name,
                    COUNT(*) as total_points,
                    COUNT(cw.id) as data_points,
                    ROUND((COUNT(cw.id) * 100.0 / COUNT(*)), 1) as coverage_percent
                FROM grid_points gp
                LEFT JOIN current_weather cw ON gp.id = cw.grid_point_id
                GROUP BY gp.region_name
                ORDER BY total_points DESC
            """)
            regions = cursor.fetchall()
            
            return {
                "grid": {
                    "total_points": total_grid_points,
                    "weather_data_points": weather_points,
                    "coverage_percent": round((weather_points / total_grid_points) * 100, 1)
                },
                "temperature": {
                    "min": temp_stats["min_temp"],
                    "max": temp_stats["max_temp"],
                    "average": round(temp_stats["avg_temp"], 1) if temp_stats["avg_temp"] else None,
                    "data_points": temp_stats["data_points"]
                },
                "regions": [
                    {
                        "name": region["region_name"],
                        "total_points": region["total_points"],
                        "data_points": region["data_points"],
                        "coverage_percent": region["coverage_percent"]
                    }
                    for region in regions
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather stats: {str(e)}")
