import React from 'react';
import { BaseOverlay } from '../BaseOverlay';
import { OverlayComponentProps } from '../../../types/overlay';
import { useGridData } from '../../../contexts/GridDataContext';
import { transformGridToSvg } from '../../../utils/coordinateTransform';

/**
 * TemperatureHeatMapOverlay - Renders temperature data as a heat map
 * 
 * This overlay visualizes temperature data from the grid as colored areas
 * rather than individual dots. Uses the same coordinate system as other overlays.
 */
export const TemperatureHeatMapOverlay: React.FC<OverlayComponentProps> = ({
  zIndex,
  opacity = 0.7,
  visible = true,
  className = '',
  sampleSize = 1000 // How many points to show
}) => {
  const { gridData, isLoading, error } = useGridData();

  if (isLoading || error || !gridData) {
    return null;
  }

  // Get temperature color based on value
  const getTemperatureColor = (temp: number): string => {
    if (temp < -20) return '#000080'; // Dark blue
    if (temp < -10) return '#0000FF'; // Blue
    if (temp < 0) return '#00FFFF';   // Cyan
    if (temp < 10) return '#00FF00';  // Green
    if (temp < 20) return '#FFFF00';  // Yellow
    if (temp < 30) return '#FF8000';  // Orange
    return '#FF0000'; // Red
  };

  // Use grid data that already has SVG coordinates
  const svgPoints = gridData.slice(0, sampleSize);
  
  // Debug: Log any points with invalid coordinates
  const invalidPoints = svgPoints.filter(point => 
    point.svgX == null || 
    point.svgY == null || 
    isNaN(point.svgX) || 
    isNaN(point.svgY)
  );
  
  if (invalidPoints.length > 0) {
    console.warn(`TemperatureHeatMapOverlay: Found ${invalidPoints.length} points with invalid coordinates:`, invalidPoints.slice(0, 5));
  }

  return (
    <BaseOverlay
      zIndex={zIndex}
      opacity={opacity}
      visible={visible}
      className={`temperature-heat-map ${className}`}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYMid meet"
        style={{ pointerEvents: 'none' }}
      >
        {/* Render temperature points as colored circles */}
        {svgPoints
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
          .map((point, index) => (
            <circle
              key={`temp-${index}`}
              cx={point.svgX}
              cy={point.svgY}
              r="3"
              fill={getTemperatureColor(point.temperature || 0)}
              opacity="0.8"
            />
          ))}
      </svg>
    </BaseOverlay>
  );
};

export default TemperatureHeatMapOverlay;
