/**
 * Examples of how to use the centralized map positioning system
 * This file demonstrates various ways to position elements on the map
 */

import { 
  positionOnMap, 
  positionMultipleOnMap, 
  createMapPosition,
  getAllCanadianCities,
  getCitiesOnMap,
  CANADIAN_CITIES,
  MapPosition,
  GeographicLocation
} from './mapPositioning';

// Example 1: Position a single location
export function positionSingleLocation() {
  // Position Alert using its coordinates
  const alertPosition = positionOnMap(82.5018, -62.3481);
  console.log('Alert position:', alertPosition);
  // Output: { x: 564, y: 51, lat: 82.5018, lon: -62.3481 }
}

// Example 2: Position multiple custom locations
export function positionCustomLocations() {
  const customLocations: GeographicLocation[] = [
    { lat: 45.5017, lon: -73.5673, name: "Montreal Downtown" },
    { lat: 43.6532, lon: -79.3832, name: "Toronto Downtown" },
    { lat: 49.2827, lon: -123.1207, name: "Vancouver Downtown" }
  ];
  
  const positions = positionMultipleOnMap(customLocations);
  console.log('Custom locations:', positions);
}

// Example 3: Use predefined cities
export function usePredefinedCities() {
  // Get all Canadian cities
  const allCities = getAllCanadianCities();
  console.log('All cities count:', allCities.length);
  
  // Get specific cities
  const majorCities = getCitiesOnMap([
    'TORONTO', 
    'MONTREAL', 
    'VANCOUVER', 
    'CALGARY', 
    'HALIFAX'
  ]);
  console.log('Major cities:', majorCities);
}

// Example 4: Create a custom map element
export function createCustomMapElement() {
  // Position a weather station
  const weatherStation = createMapPosition(50.0, -100.0, "Weather Station Alpha");
  console.log('Weather station:', weatherStation);
  
  // Position a custom marker
  const customMarker = positionOnMap(60.0, -110.0);
  console.log('Custom marker:', customMarker);
}

// Example 5: Use in a React component
export function useInReactComponent() {
  // This would be used in a React component like this:
  /*
  const MyMapComponent = () => {
    const cityPositions = getAllCanadianCities();
    
    return (
      <svg viewBox="0 0 800 600">
        {cityPositions.map((city, index) => (
          <circle
            key={index}
            cx={city.x}
            cy={city.y}
            r="5"
            fill="blue"
          />
        ))}
      </svg>
    );
  };
  */
}

// Example 6: Position elements for different map features
export function positionMapFeatures() {
  // Position reference points for calibration
  const referencePoints = [
    { lat: 83.111, lon: -69.958, name: "Cape Columbia" },
    { lat: 42.3149, lon: -83.0364, name: "Windsor" },
    { lat: 49.2827, lon: -123.1207, name: "Vancouver" }
  ];
  
  const positions = positionMultipleOnMap(referencePoints);
  console.log('Reference points:', positions);
  
  // Position weather data points (if you have coordinates)
  const weatherData = [
    { lat: 45.0, lon: -75.0 },
    { lat: 50.0, lon: -100.0 },
    { lat: 55.0, lon: -125.0 }
  ];
  
  const weatherPositions = positionMultipleOnMap(weatherData);
  console.log('Weather data positions:', weatherPositions);
}

// Example 7: Validate coordinates before positioning
export function validateAndPosition(lat: number, lon: number, name?: string): MapPosition | null {
  // Basic validation
  if (lat < -90 || lat > 90) {
    console.error('Invalid latitude:', lat);
    return null;
  }
  
  if (lon < -180 || lon > 180) {
    console.error('Invalid longitude:', lon);
    return null;
  }
  
  // Position if valid
  return createMapPosition(lat, lon, name);
}
