# Map Overlay System Documentation

## Overview

The Map Overlay System is a composable architecture for rendering multiple visualization layers on the Canadian Weather AI Prediction System map. It provides a flexible, maintainable way to combine different data visualizations while ensuring consistent positioning and layering.

## Architecture

### Core Components

#### BaseOverlay
The foundation component that all overlays must extend. Provides common functionality:
- Z-index management
- Opacity control
- Visibility toggling
- Consistent positioning

```tsx
<BaseOverlay zIndex={2} opacity={0.8} visible={true}>
  {/* Your overlay content */}
</BaseOverlay>
```

#### OverlayManager
Container component that manages multiple overlays and ensures proper layering:

```tsx
<OverlayManager>
  <TemperatureOverlay zIndex={1} />
  <WildfireOverlay zIndex={2} />
  <CityOverlay zIndex={3} />
</OverlayManager>
```

### Coordinate System

All overlays use a centralized coordinate transformation system:

#### Geographic to SVG Conversion
- **Input**: Latitude/longitude coordinates (degrees)
- **Output**: SVG pixel coordinates (x, y)
- **Projection**: Mercator projection with reference point calibration
- **Range**: 0-800 pixels (width), 0-600 pixels (height)

#### Usage
```tsx
import { positionOnMap } from '../../../utils/mapPositioning';

const position = positionOnMap(49.2827, -123.1207); // Vancouver
// Returns: { x: 277, y: 520, lat: 49.2827, lon: -123.1207 }
```

#### Reference Points
The system uses 23 strategically placed reference points across Canada for accurate coordinate transformation:
- Cape Columbia (northernmost)
- Windsor (southernmost) 
- Vancouver (westernmost)
- Cape Spear (easternmost)
- Plus 19 additional calibration points

## Creating Custom Overlays

### 1. Basic Overlay Structure

```tsx
import React from 'react';
import { BaseOverlay } from '../BaseOverlay';
import { OverlayComponentProps } from '../../../types/overlay';
import { positionOnMap } from '../../../utils/mapPositioning';

export const MyCustomOverlay: React.FC<OverlayComponentProps> = ({
  zIndex,
  opacity = 1,
  visible = true,
  className = '',
  // Your custom props
  data = []
}) => {
  return (
    <BaseOverlay
      zIndex={zIndex}
      opacity={opacity}
      visible={visible}
      className={`my-custom-overlay ${className}`}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYMid meet"
        style={{ pointerEvents: 'none' }}
      >
        {/* Your overlay content */}
        {data.map((item, index) => {
          const position = positionOnMap(item.lat, item.lon);
          return (
            <circle
              key={index}
              cx={position.x}
              cy={position.y}
              r="5"
              fill="#ff0000"
            />
          );
        })}
      </svg>
    </BaseOverlay>
  );
};
```

### 2. Using Weather Data

For overlays that need weather data, use the GridDataContext:

```tsx
import { useGridData } from '../../../contexts/GridDataContext';

export const WeatherOverlay: React.FC<OverlayComponentProps> = (props) => {
  const { gridData, isLoading, error } = useGridData();
  
  if (isLoading || error || !gridData) {
    return null;
  }
  
  // Use gridData which already has SVG coordinates
  const points = gridData.slice(0, props.sampleSize || 1000);
  
  return (
    <BaseOverlay {...props}>
      {/* Render using points with svgX, svgY properties */}
    </BaseOverlay>
  );
};
```

### 3. Z-Index Guidelines

Follow these z-index ranges for consistent layering:

- **1-10**: Base data layers (temperature, humidity, pressure)
- **11-20**: Event overlays (wildfires, storms, alerts)
- **21-30**: Geographic features (cities, boundaries, labels)
- **31-40**: Interactive elements (controls, tooltips)
- **41-50**: UI overlays (modals, notifications)

### 4. Performance Considerations

#### Data Filtering
Always filter data to only render what's needed:

```tsx
const visiblePoints = points
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
  .slice(0, sampleSize);
```

#### Sample Size
Use the `sampleSize` prop to limit rendered points:

```tsx
<MyOverlay sampleSize={500} /> // Only render 500 points
```

#### Memoization
For expensive calculations, use React.memo or useMemo:

```tsx
const processedData = useMemo(() => {
  return data.map(item => expensiveCalculation(item));
}, [data]);
```

## Integration

### Adding to WeatherDataMap

```tsx
<OverlayManager>
  <GridOverlay zIndex={2} sampleSize={1000} />
  <MyCustomOverlay zIndex={3} data={myData} />
</OverlayManager>
```

### Export from Index

Add your overlay to the index file:

```tsx
// frontend/src/components/map/overlays/index.ts
export { default as MyCustomOverlay } from './MyCustomOverlay';
```

## Best Practices

### 1. Error Handling
- Always validate coordinate data
- Handle loading and error states
- Provide fallback values for missing data

### 2. Accessibility
- Use semantic SVG elements
- Provide alt text for important visual elements
- Ensure sufficient color contrast

### 3. Responsive Design
- Use percentage-based sizing
- Test at different viewport sizes
- Maintain aspect ratio with `preserveAspectRatio`

### 4. Code Organization
- Keep overlays focused on single responsibilities
- Extract reusable utilities
- Use TypeScript for type safety

## Troubleshooting

### Common Issues

#### NaN Coordinates
- Check that input data has valid lat/lon values
- Verify coordinate transformation is working
- Use the validation filters provided

#### Overlay Not Visible
- Check z-index values
- Verify `visible` prop is true
- Ensure opacity is not 0

#### Performance Issues
- Reduce sample size
- Add data filtering
- Use React.memo for expensive components

### Debug Tools

Enable debug logging in coordinate transformation:

```tsx
// Check console for coordinate warnings
console.warn('geoToSvg: Invalid coordinates', lat, lon);
```

## Examples

See the existing overlay components for reference:
- `TemperatureHeatMapOverlay` - Weather data visualization
- `WildfireAreasOverlay` - Event-based overlays
- `AffectedCitiesOverlay` - Geographic markers
- `WeatherAlertsOverlay` - Alert system integration

## Future Enhancements

- Animation support for dynamic data
- Interactive overlay controls
- Real-time data streaming
- Advanced filtering and search
- Export capabilities for overlays