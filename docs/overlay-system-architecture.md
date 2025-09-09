# Overlay System Architecture

## System Overview

The Map Overlay System provides a composable architecture for rendering multiple visualization layers on the Canadian Weather AI Prediction System map. It ensures consistent positioning, proper layering, and maintainable code organization.

## Core Architecture

### 1. Layered Rendering System

```
┌─────────────────────────────────────┐
│ UI Controls (z-index: 41-50)        │
├─────────────────────────────────────┤
│ Interactive Elements (z-index: 31-40)│
├─────────────────────────────────────┤
│ Geographic Features (z-index: 21-30)│
├─────────────────────────────────────┤
│ Event Overlays (z-index: 11-20)     │
├─────────────────────────────────────┤
│ Base Data Layers (z-index: 1-10)    │
├─────────────────────────────────────┤
│ Canada SVG Map (z-index: 1)         │
└─────────────────────────────────────┘
```

### 2. Component Hierarchy

```
WeatherDataMap
├── Background
├── Canada SVG Map (z-index: 1)
└── OverlayManager
    ├── GridOverlay (z-index: 2)
    ├── TemperatureOverlay (z-index: 3)
    ├── WildfireOverlay (z-index: 4)
    ├── CityOverlay (z-index: 5)
    └── AlertOverlay (z-index: 6)
```

### 3. Data Flow

```
Backend API → GridDataContext → Overlay Components → SVG Rendering
     ↓              ↓                    ↓              ↓
Raw Weather Data → Transformed Data → Filtered Data → Visual Elements
```

## Coordinate System

### Geographic to SVG Transformation

The system uses a two-step coordinate transformation:

1. **Geographic Coordinates** (lat/lon degrees) → **Normalized Coordinates** (0-1 range)
2. **Normalized Coordinates** → **SVG Pixel Coordinates** (0-800 x 0-600)

### Reference Point Calibration

23 strategically placed reference points ensure accurate mapping:

```typescript
interface ReferencePoint {
  x: number;        // SVG pixel x-coordinate
  y: number;        // SVG pixel y-coordinate  
  name: string;     // Human-readable name
  lat: number;      // Geographic latitude
  lon: number;      // Geographic longitude
}
```

### Mercator Projection

Uses Mercator projection for accurate latitude mapping:

```typescript
const mercatorLat = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
```

## Component Design Patterns

### 1. Base Overlay Pattern

All overlays extend `BaseOverlay` for consistency:

```typescript
interface BaseOverlayProps {
  zIndex: number;      // Layer ordering
  opacity?: number;    // Transparency (0-1)
  visible?: boolean;   // Show/hide toggle
  className?: string;  // CSS classes
}
```

### 2. Data Context Pattern

Weather data is provided via React Context:

```typescript
interface GridDataContextType {
  gridData: GridPoint[];     // Transformed data with SVG coordinates
  isLoading: boolean;        // Loading state
  error: string | null;      // Error state
  loadGridData: (sampleSize?: number) => Promise<void>;
  refreshGridData: () => Promise<void>;
}
```

### 3. Composable Overlay Pattern

Overlays are designed to be composable and reusable:

```typescript
interface OverlayComponentProps extends BaseOverlayProps {
  data?: any;           // Overlay-specific data
  sampleSize?: number;  // Performance control
  [key: string]: any;   // Additional props
}
```

## Performance Optimizations

### 1. Data Filtering

Multiple levels of data filtering ensure only valid points are rendered:

```typescript
// Input validation
.filter(point => 
  point.latitude != null && 
  point.longitude != null && 
  !isNaN(point.latitude) && 
  !isNaN(point.longitude)
)

// Output validation  
.filter(point => 
  point.svgX != null && 
  point.svgY != null && 
  !isNaN(point.svgX) && 
  !isNaN(point.svgY) &&
  point.svgX >= 0 && 
  point.svgY >= 0 &&
  point.svgX <= 800 && 
  point.svgY <= 600
)
```

### 2. Sample Size Control

Limit rendered points for performance:

```typescript
const displayPoints = gridData.slice(0, sampleSize);
```

### 3. Memoization

Use React.memo for expensive components:

```typescript
export const MyOverlay = React.memo<OverlayComponentProps>(({ data, ...props }) => {
  // Component implementation
});
```

## Error Handling

### 1. Coordinate Validation

Comprehensive validation at multiple levels:

```typescript
// Input validation
if (lat == null || lon == null || isNaN(lat) || isNaN(lon)) {
  console.warn(`geoToSvg: Invalid coordinates - lat: ${lat}, lon: ${lon}`);
  return { x: 0, y: 0 };
}

// Output validation
if (isNaN(x) || isNaN(y)) {
  console.warn(`geoToSvg: Result is NaN - lat: ${lat}, lon: ${lon}, x: ${x}, y: ${y}`);
  return { x: 0, y: 0 };
}
```

### 2. Graceful Degradation

Handle missing or invalid data gracefully:

```typescript
if (isLoading || error || !gridData) {
  return null; // Don't render anything
}
```

### 3. Debug Logging

Provide detailed logging for troubleshooting:

```typescript
const invalidPoints = svgPoints.filter(point => 
  point.svgX == null || 
  point.svgY == null || 
  isNaN(point.svgX) || 
  isNaN(point.svgY)
);

if (invalidPoints.length > 0) {
  console.warn(`Found ${invalidPoints.length} points with invalid coordinates:`, invalidPoints.slice(0, 5));
}
```

## File Organization

```
frontend/src/components/map/overlays/
├── README.md                           # User documentation
├── index.ts                           # Export all overlays
├── BaseOverlay.tsx                    # Base component
├── OverlayManager.tsx                 # Container component
├── TemperatureHeatMapOverlay.tsx      # Example overlay
├── WildfireAreasOverlay.tsx           # Example overlay
├── AffectedCitiesOverlay.tsx          # Example overlay
└── WeatherAlertsOverlay.tsx           # Example overlay
```

## Type Definitions

```typescript
// Base overlay interface
interface BaseOverlayProps {
  zIndex: number;
  opacity?: number;
  visible?: boolean;
  className?: string;
}

// Overlay component props
interface OverlayComponentProps extends BaseOverlayProps {
  data?: any;
  sampleSize?: number;
  [key: string]: any;
}

// Grid point with SVG coordinates
interface GridPoint {
  lat: number;
  lon: number;
  svgX: number;
  svgY: number;
  temperature?: number;
  humidity?: number;
  // ... other weather properties
}

// Reference point for calibration
interface ReferencePoint {
  x: number;
  y: number;
  name: string;
  lat: number;
  lon: number;
}
```

## Future Enhancements

### 1. Animation System
- Smooth transitions between overlay states
- Animated data updates
- Interactive hover effects

### 2. Advanced Filtering
- Real-time data filtering
- Search and query capabilities
- Custom filter combinations

### 3. Performance Improvements
- WebGL rendering for large datasets
- Virtual scrolling for massive point clouds
- Lazy loading of overlay data

### 4. Interactive Features
- Click handlers for overlay elements
- Tooltip system
- Selection and highlighting

### 5. Export Capabilities
- SVG export of overlay combinations
- PNG/PDF export with overlays
- Data export in various formats

## Testing Strategy

### 1. Unit Tests
- Coordinate transformation accuracy
- Component prop handling
- Error state management

### 2. Integration Tests
- Overlay composition
- Data flow validation
- Performance benchmarks

### 3. Visual Regression Tests
- Overlay positioning accuracy
- Z-index layering verification
- Responsive design validation

## Maintenance Guidelines

### 1. Adding New Overlays
1. Create component extending `BaseOverlay`
2. Use centralized coordinate system
3. Add to exports in `index.ts`
4. Update documentation
5. Add tests

### 2. Modifying Coordinate System
1. Update reference points carefully
2. Test with known geographic locations
3. Verify all overlays still align
4. Update documentation

### 3. Performance Monitoring
1. Monitor render times
2. Track memory usage
3. Validate data filtering effectiveness
4. Optimize based on metrics
