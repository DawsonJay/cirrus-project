// Coordinate transformation utilities for mapping geographic coordinates to SVG pixels
// Uses Mercator projection and reference point calibration for accurate mapping

// Import reference points from separate file to prevent corruption
import { normalizedReferencePoints } from './referencePoints';

export interface ReferencePoint {
  x: number; // Normalized x coordinate (0-1)
  y: number; // Normalized y coordinate (0-1)
  name: string;
  lat: number;
  lon: number;
}

export interface GridPoint {
  // Geographic data
  lat: number;
  lon: number;
  
  // SVG pixel coordinates (calculated once)
  svgX: number;
  svgY: number;
  
  // Weather data (new schema v2 format)
  temperature_2m?: number;
  relative_humidity_2m?: number;
  precipitation?: number;
  wind_speed_10m?: number;
  pressure_msl?: number;
  cape?: number;
  cin?: number;
  date_slice?: string;
  timestamp_utc?: string;
  
  // Legacy fields for backward compatibility
  temperature?: number;
  humidity?: number;
  pressure?: number;
  windSpeed?: number;
  windDirection?: number;
  visibility?: number;
  cloudCover?: number;
  uvIndex?: number;
}

// Re-export for backward compatibility
export { normalizedReferencePoints };


// SVG viewbox dimensions
export const SVG_VIEWBOX = {
  width: 800,
  height: 600
};

/**
 * Returns reference points with pixel coordinates (already in pixel format)
 * @param referencePoints - Reference points with pixel coordinates
 * @returns Reference points with pixel coordinates
 */
export const getScaledReferencePoints = (referencePoints: Record<string, ReferencePoint>) => {
  return referencePoints; // Already in pixel coordinates
};

/**
 * Converts geographic coordinates (lat/lon) to SVG pixel coordinates
 * Uses Mercator projection and reference point calibration for accuracy
 * @param lat - Latitude in degrees
 * @param lon - Longitude in degrees
 * @returns SVG pixel coordinates {x, y}
 */
export const geoToSvg = (lat: number, lon: number): { x: number; y: number } => {
  // Validate input coordinates
  if (lat == null || lon == null || isNaN(lat) || isNaN(lon)) {
    console.warn(`geoToSvg: Invalid coordinates - lat: ${lat}, lon: ${lon}`);
    return { x: 0, y: 0 };
  }
  
  // Clamp coordinates to reasonable ranges
  const clampedLat = Math.max(-90, Math.min(90, lat));
  const clampedLon = Math.max(-180, Math.min(180, lon));
  
  const scaledPoints = getScaledReferencePoints(normalizedReferencePoints);
  const points = Object.values(scaledPoints);
  
  // Find the four extreme reference points
  const northPoint = points.find(p => p.name === "Cape Columbia")!;
  const southPoint = points.find(p => p.name === "Windsor")!;
  const eastPoint = points.find(p => p.name === "Cape Spear")!;
  const westPoint = points.find(p => p.name === "Vancouver")!;
  
  // Convert to radians
  const latRad = (clampedLat * Math.PI) / 180;
  const lonRad = (clampedLon * Math.PI) / 180;
  const northLatRad = (northPoint.lat * Math.PI) / 180;
  const southLatRad = (southPoint.lat * Math.PI) / 180;
  const eastLonRad = (eastPoint.lon * Math.PI) / 180;
  const westLonRad = (westPoint.lon * Math.PI) / 180;
  
  // Apply Mercator projection for latitude
  const mercatorLat = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
  const mercatorNorthLat = Math.log(Math.tan(Math.PI / 4 + northLatRad / 2));
  const mercatorSouthLat = Math.log(Math.tan(Math.PI / 4 + southLatRad / 2));
  
  // Calculate percentages within the reference bounds
  const latPercent = (mercatorLat - mercatorSouthLat) / (mercatorNorthLat - mercatorSouthLat);
  const lonPercent = (lonRad - westLonRad) / (eastLonRad - westLonRad);
  
  // Convert to SVG coordinates
  const x = westPoint.x + (lonPercent * (eastPoint.x - westPoint.x));
  const y = southPoint.y - (latPercent * (southPoint.y - northPoint.y));
  
  // Validate output coordinates
  if (isNaN(x) || isNaN(y)) {
    console.warn(`geoToSvg: Result is NaN - lat: ${lat}, lon: ${lon}, x: ${x}, y: ${y}`);
    return { x: 0, y: 0 };
  }
  
  return { x, y };
};

/**
 * Transforms a grid point from geographic coordinates to SVG coordinates
 * @param point - Grid point with lat/lon coordinates
 * @returns Grid point with SVG coordinates added
 */
export const transformGridPointToSvg = (point: Omit<GridPoint, 'svgX' | 'svgY'>): GridPoint => {
  const svgCoords = geoToSvg(point.lat, point.lon);
  return {
    ...point,
    svgX: svgCoords.x,
    svgY: svgCoords.y
  };
};

/**
 * Transforms an array of grid points from geographic coordinates to SVG coordinates
 * @param points - Array of grid points with lat/lon coordinates
 * @returns Array of grid points with SVG coordinates added
 */
export const transformGridToSvg = (points: any[]): GridPoint[] => {
  return points
    .filter(point => 
      point && 
      point.latitude != null && 
      point.longitude != null && 
      !isNaN(point.latitude) && 
      !isNaN(point.longitude)
    )
    .map(point => {
      // Handle new weather data service format: { id, latitude, longitude, region, temperature_2m, relative_humidity_2m, ... }
      const gridPoint: Omit<GridPoint, 'svgX' | 'svgY'> = {
        lat: point.latitude,
        lon: point.longitude,
        
        // New schema v2 fields
        temperature_2m: point.temperature_2m,
        relative_humidity_2m: point.relative_humidity_2m,
        precipitation: point.precipitation,
        wind_speed_10m: point.wind_speed_10m,
        pressure_msl: point.pressure_msl,
        cape: point.cape,
        cin: point.cin,
        date_slice: point.date_slice,
        timestamp_utc: point.timestamp_utc,
        
        // Legacy fields for backward compatibility
        temperature: point.temperature_2m || point.temperature,
        humidity: point.relative_humidity_2m || point.humidity,
        pressure: point.pressure_msl || point.pressure,
        windSpeed: point.wind_speed_10m || point.wind_speed,
        windDirection: point.wind_direction,
        visibility: point.visibility,
        cloudCover: point.cloud_cover,
        uvIndex: point.uv_index
      };
      
      return transformGridPointToSvg(gridPoint);
    })
    .filter(point => 
      point.svgX != null && 
      point.svgY != null && 
      !isNaN(point.svgX) && 
      !isNaN(point.svgY)
    );
};
