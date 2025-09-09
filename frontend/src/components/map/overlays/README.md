# Map Overlay System

This directory contains the composable overlay system for the Canadian Weather AI Prediction System. The overlay system allows you to create multiple visualization layers that can be combined and toggled independently.

## Architecture

### Base Components

- **`BaseOverlay`** - Base component that all overlays extend
- **`OverlayManager`** - Container that manages multiple overlays
- **`OverlayComponentProps`** - TypeScript interface for overlay props

### Overlay Components

- **`TemperatureHeatMapOverlay`** - Renders temperature data as colored areas
- **`WildfireAreasOverlay`** - Shows wildfire-affected regions
- **`AffectedCitiesOverlay`** - Displays cities impacted by weather events
- **`WeatherAlertsOverlay`** - Shows weather warnings and alerts

## Usage

### Basic Overlay

```tsx
import { TemperatureHeatMapOverlay } from './overlays';

<TemperatureHeatMapOverlay
  zIndex={2}
  opacity={0.7}
  visible={true}
  sampleSize={1000}
/>
```

### Multiple Overlays

```tsx
import { OverlayManager, TemperatureHeatMapOverlay, WildfireAreasOverlay } from './overlays';

<OverlayManager>
  <TemperatureHeatMapOverlay zIndex={1} opacity={0.7} />
  <WildfireAreasOverlay zIndex={2} opacity={0.8} />
</OverlayManager>
```

## Creating New Overlays

### 1. Extend BaseOverlay

```tsx
import { BaseOverlay } from '../BaseOverlay';
import { OverlayComponentProps } from '../../../types/overlay';

export const MyCustomOverlay: React.FC<OverlayComponentProps> = ({
  zIndex,
  opacity = 1,
  visible = true,
  className = '',
  // Your custom props
}) => {
  return (
    <BaseOverlay
      zIndex={zIndex}
      opacity={opacity}
      visible={visible}
      className={`my-custom-overlay ${className}`}
    >
      {/* Your overlay content */}
    </BaseOverlay>
  );
};
```

### 2. Use Coordinate System

All overlays should use the centralized coordinate system:

```tsx
import { positionOnMap } from '../../../utils/mapPositioning';

// Convert geographic coordinates to SVG pixels
const position = positionOnMap(lat, lon);
```

### 3. Export from Index

Add your overlay to `index.ts`:

```tsx
export { default as MyCustomOverlay } from './MyCustomOverlay';
```

## Coordinate System

All overlays use the same coordinate transformation system:

- **Geographic coordinates** (lat/lon) → **SVG pixels** (x/y)
- **Consistent positioning** across all overlays
- **Mercator projection** for accurate mapping
- **Reference point calibration** for precise alignment

## Z-Index Management

Overlays are layered using z-index values:

- **1-10**: Base data layers (temperature, humidity, etc.)
- **11-20**: Event overlays (wildfires, storms, etc.)
- **21-30**: City and location markers
- **31-40**: Alerts and warnings
- **41-50**: UI controls and interactions

## Best Practices

### Performance
- Use `sampleSize` prop to limit rendered points
- Implement proper loading states
- Use `pointerEvents: 'none'` for non-interactive overlays

### Styling
- Use consistent color schemes
- Provide opacity controls
- Include proper text shadows for readability

### Data
- Handle missing data gracefully
- Provide fallback values
- Use appropriate data types

## Examples

See `OverlayDemoPage.tsx` for a complete example of how to use the overlay system with controls for toggling and opacity adjustment.
