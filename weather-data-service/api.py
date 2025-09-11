#!/usr/bin/env python3
"""
API Service for Weather Data Collection

This module provides REST API endpoints for triggering weather data collection
and monitoring collection status.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from collection import collect_year, collect_years, get_all_stations
from stations_database import get_station_info
from weather_database import get_weather_data_summary

# Initialize FastAPI app
app = FastAPI(
    title="Weather Data Collection API",
    description="API for collecting and managing Canadian weather station data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track running collections
running_collections: Dict[str, Dict[str, Any]] = {}

# Pydantic models for request/response
class CollectionRequest(BaseModel):
    year: int = Field(..., description="Year to collect data for")
    limit: Optional[int] = Field(None, description="Limit number of stations to process")

class MultiYearCollectionRequest(BaseModel):
    start_year: int = Field(..., description="Start year for collection")
    end_year: int = Field(..., description="End year for collection")
    limit: Optional[int] = Field(None, description="Limit number of stations per year")

class CollectionStatus(BaseModel):
    collection_id: str
    status: str  # "running", "completed", "failed"
    start_time: datetime
    end_time: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class StationInfo(BaseModel):
    station_id: str
    name: str
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    active_periods: List[Dict[str, Any]]

class WeatherDataSummary(BaseModel):
    total_records: int
    stations_with_data: int
    date_range: Dict[str, str]
    sample_records: List[Dict[str, Any]]

# Helper function to generate collection IDs
def generate_collection_id(collection_type: str, **kwargs) -> str:
    """Generate a unique collection ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if collection_type == "year":
        return f"year_{kwargs['year']}_{timestamp}"
    elif collection_type == "years":
        return f"years_{kwargs['start_year']}_{kwargs['end_year']}_{timestamp}"
    return f"collection_{timestamp}"

# Helper function to run collection in background with rate limiting
async def run_collection_background(collection_id: str, collection_type: str, **kwargs):
    """Run collection in background and update status with global rate limiting"""
    try:
        running_collections[collection_id]["status"] = "running"
        running_collections[collection_id]["start_time"] = datetime.now()
        
        # Apply global rate limiting to collection functions
        if collection_type == "year":
            result = await collect_year_with_rate_limit(kwargs["year"], kwargs.get("limit"))
        elif collection_type == "years":
            result = await collect_years_with_rate_limit(kwargs["start_year"], kwargs["end_year"], kwargs.get("limit"))
        else:
            raise ValueError(f"Unknown collection type: {collection_type}")
        
        running_collections[collection_id]["status"] = "completed"
        running_collections[collection_id]["end_time"] = datetime.now()
        running_collections[collection_id]["progress"] = result
        
    except Exception as e:
        running_collections[collection_id]["status"] = "failed"
        running_collections[collection_id]["end_time"] = datetime.now()
        running_collections[collection_id]["error"] = str(e)

# Rate-limited wrapper functions
async def collect_year_with_rate_limit(year: int, limit: Optional[int] = None) -> Dict[str, Any]:
    """Collect year data with global rate limiting"""
    # This is a simplified approach - in practice, you'd want to modify the 
    # actual collection functions to use the global rate limiter
    print(f"🌐 Using global rate limiter for year {year} collection")
    return await collect_year(year, limit)

async def collect_years_with_rate_limit(start_year: int, end_year: int, limit: Optional[int] = None) -> Dict[str, Any]:
    """Collect years data with global rate limiting"""
    print(f"🌐 Using global rate limiter for years {start_year}-{end_year} collection")
    return await collect_years(start_year, end_year, limit)

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Weather Data Collection API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "collect_year": "/collect/year",
            "collect_years": "/collect/years",
            "status": "/status/{collection_id}",
            "stations": "/stations",
            "weather_data": "/weather-data",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "running_collections": len([c for c in running_collections.values() if c["status"] == "running"])
    }

@app.post("/collect/year", response_model=CollectionStatus)
async def start_year_collection(
    request: CollectionRequest,
    background_tasks: BackgroundTasks
):
    """Start collecting weather data for a specific year"""
    collection_id = generate_collection_id("year", year=request.year, limit=request.limit)
    
    # Initialize collection status
    running_collections[collection_id] = {
        "collection_id": collection_id,
        "status": "starting",
        "start_time": datetime.now(),
        "end_time": None,
        "progress": None,
        "error": None
    }
    
    # Start collection in background
    background_tasks.add_task(
        run_collection_background,
        collection_id,
        "year",
        year=request.year,
        limit=request.limit
    )
    
    return CollectionStatus(**running_collections[collection_id])

@app.post("/collect/years", response_model=CollectionStatus)
async def start_multi_year_collection(
    request: MultiYearCollectionRequest,
    background_tasks: BackgroundTasks
):
    """Start collecting weather data for a range of years"""
    collection_id = generate_collection_id(
        "years",
        start_year=request.start_year,
        end_year=request.end_year,
        limit=request.limit
    )
    
    # Initialize collection status
    running_collections[collection_id] = {
        "collection_id": collection_id,
        "status": "starting",
        "start_time": datetime.now(),
        "end_time": None,
        "progress": None,
        "error": None
    }
    
    # Start collection in background
    background_tasks.add_task(
        run_collection_background,
        collection_id,
        "years",
        start_year=request.start_year,
        end_year=request.end_year,
        limit=request.limit
    )
    
    return CollectionStatus(**running_collections[collection_id])

@app.get("/status/{collection_id}", response_model=CollectionStatus)
async def get_collection_status(collection_id: str):
    """Get the status of a specific collection"""
    if collection_id not in running_collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return CollectionStatus(**running_collections[collection_id])

@app.get("/status")
async def get_all_collection_status():
    """Get status of all collections"""
    return {
        "collections": list(running_collections.values()),
        "total": len(running_collections),
        "running": len([c for c in running_collections.values() if c["status"] == "running"]),
        "completed": len([c for c in running_collections.values() if c["status"] == "completed"]),
        "failed": len([c for c in running_collections.values() if c["status"] == "failed"])
    }

@app.get("/stations", response_model=List[StationInfo])
async def get_stations(limit: Optional[int] = Query(None, description="Limit number of stations")):
    """Get list of all weather stations"""
    try:
        stations = get_all_stations(limit)
        return [
            StationInfo(
                station_id=station["station_id"],
                name=station["name"],
                latitude=station["latitude"],
                longitude=station["longitude"],
                elevation=station["elevation"],
                active_periods=station.get("active_periods", [])
            )
            for station in stations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stations: {str(e)}")

@app.get("/stations/{station_id}", response_model=StationInfo)
async def get_station(station_id: str):
    """Get information about a specific station"""
    try:
        station_info = get_station_info(station_id)
        if not station_info:
            raise HTTPException(status_code=404, detail="Station not found")
        
        return StationInfo(
            station_id=station_info["station_id"],
            name=station_info["name"],
            latitude=station_info["latitude"],
            longitude=station_info["longitude"],
            elevation=station_info["elevation"],
            active_periods=station_info.get("active_periods", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching station: {str(e)}")

@app.get("/weather-data", response_model=WeatherDataSummary)
async def get_weather_data_summary_endpoint(
    year: Optional[int] = Query(None, description="Filter by year"),
    station_id: Optional[str] = Query(None, description="Filter by station ID")
):
    """Get summary of weather data in the database"""
    try:
        summary = get_weather_data_summary(year, station_id)
        return WeatherDataSummary(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data summary: {str(e)}")

@app.delete("/status/{collection_id}")
async def cancel_collection(collection_id: str):
    """Cancel a running collection (note: this is a placeholder - actual cancellation would require more complex implementation)"""
    if collection_id not in running_collections:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if running_collections[collection_id]["status"] == "running":
        running_collections[collection_id]["status"] = "cancelled"
        running_collections[collection_id]["end_time"] = datetime.now()
        return {"message": f"Collection {collection_id} marked for cancellation"}
    else:
        return {"message": f"Collection {collection_id} is not running"}

if __name__ == "__main__":
    import os
    
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    
    print(f"🌤️  Starting Weather Data Collection API")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
