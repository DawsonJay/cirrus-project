# Map Positioning System

A centralized coordinate system for positioning elements on the Canadian weather map. This system ensures all map elements use the same transformation logic as the weather data grid.

## Overview

The map positioning system provides a consistent way to convert geographic coordinates (latitude/longitude) to SVG pixel coordinates on the map. It uses the same Mercator projection and reference point calibration as the weather data grid.

## Key Features

- **Consistent positioning** - All map elements use the same coordinate transformation
- **Centralized logic** - Single source of truth for coordinate conversion
- **Predefined cities** - Common Canadian cities with accurate coordinates
- **Type safety** - Full TypeScript support with proper interfaces
- **Easy to use** - Simple functions for common positioning tasks

## Core Functions

### `positionOnMap(lat: number, lon: number): MapPosition`
Convert geographic coordinates to map pixel coordinates.

```typescript
const alertPosition = positionOnMap(82.5018, -62.3481);
// Returns: { x: 564, y: 51, lat: 82.5018, lon: -62.3481 }
```

### `positionMultipleOnMap(locations: GeographicLocation[]): MapPosition[]`
Position multiple locations at once.

```typescript
const locations = [
  { lat: 45.5017, lon: -73.5673, name: "Montreal" },
  { lat: 43.6532, lon: -79.3832, name: "Toronto" }
];
const positions = positionMultipleOnMap(locations);
```

### `createMapPosition(lat: number, lon: number, name?: string): MapPosition`
Create a map position with optional name.

```typescript
const weatherStation = createMapPosition(50.0, -100.0, "Station Alpha");
```

## Predefined Cities

### `getAllCanadianCities(): MapPosition[]`
Get all Canadian cities positioned on the map.

### `getCitiesOnMap(cityKeys: string[]): MapPosition[]`
Get specific cities by their keys.

```typescript
const majorCities = getCitiesOnMap(['TORONTO', 'MONTREAL', 'VANCOUVER']);
```

### Available City Keys
- `VANCOUVER`, `CALGARY`, `EDMONTON`, `WINNIPEG`
- `TORONTO`, `MONTREAL`, `OTTAWA`, `QUEBEC_CITY`
- `HALIFAX`, `ST_JOHNS`, `FREDERICTON`, `CHARLOTTETOWN`
- `YELLOWKNIFE`, `INUVIK`, `TUKTOYAKTUK`, `CHURCHILL`
- `IQALUIT`, `RESOLUTE`, `ALERT`, `CAPE_COLUMBIA`
- And many more...

## Usage Examples

### Basic Positioning
```typescript
import { positionOnMap } from '../utils/mapPositioning';

// Position a single location
const position = positionOnMap(45.5017, -73.5673);
console.log(`X: ${position.x}, Y: ${position.y}`);
```

### React Component
```typescript
import { getAllCanadianCities } from '../utils/mapPositioning';

const MyMapComponent = () => {
  const cities = getAllCanadianCities();
  
  return (
    <svg viewBox="0 0 800 600">
      {cities.map((city, index) => (
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
```

### Custom Locations
```typescript
import { positionMultipleOnMap } from '../utils/mapPositioning';

const customLocations = [
  { lat: 45.0, lon: -75.0, name: "Custom Point 1" },
  { lat: 50.0, lon: -100.0, name: "Custom Point 2" }
];

const positions = positionMultipleOnMap(customLocations);
```

## Coordinate System Details

- **Map dimensions**: 800x600 SVG viewBox
- **Projection**: Mercator projection
- **Reference points**: 23 calibrated reference points
- **Transformation**: Uses `geoToSvg()` from `coordinateTransform.ts`
- **Consistency**: Same system as weather data grid

## Benefits

1. **Consistency** - All map elements use identical positioning logic
2. **Maintainability** - Single place to update coordinate transformation
3. **Accuracy** - Uses the same calibrated reference points as weather data
4. **Type Safety** - Full TypeScript support prevents errors
5. **Reusability** - Easy to use across different components

## Integration

This system is designed to work seamlessly with:
- Weather data grid overlay
- City labels
- Reference point calibration
- Any future map elements

## Future Enhancements

- Support for different map projections
- Dynamic reference point updates
- Coordinate validation and error handling
- Performance optimizations for large datasets
