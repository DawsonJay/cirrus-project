"""
Grid generator for creating coordinate points across Canada
"""

import logging
from typing import List, Tuple, Dict, Any
from app.database.connection import db_manager

logger = logging.getLogger(__name__)

class GridGenerator:
    """Generates grid coordinates for weather data collection"""
    
    def __init__(self, spacing_km: float = 50.0):
        self.spacing_km = spacing_km
        self.spacing_degrees = spacing_km / 111.0  # Approximate km per degree
        
        # Canada bounds (approximate)
        self.bounds = {
            "min_lat": 41.0,  # Southern border
            "max_lat": 84.0,  # Northern border
            "min_lon": -141.0,  # Western border
            "max_lon": -52.0   # Eastern border
        }
        
        # Major Canadian regions for naming (updated with more accurate bounds)
        self.regions = {
            "BC": {"min_lat": 48.0, "max_lat": 60.0, "min_lon": -140.0, "max_lon": -114.0},
            "AB": {"min_lat": 49.0, "max_lat": 60.0, "min_lon": -120.0, "max_lon": -110.0},
            "SK": {"min_lat": 49.0, "max_lat": 60.0, "min_lon": -110.0, "max_lon": -102.0},
            "MB": {"min_lat": 49.0, "max_lat": 60.0, "min_lon": -102.0, "max_lon": -95.0},
            "ON": {"min_lat": 41.0, "max_lat": 57.0, "min_lon": -95.0, "max_lon": -74.0},  # Extended south
            "QC": {"min_lat": 45.0, "max_lat": 63.0, "min_lon": -80.0, "max_lon": -57.0},
            "NB": {"min_lat": 44.0, "max_lat": 48.0, "min_lon": -69.0, "max_lon": -64.0},
            "NS": {"min_lat": 43.0, "max_lat": 47.0, "min_lon": -66.0, "max_lon": -60.0},
            "PE": {"min_lat": 46.0, "max_lat": 47.0, "min_lon": -64.0, "max_lon": -62.0},
            "NL": {"min_lat": 47.0, "max_lat": 60.0, "min_lon": -60.0, "max_lon": -52.0},
            "YT": {"min_lat": 60.0, "max_lat": 70.0, "min_lon": -141.0, "max_lon": -123.0},
            "NT": {"min_lat": 60.0, "max_lat": 78.0, "min_lon": -123.0, "max_lon": -95.0},
            "NU": {"min_lat": 60.0, "max_lat": 84.0, "min_lon": -95.0, "max_lon": -60.0},
            # Add some US border areas that might be in our grid
            "US-Border": {"min_lat": 41.0, "max_lat": 49.0, "min_lon": -141.0, "max_lon": -95.0},
            "Arctic": {"min_lat": 70.0, "max_lat": 84.0, "min_lon": -141.0, "max_lon": -60.0},
            "Maritime": {"min_lat": 41.0, "max_lat": 50.0, "min_lon": -80.0, "max_lon": -52.0}
        }
    
    def generate_grid_coordinates(self) -> List[Tuple[float, float, str]]:
        """Generate all grid coordinates for Canada"""
        coordinates = []
        
        # Generate grid points
        lat = self.bounds["min_lat"]
        while lat <= self.bounds["max_lat"]:
            lon = self.bounds["min_lon"]
            while lon <= self.bounds["max_lon"]:
                # Determine region name
                region_name = self._get_region_name(lat, lon)
                coordinates.append((lat, lon, region_name))
                
                lon += self.spacing_degrees
            lat += self.spacing_degrees
        
        logger.info(f"Generated {len(coordinates)} grid coordinates")
        return coordinates
    
    def _get_region_name(self, lat: float, lon: float) -> str:
        """Get region name for given coordinates"""
        for region, bounds in self.regions.items():
            if (bounds["min_lat"] <= lat <= bounds["max_lat"] and 
                bounds["min_lon"] <= lon <= bounds["max_lon"]):
                return region
        return "Unknown"
    
    def populate_database(self) -> bool:
        """Populate database with grid coordinates"""
        try:
            coordinates = self.generate_grid_coordinates()
            
            with db_manager as conn:
                # Clear existing grid points
                conn.execute("DELETE FROM grid_points")
                
                # Insert new coordinates
                conn.executemany(
                    "INSERT INTO grid_points (latitude, longitude, region_name) VALUES (?, ?, ?)",
                    coordinates
                )
                
                logger.info(f"Populated database with {len(coordinates)} grid points")
                return True
                
        except Exception as e:
            logger.error(f"Failed to populate database: {e}")
            return False
    
    def get_grid_points(self) -> List[Dict[str, Any]]:
        """Get all grid points from database"""
        try:
            with db_manager as conn:
                cursor = conn.execute("SELECT * FROM grid_points ORDER BY id")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get grid points: {e}")
            return []
    
    def get_coordinates_for_batch(self) -> List[Tuple[float, float]]:
        """Get coordinates in format suitable for Open-Meteo batch requests"""
        grid_points = self.get_grid_points()
        return [(point["latitude"], point["longitude"]) for point in grid_points]
    
    def get_grid_stats(self) -> Dict[str, Any]:
        """Get statistics about the grid"""
        try:
            with db_manager as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_points,
                        COUNT(DISTINCT region_name) as regions,
                        MIN(latitude) as min_lat,
                        MAX(latitude) as max_lat,
                        MIN(longitude) as min_lon,
                        MAX(longitude) as max_lon
                    FROM grid_points
                """)
                stats = dict(cursor.fetchone())
                
                # Add region breakdown
                cursor = conn.execute("""
                    SELECT region_name, COUNT(*) as count 
                    FROM grid_points 
                    GROUP BY region_name 
                    ORDER BY count DESC
                """)
                stats["region_breakdown"] = {row["region_name"]: row["count"] for row in cursor.fetchall()}
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get grid stats: {e}")
            return {}
