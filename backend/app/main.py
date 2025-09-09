"""
Cirrus Project - Main FastAPI Application
Canadian Weather AI Prediction System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any

from .config import settings
from .services.weather_service import WeatherService
from .api.weather import router as weather_router

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize weather service
weather_service = WeatherService()

# Include API routers
app.include_router(weather_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Cirrus Project API",
        "description": "Canadian Weather AI Prediction System",
        "version": "1.0.0",
        "status": "active",
        "available_endpoints": [
            "/health",
            "/api/weather/current",
            "/api/weather/forecast",
            "/api/weather/alerts",
            "/api/weather/grid",
            "/api/weather/stats"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cirrus-backend"}

@app.get("/api/weather/current")
async def get_current_weather(lat: float, lon: float):
    """Get current weather data for given coordinates"""
    try:
        weather_data = await weather_service.get_current_weather(lat, lon)
        return {
            "success": True,
            "data": weather_data,
            "coordinates": {"lat": lat, "lon": lon}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")

@app.get("/api/weather/forecast")
async def get_weather_forecast(lat: float, lon: float, days: int = 5):
    """Get weather forecast for given coordinates"""
    try:
        forecast_data = await weather_service.get_forecast(lat, lon, days)
        return {
            "success": True,
            "data": forecast_data,
            "coordinates": {"lat": lat, "lon": lon},
            "forecast_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forecast data: {str(e)}")

@app.get("/api/weather/alerts")
async def get_weather_alerts(lat: float, lon: float):
    """Get weather alerts for given coordinates"""
    try:
        alerts_data = await weather_service.get_weather_alerts(lat, lon)
        return {
            "success": True,
            "data": alerts_data,
            "coordinates": {"lat": lat, "lon": lon}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts data: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
