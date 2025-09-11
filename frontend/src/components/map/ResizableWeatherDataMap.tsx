import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

interface GridPoint {
  id: number;
  latitude: number;
  longitude: number;
  region_name: string;
  temperature: number | null;
  humidity: number | null;
  weather_description: string | null;
}

interface GridDataResponse {
  points: GridPoint[];
  total_points: number;
  data_coverage: number;
  temperature_range: {
    min: number | null;
    max: number | null;
  };
}

interface ResizableWeatherDataMapProps {
  sampleSize?: number;
  mapWidth?: number;
  mapHeight?: number;
}

const ResizableWeatherDataMap: React.FC<ResizableWeatherDataMapProps> = ({ 
  sampleSize = 1000, 
  mapWidth = 800, 
  mapHeight = 600 
}) => {
  const [gridData, setGridData] = useState<GridDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Reference points with normalized coordinates (0-1 range)
  // These are the original calibrated positions normalized to the base 800x600 viewBox
  const normalizedReferencePoints = {
    capeColumbia: { x: 0.6589, y: 0.0446, name: "Cape Columbia", lat: 83.111, lon: -69.958 },
    windsor: { x: 0.5827, y: 0.9463, name: "Windsor", lat: 42.3149, lon: -83.0364 },
    capeSpear: { x: 0.7589, y: 0.8828, name: "Cape Spear", lat: 47.517, lon: -52.617 },
    vancouver: { x: 0.3464, y: 0.8663, name: "Vancouver", lat: 49.2827, lon: -123.1207 },
    toronto: { x: 0.6027, y: 0.9296, name: "Toronto", lat: 43.7, lon: -79.4 },
    capeBreton: { x: 0.6909, y: 0.9047, name: "Cape Breton", lat: 45.95, lon: -59.97 },
    churchill: { x: 0.5166, y: 0.7368, name: "Churchill", lat: 58.768, lon: -94.17 },
    yellowknife: { x: 0.3972, y: 0.6818, name: "Yellowknife", lat: 62.454, lon: -114.372 },
    winnipeg: { x: 0.4987, y: 0.8591, name: "Winnipeg", lat: 49.895, lon: -97.138 },
    montreal: { x: 0.6460, y: 0.9074, name: "Montreal", lat: 45.502, lon: -73.567 },
    calgary: { x: 0.4017, y: 0.8416, name: "Calgary", lat: 51.0447, lon: -114.0719 },
    halifax: { x: 0.6954, y: 0.9195, name: "Halifax", lat: 44.6488, lon: -63.5752 },
    whitehorse: { x: 0.2777, y: 0.7127, name: "Whitehorse", lat: 60.7212, lon: -135.0568 },
    iqaluit: { x: 0.6666, y: 0.6593, name: "Iqaluit", lat: 63.7467, lon: -68.517 },
    stJohns: { x: 0.7600, y: 0.8779, name: "St. John's", lat: 47.5615, lon: -52.7126 },
    princeRupert: { x: 0.3019, y: 0.8027, name: "Prince Rupert", lat: 54.3, lon: -130.3 },
    resolute: { x: 0.5121, y: 0.4106, name: "Resolute", lat: 74.7, lon: -94.8 },
    tuktoyaktuk: { x: 0.2894, y: 0.5408, name: "Tuktoyaktuk", lat: 69.4, lon: -133.0 },
    saskatoon: { x: 0.4394, y: 0.8285, name: "Saskatoon", lat: 52.1579, lon: -106.6702 },
    thunderBay: { x: 0.5490, y: 0.8738, name: "Thunder Bay", lat: 48.3809, lon: -89.2477 },
    victoria: { x: 0.3450, y: 0.8775, name: "Victoria", lat: 48.4284, lon: -123.3656 },
    fredericton: { x: 0.6769, y: 0.9062, name: "Fredericton", lat: 45.9636, lon: -66.6431 },
    inuvik: { x: 0.2844, y: 0.5672, name: "Inuvik", lat: 68.3607, lon: -133.7230 },
    alert: { x: 0.6666, y: 0.4106, name: "Alert", lat: 82.5018, lon: -62.3481 }
  };

  // Convert normalized coordinates to actual pixel coordinates based on current map size
  const getScaledReferencePoints = () => {
    return Object.fromEntries(
      Object.entries(normalizedReferencePoints).map(([key, point]) => [
        key,
        {
          ...point,
          x: point.x * mapWidth,
          y: point.y * mapHeight
        }
      ])
    );
  };

  // Convert geographic coordinates to SVG coordinates using proper geographic projection
  const geoToSvg = (lat: number, lon: number) => {
    const scaledPoints = getScaledReferencePoints();
    const points = Object.values(scaledPoints);
    
    // Get the extreme points from scaled positions
    const northPoint = points.find(p => p.name === "Cape Columbia")!;
    const southPoint = points.find(p => p.name === "Windsor")!;
    const eastPoint = points.find(p => p.name === "Cape Spear")!;
    const westPoint = points.find(p => p.name === "Vancouver")!;
    
    // Convert to radians for trigonometric calculations
    const latRad = (lat * Math.PI) / 180;
    const lonRad = (lon * Math.PI) / 180;
    const northLatRad = (northPoint.lat * Math.PI) / 180;
    const southLatRad = (southPoint.lat * Math.PI) / 180;
    const eastLonRad = (eastPoint.lon * Math.PI) / 180;
    const westLonRad = (westPoint.lon * Math.PI) / 180;
    
    // Use Mercator projection for longitude (accounts for Earth's curvature)
    const mercatorLat = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
    const mercatorNorthLat = Math.log(Math.tan(Math.PI / 4 + northLatRad / 2));
    const mercatorSouthLat = Math.log(Math.tan(Math.PI / 4 + southLatRad / 2));
    
    // Calculate percentages using Mercator projection
    const latPercent = (mercatorLat - mercatorSouthLat) / (mercatorNorthLat - mercatorSouthLat);
    const lonPercent = (lonRad - westLonRad) / (eastLonRad - westLonRad);
    
    // Map to SVG coordinates using scaled positions
    const x = westPoint.x + (lonPercent * (eastPoint.x - westPoint.x));
    const y = southPoint.y - (latPercent * (southPoint.y - northPoint.y));
    
    return { x, y };
  };

  // Get temperature color
  const getTemperatureColor = (temperature: number | null) => {
    if (temperature === null) {
      return '#ffffff';
    }
    
    const minTemp = -70;
    const maxTemp = 40;
    const normalizedTemp = (temperature - minTemp) / (maxTemp - minTemp);
    
    if (normalizedTemp <= 0.5) {
      const intensity = normalizedTemp * 2;
      const blue = Math.round(255 * (1 - intensity));
      const green = Math.round(255 * (1 - intensity));
      const red = Math.round(255 * intensity);
      return `rgb(${red}, ${green}, ${blue})`;
    } else {
      const intensity = (normalizedTemp - 0.5) * 2;
      const red = 255;
      const green = Math.round(255 * (1 - intensity));
      const blue = Math.round(255 * (1 - intensity));
      return `rgb(${red}, ${green}, ${blue})`;
    }
  };

  // Fetch grid data from weather data service
  useEffect(() => {
    const fetchGridData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch(`http://localhost:8000/api/weather/grid?sample_size=${sampleSize}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data: GridDataResponse = await response.json();
        setGridData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch weather data');
        console.error('Error fetching grid data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGridData();
  }, [sampleSize]);

  const scaledPoints = getScaledReferencePoints();

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        flexDirection: 'column',
        gap: 2
      }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">
          Loading weather data...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        p: 2
      }}>
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          <Typography variant="h6">Failed to load weather data</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  if (!gridData) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%'
      }}>
        <Typography variant="body2" color="text.secondary">
          No weather data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', position: 'relative' }}>
      {/* Background */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: '#2a2e37',
        }}
      />
      
      {/* Canada SVG Map */}
      <Box
        component="img"
        src="/assets/maps/canada-wireframe.svg"
        alt="Canada Wireframe Map by Vemaps.com"
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          zIndex: 2,
        }}
      />

      {/* Weather Data Overlay */}
      <Box
        component="svg"
        viewBox={`0 0 ${mapWidth} ${mapHeight}`}
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 3,
          pointerEvents: 'auto',
        }}
      >
        {/* Reference Points - Only show key ones for clarity */}
        {Object.entries(scaledPoints)
          .filter(([key]) => ['toronto', 'vancouver', 'montreal', 'calgary', 'halifax'].includes(key))
          .map(([key, point]) => (
          <g key={key}>
            <circle
              cx={point.x}
              cy={point.y}
              r="2"
              fill={
                key === 'toronto' ? '#ff00ff' : 
                key === 'vancouver' ? '#ffff00' :
                key === 'montreal' ? '#88ff00' :
                key === 'calgary' ? '#ff4444' :
                key === 'halifax' ? '#44ff44' : '#ffffff'
              }
              opacity="1"
            />
            <text
              x={point.x + 8}
              y={point.y + 4}
              fill="white"
              fontSize="10"
              fontWeight="bold"
              style={{ textShadow: '1px 1px 2px black' }}
            >
              {point.name}
            </text>
          </g>
        ))}
        
        {/* Weather Data Points */}
        {gridData.points.map((point) => {
          const { x, y } = geoToSvg(point.latitude, point.longitude);
          const color = getTemperatureColor(point.temperature);
          
          return (
            <circle
              key={point.id}
              cx={x}
              cy={y}
              r="1"
              fill={color}
              opacity={point.temperature === null ? 0.3 : 0.8}
            />
          );
        })}
      </Box>

      {/* Data Info Overlay */}
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: 2,
          borderRadius: 1,
          zIndex: 4,
          minWidth: 200,
        }}
      >
        <Typography variant="h6" gutterBottom>
          Weather Data
        </Typography>
        <Typography variant="body2">
          Points: {gridData.total_points.toLocaleString()}
        </Typography>
        <Typography variant="body2">
          Coverage: {gridData.data_coverage.toFixed(1)}%
        </Typography>
        <Typography variant="body2">
          Map Size: {mapWidth} × {mapHeight}
        </Typography>
        {gridData.temperature_range.min !== null && gridData.temperature_range.max !== null && (
          <>
            <Typography variant="body2">
              Temp Range: {gridData.temperature_range.min.toFixed(1)}°C to {gridData.temperature_range.max.toFixed(1)}°C
            </Typography>
          </>
        )}
        <Typography variant="body2" sx={{ mt: 1, fontSize: '0.75rem' }}>
          Blue = Cold, Red = Hot, White = No Data
        </Typography>
      </Box>
    </Box>
  );
};

export default ResizableWeatherDataMap;
