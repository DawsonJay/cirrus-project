import React from 'react';
import { useGridData } from '../../contexts/GridDataContext';

interface GridOverlayProps {
  sampleSize?: number;
  showTemperature?: boolean;
  showHumidity?: boolean;
  showPressure?: boolean;
  showWindSpeed?: boolean;
  showPrecipitation?: boolean;
  showVisibility?: boolean;
  showCloudCover?: boolean;
  showUvIndex?: boolean;
  pointSize?: number;
  className?: string;
  zIndex?: number;
}

/**
 * Converts temperature to color for visualization
 * @param temperature - Temperature in Celsius
 * @returns CSS color string
 */
const getTemperatureColor = (temperature?: number): string => {
  if (temperature === undefined || temperature === null) {
    return '#ffffff'; // White for unknown
  }

  // Temperature range: -70°C to 40°C
  const minTemp = -70;
  const maxTemp = 40;
  
  // Clamp temperature to range
  const clampedTemp = Math.max(minTemp, Math.min(maxTemp, temperature));
  
  // Normalize to 0-1 range
  const normalized = (clampedTemp - minTemp) / (maxTemp - minTemp);
  
  // Create color gradient from blue (cold) to red (hot)
  if (normalized < 0.5) {
    // Blue to white (cold to moderate)
    const intensity = normalized * 2;
    const blue = Math.round(255 * (1 - intensity));
    const green = Math.round(255 * intensity);
    return `rgb(${255 - blue}, ${green}, 255)`;
  } else {
    // White to red (moderate to hot)
    const intensity = (normalized - 0.5) * 2;
    const red = 255;
    const green = Math.round(255 * (1 - intensity));
    const blue = Math.round(255 * (1 - intensity));
    return `rgb(${red}, ${green}, ${blue})`;
  }
};

/**
 * Converts humidity to color for visualization
 * @param humidity - Humidity percentage (0-100)
 * @returns CSS color string
 */
const getHumidityColor = (humidity?: number): string => {
  if (humidity === undefined || humidity === null) {
    return '#ffffff'; // White for unknown
  }

  // Humidity range: 0% to 100%
  const normalized = Math.max(0, Math.min(100, humidity)) / 100;
  
  // Create color gradient from light blue (dry) to dark blue (humid)
  const blue = Math.round(100 + (155 * normalized));
  return `rgb(0, 100, ${blue})`;
};

/**
 * Converts pressure to color for visualization
 * @param pressure - Pressure in hPa
 * @returns CSS color string
 */
const getPressureColor = (pressure?: number): string => {
  if (pressure === undefined || pressure === null) {
    return '#ffffff'; // White for unknown
  }

  // Pressure range: 950 hPa to 1050 hPa
  const minPressure = 950;
  const maxPressure = 1050;
  const normalized = Math.max(0, Math.min(1, (pressure - minPressure) / (maxPressure - minPressure)));
  
  // Create color gradient from purple (low) to yellow (high)
  const red = Math.round(128 + (127 * normalized));
  const green = Math.round(128 * normalized);
  const blue = Math.round(255 - (127 * normalized));
  return `rgb(${red}, ${green}, ${blue})`;
};

/**
 * Converts wind speed to color for visualization
 * @param windSpeed - Wind speed in km/h
 * @returns CSS color string
 */
const getWindSpeedColor = (windSpeed?: number): string => {
  if (windSpeed === undefined || windSpeed === null) {
    return '#ffffff'; // White for unknown
  }

  // Wind speed range: 0 km/h to 100 km/h
  const normalized = Math.max(0, Math.min(100, windSpeed)) / 100;
  
  // Create color gradient from green (calm) to red (windy)
  const red = Math.round(255 * normalized);
  const green = Math.round(255 * (1 - normalized));
  return `rgb(${red}, ${green}, 0)`;
};

/**
 * Converts precipitation to color for visualization
 * @param precipitation - Precipitation in mm
 * @returns CSS color string
 */
const getPrecipitationColor = (precipitation?: number): string => {
  if (precipitation === undefined || precipitation === null) {
    return '#ffffff'; // White for unknown
  }

  // Precipitation range: 0 mm to 50 mm
  const normalized = Math.max(0, Math.min(50, precipitation)) / 50;
  
  // Create color gradient from light blue (no rain) to dark blue (heavy rain)
  const blue = Math.round(200 + (55 * normalized));
  return `rgb(0, 0, ${blue})`;
};

/**
 * Gets the appropriate color based on the selected visualization mode
 * @param point - Grid point with weather data
 * @param props - GridOverlay props
 * @returns CSS color string
 */
const getPointColor = (point: any, props: GridOverlayProps): string => {
  if (props.showTemperature) return getTemperatureColor(point.temperature);
  if (props.showHumidity) return getHumidityColor(point.humidity);
  if (props.showPressure) return getPressureColor(point.pressure);
  if (props.showWindSpeed) return getWindSpeedColor(point.windSpeed);
  if (props.showPrecipitation) return getPrecipitationColor(point.precipitation);
  
  // Default to temperature
  return getTemperatureColor(point.temperature);
};

/**
 * GridOverlay component that renders weather data points on the map
 * @param props - Component props
 * @returns JSX element
 */
export const GridOverlay: React.FC<GridOverlayProps> = ({
  sampleSize = 1000,
  showTemperature = true,
  showHumidity = false,
  showPressure = false,
  showWindSpeed = false,
  showPrecipitation = false,
  showVisibility = false,
  showCloudCover = false,
  showUvIndex = false,
  pointSize = 1,
  className = '',
  zIndex = 1
}) => {
  const { gridData, isLoading, error } = useGridData();

  // Show loading state
  if (isLoading) {
    return (
      <svg className={className} width="800" height="600">
        <text x="400" y="300" textAnchor="middle" fill="#666">
          Loading weather data...
        </text>
      </svg>
    );
  }

  // Show error state
  if (error) {
    return (
      <svg className={className} width="800" height="600">
        <text x="400" y="300" textAnchor="middle" fill="#ff0000">
          Error: {error}
        </text>
      </svg>
    );
  }

  // Sample the grid data based on sampleSize
  const displayPoints = gridData.slice(0, sampleSize);

  return (
    <svg 
      className={className} 
      width="100%" 
      height="100%" 
      viewBox="0 0 800 600"
      preserveAspectRatio="xMidYMid meet"
    >
      {/* Render weather data points */}
      {displayPoints.map((point, index) => (
        <circle
          key={`${point.lat}-${point.lon}-${index}`}
          cx={point.svgX}
          cy={point.svgY}
          r={pointSize}
          fill={getPointColor(point, {
            showTemperature,
            showHumidity,
            showPressure,
            showWindSpeed,
            showPrecipitation,
            showVisibility,
            showCloudCover,
            showUvIndex
          })}
          opacity={0.8}
        />
      ))}
    </svg>
  );
};

export default GridOverlay;
