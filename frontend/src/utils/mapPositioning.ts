import { geoToSvg } from './coordinateTransform';

/**
 * Centralized coordinate system for positioning elements on the map
 * Uses the same transformation logic as the weather data grid
 */

export interface MapPosition {
  x: number;
  y: number;
  lat?: number;
  lon?: number;
  name?: string;
}

export interface GeographicLocation {
  lat: number;
  lon: number;
  name?: string;
}

/**
 * Convert geographic coordinates to map pixel coordinates
 * Uses the same transformation system as the weather data grid
 * @param lat - Latitude
 * @param lon - Longitude
 * @returns MapPosition with x, y coordinates
 */
export function positionOnMap(lat: number, lon: number): MapPosition {
  const svgCoords = geoToSvg(lat, lon);
  return {
    x: svgCoords.x,
    y: svgCoords.y,
    lat,
    lon
  };
}

/**
 * Position multiple geographic locations on the map
 * @param locations - Array of geographic locations
 * @returns Array of MapPosition objects
 */
export function positionMultipleOnMap(locations: GeographicLocation[]): MapPosition[] {
  return locations.map(location => ({
    ...positionOnMap(location.lat, location.lon),
    name: location.name
  }));
}

/**
 * Helper function to create a map position from coordinates
 * @param lat - Latitude
 * @param lon - Longitude
 * @param name - Optional name for the location
 * @returns MapPosition object
 */
export function createMapPosition(lat: number, lon: number, name?: string): MapPosition {
  return {
    ...positionOnMap(lat, lon),
    name
  };
}

/**
 * Common Canadian cities with their coordinates for easy positioning
 */
export const CANADIAN_CITIES = {
  // Western Canada
  VANCOUVER: { lat: 49.2827, lon: -123.1207, name: "Vancouver" },
  CALGARY: { lat: 51.0447, lon: -114.0719, name: "Calgary" },
  EDMONTON: { lat: 53.5461, lon: -113.4938, name: "Edmonton" },
  WINNIPEG: { lat: 49.895, lon: -97.138, name: "Winnipeg" },
  WHITEHORSE: { lat: 60.7212, lon: -135.0568, name: "Whitehorse" },
  PRINCE_RUPERT: { lat: 54.3, lon: -130.3, name: "Prince Rupert" },
  VICTORIA: { lat: 48.4284, lon: -123.3656, name: "Victoria" },
  SASKATOON: { lat: 52.1579, lon: -106.6702, name: "Saskatoon" },
  REGINA: { lat: 50.4452, lon: -104.6189, name: "Regina" },
  
  // Central Canada
  TORONTO: { lat: 43.7, lon: -79.4, name: "Toronto" },
  MONTREAL: { lat: 45.502, lon: -73.567, name: "Montreal" },
  OTTAWA: { lat: 45.4215, lon: -75.6972, name: "Ottawa" },
  QUEBEC_CITY: { lat: 46.8139, lon: -71.2080, name: "Quebec City" },
  THUNDER_BAY: { lat: 48.3809, lon: -89.2477, name: "Thunder Bay" },
  WINDSOR: { lat: 42.3149, lon: -83.0364, name: "Windsor" },
  HAMILTON: { lat: 43.2557, lon: -79.8711, name: "Hamilton" },
  LONDON: { lat: 42.9849, lon: -81.2453, name: "London" },
  KITCHENER: { lat: 43.4501, lon: -80.4829, name: "Kitchener" },
  OSHAWA: { lat: 43.8971, lon: -78.8658, name: "Oshawa" },
  
  // Eastern Canada
  HALIFAX: { lat: 44.6488, lon: -63.5752, name: "Halifax" },
  ST_JOHNS: { lat: 47.5615, lon: -52.7126, name: "St. John's" },
  FREDERICTON: { lat: 45.9636, lon: -66.6431, name: "Fredericton" },
  CHARLOTTETOWN: { lat: 46.2382, lon: -63.1311, name: "Charlottetown" },
  
  // Northern Canada
  YELLOWKNIFE: { lat: 62.454, lon: -114.372, name: "Yellowknife" },
  INUVIK: { lat: 68.3607, lon: -133.723, name: "Inuvik" },
  TUKTOYAKTUK: { lat: 69.4, lon: -133, name: "Tuktoyaktuk" },
  CHURCHILL: { lat: 58.768, lon: -94.17, name: "Churchill" },
  IQALUIT: { lat: 63.7467, lon: -68.517, name: "Iqaluit" },
  RESOLUTE: { lat: 74.7, lon: -94.8, name: "Resolute" },
  ALERT: { lat: 82.5018, lon: -62.3481, name: "Alert" },
  CAPE_COLUMBIA: { lat: 83.111, lon: -69.958, name: "Cape Columbia" }
} as const;

/**
 * Get all Canadian cities positioned on the map
 * @returns Array of MapPosition objects for all cities
 */
export function getAllCanadianCities(): MapPosition[] {
  return Object.values(CANADIAN_CITIES).map(city => ({
    ...positionOnMap(city.lat, city.lon),
    name: city.name
  }));
}

/**
 * Get specific cities positioned on the map
 * @param cityKeys - Array of city keys from CANADIAN_CITIES
 * @returns Array of MapPosition objects for specified cities
 */
export function getCitiesOnMap(cityKeys: (keyof typeof CANADIAN_CITIES)[]): MapPosition[] {
  return cityKeys.map(key => {
    const city = CANADIAN_CITIES[key];
    return positionOnMap(city.lat, city.lon);
  });
}
