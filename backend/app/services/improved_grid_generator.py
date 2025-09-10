"""
Improved grid generator for creating evenly spaced coordinate points across Canada
Uses proper geographic spacing that accounts for Earth's curvature
"""

import logging
import math
from typing import List, Tuple, Dict, Any
from app.database.connection import db_manager

logger = logging.getLogger(__name__)

class ImprovedGridGenerator:
    """Generates evenly spaced grid coordinates for weather data collection"""
    
    def __init__(self, target_points: int = 10000):
        self.target_points = target_points
        
        # Canada bounds (more precise)
        self.bounds = {
            "min_lat": 41.0,   # Southern border (US border)
            "max_lat": 84.0,   # Northern border (Arctic)
            "min_lon": -141.0, # Western border (Alaska border)
            "max_lon": -52.0   # Eastern border (Atlantic)
        }
        
        # Calculate optimal spacing for even coverage
        self.spacing_km = self._calculate_optimal_spacing()
        logger.info(f"Target: {target_points} points, Optimal spacing: {self.spacing_km:.1f} km")
        
        # Regional classification
        self.regions = {
            "arctic": {"min_lat": 70.0, "max_lat": 84.0},
            "northern": {"min_lat": 60.0, "max_lat": 70.0},
            "central": {"min_lat": 50.0, "max_lat": 60.0},
            "southern": {"min_lat": 41.0, "max_lat": 50.0}
        }
    
    def _calculate_optimal_spacing(self) -> float:
        """Calculate optimal spacing to achieve target point count with even coverage"""
        
        # Calculate area of Canada in square kilometers
        # Using a more accurate method that accounts for Earth's curvature
        
        # Convert bounds to radians
        min_lat_rad = math.radians(self.bounds["min_lat"])
        max_lat_rad = math.radians(self.bounds["max_lat"])
        min_lon_rad = math.radians(self.bounds["min_lon"])
        max_lon_rad = math.radians(self.bounds["max_lon"])
        
        # Earth's radius in km
        R = 6371.0
        
        # Calculate area using spherical geometry
        # Area = R² * (max_lon - min_lon) * (sin(max_lat) - sin(min_lat))
        area_km2 = R * R * (max_lon_rad - min_lon_rad) * (math.sin(max_lat_rad) - math.sin(min_lat_rad))
        
        # Calculate spacing to achieve target points
        # Each point covers an area of spacing²
        spacing_km = math.sqrt(area_km2 / self.target_points)
        
        return spacing_km
    
    def _km_to_degrees_lat(self, km: float) -> float:
        """Convert kilometers to degrees of latitude (constant)"""
        return km / 111.0
    
    def _km_to_degrees_lon(self, km: float, lat: float) -> float:
        """Convert kilometers to degrees of longitude (varies with latitude)"""
        return km / (111.0 * math.cos(math.radians(lat)))
    
    def generate_grid_coordinates(self) -> List[Tuple[float, float, str]]:
        """Generate evenly spaced grid coordinates for Canada"""
        coordinates = []
        
        # Calculate spacing in degrees
        lat_spacing = self._km_to_degrees_lat(self.spacing_km)
        
        # Generate grid points
        lat = self.bounds["min_lat"]
        while lat <= self.bounds["max_lat"]:
            # Calculate longitude spacing for this latitude
            lon_spacing = self._km_to_degrees_lon(self.spacing_km, lat)
            
            lon = self.bounds["min_lon"]
            while lon <= self.bounds["max_lon"]:
                # Determine region
                region = self._get_region(lat)
                coordinates.append((lat, lon, region))
                
                lon += lon_spacing
            lat += lat_spacing
        
        logger.info(f"Generated {len(coordinates)} grid coordinates with {self.spacing_km:.1f} km spacing")
        return coordinates
    
    def _get_region(self, lat: float) -> str:
        """Get region classification based on latitude"""
        if lat >= 70.0:
            return "arctic"
        elif lat >= 60.0:
            return "northern"
        elif lat >= 50.0:
            return "central"
        else:
            return "southern"
    
    def populate_database(self) -> bool:
        """Populate database with grid coordinates"""
        try:
            coordinates = self.generate_grid_coordinates()
            
            with db_manager as conn:
                # Clear existing grid points
                conn.execute("DELETE FROM grid_points")
                
                # Insert new coordinates
                conn.executemany(
                    "INSERT INTO grid_points (latitude, longitude, region) VALUES (?, ?, ?)",
                    coordinates
                )
                
                conn.commit()
                logger.info(f"Populated database with {len(coordinates)} grid points")
                return True
                
        except Exception as e:
            logger.error(f"Failed to populate database: {e}")
            return False
    
    def get_grid_stats(self) -> Dict[str, Any]:
        """Get statistics about the grid"""
        try:
            with db_manager as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_points,
                        COUNT(DISTINCT region) as regions,
                        MIN(latitude) as min_lat,
                        MAX(latitude) as max_lat,
                        MIN(longitude) as min_lon,
                        MAX(longitude) as max_lon
                    FROM grid_points
                """)
                stats = dict(cursor.fetchone())
                
                # Add region breakdown
                cursor = conn.execute("""
                    SELECT region, COUNT(*) as count 
                    FROM grid_points 
                    GROUP BY region 
                    ORDER BY count DESC
                """)
                stats["region_breakdown"] = {row["region"]: row["count"] for row in cursor.fetchall()}
                
                # Calculate actual spacing
                if stats["total_points"] > 1:
                    cursor = conn.execute("""
                        SELECT latitude, longitude FROM grid_points 
                        ORDER BY latitude, longitude LIMIT 2
                    """)
                    points = cursor.fetchall()
                    if len(points) == 2:
                        lat_diff = abs(points[1][0] - points[0][0])
                        lon_diff = abs(points[1][1] - points[0][1])
                        stats["actual_lat_spacing_km"] = lat_diff * 111.0
                        stats["actual_lon_spacing_km"] = lon_diff * 111.0 * math.cos(math.radians(points[0][0]))
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get grid stats: {e}")
            return {}
    
    def get_coordinates_for_batch(self) -> List[Tuple[float, float]]:
        """Get coordinates in format suitable for Open-Meteo batch requests"""
        try:
            with db_manager as conn:
                cursor = conn.execute("SELECT latitude, longitude FROM grid_points ORDER BY id")
                return [(row["latitude"], row["longitude"]) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get coordinates: {e}")
            return []
    
    def analyze_coverage(self) -> Dict[str, Any]:
        """Analyze the coverage quality of the grid"""
        try:
            with db_manager as conn:
                # Get sample of points to analyze spacing
                cursor = conn.execute("""
                    SELECT latitude, longitude FROM grid_points 
                    ORDER BY latitude, longitude 
                    LIMIT 100
                """)
                points = [(row["latitude"], row["longitude"]) for row in cursor.fetchall()]
                
                if len(points) < 2:
                    return {"error": "Not enough points to analyze"}
                
                # Calculate spacing variations
                spacings = []
                for i in range(len(points) - 1):
                    lat1, lon1 = points[i]
                    lat2, lon2 = points[i + 1]
                    
                    # Calculate distance using Haversine formula
                    lat1_rad = math.radians(lat1)
                    lat2_rad = math.radians(lat2)
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    
                    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    distance_km = 6371 * c
                    
                    spacings.append(distance_km)
                
                if spacings:
                    avg_spacing = sum(spacings) / len(spacings)
                    min_spacing = min(spacings)
                    max_spacing = max(spacings)
                    spacing_variance = sum((s - avg_spacing)**2 for s in spacings) / len(spacings)
                    
                    return {
                        "average_spacing_km": avg_spacing,
                        "min_spacing_km": min_spacing,
                        "max_spacing_km": max_spacing,
                        "spacing_variance": spacing_variance,
                        "spacing_consistency": "good" if spacing_variance < (avg_spacing * 0.1)**2 else "poor"
                    }
                
        except Exception as e:
            logger.error(f"Failed to analyze coverage: {e}")
            return {"error": str(e)}
