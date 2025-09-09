import React from 'react';
import { BaseOverlay } from '../BaseOverlay';
import { OverlayComponentProps } from '../../../types/overlay';
import { positionOnMap } from '../../../utils/mapPositioning';

/**
 * AffectedCitiesOverlay - Renders cities affected by weather events
 * 
 * This overlay shows cities that are affected by various weather conditions,
 * with different icons and colors based on the type and severity of impact.
 */
export const AffectedCitiesOverlay: React.FC<OverlayComponentProps> = ({
  zIndex,
  opacity = 1,
  visible = true,
  className = '',
  affectedCities = [] // Mock data for now
}) => {
  // Mock affected cities data - in real implementation, this would come from an API
  const mockAffectedCities = [
    {
      id: 'city-1',
      name: 'Vancouver',
      lat: 49.2827,
      lon: -123.1207,
      impact: 'high',
      eventType: 'wildfire',
      population: 675218
    },
    {
      id: 'city-2',
      name: 'Calgary',
      lat: 51.0447,
      lon: -114.0719,
      impact: 'medium',
      eventType: 'heatwave',
      population: 1306784
    },
    {
      id: 'city-3',
      name: 'Toronto',
      lat: 43.7,
      lon: -79.4,
      impact: 'low',
      eventType: 'storm',
      population: 2930000
    },
    {
      id: 'city-4',
      name: 'Montreal',
      lat: 45.502,
      lon: -73.567,
      impact: 'high',
      eventType: 'flood',
      population: 1780000
    }
  ];

  const getImpactColor = (impact: string): string => {
    switch (impact) {
      case 'high': return '#FF0000'; // Red
      case 'medium': return '#FF8000'; // Orange
      case 'low': return '#FFFF00'; // Yellow
      default: return '#808080'; // Gray
    }
  };

  const getEventIcon = (eventType: string): string => {
    switch (eventType) {
      case 'wildfire': return '🔥';
      case 'heatwave': return '🌡️';
      case 'storm': return '⛈️';
      case 'flood': return '🌊';
      default: return '⚠️';
    }
  };

  const getIconSize = (population: number): number => {
    if (population > 2000000) return 20; // Large cities
    if (population > 1000000) return 16; // Medium cities
    return 12; // Small cities
  };

  return (
    <BaseOverlay
      zIndex={zIndex}
      opacity={opacity}
      visible={visible}
      className={`affected-cities ${className}`}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYMid meet"
        style={{ pointerEvents: 'none' }}
      >
        {/* Render affected cities */}
        {mockAffectedCities.map((city) => {
          const position = positionOnMap(city.lat, city.lon);
          const iconSize = getIconSize(city.population);
          
          return (
            <g key={city.id}>
              {/* City impact circle */}
              <circle
                cx={position.x}
                cy={position.y}
                r={iconSize / 2 + 2}
                fill={getImpactColor(city.impact)}
                opacity="0.3"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              {/* City icon */}
              <text
                x={position.x}
                y={position.y + 4}
                fontSize={iconSize}
                textAnchor="middle"
                style={{ pointerEvents: 'none' }}
              >
                {getEventIcon(city.eventType)}
              </text>
              {/* City label */}
              <text
                x={position.x}
                y={position.y - iconSize / 2 - 8}
                fill="#FFFFFF"
                fontSize="10"
                fontWeight="600"
                textAnchor="middle"
                style={{ 
                  textShadow: '1px 1px 2px rgba(0,0,0,0.8)',
                  pointerEvents: 'none'
                }}
              >
                {city.name}
              </text>
            </g>
          );
        })}
      </svg>
    </BaseOverlay>
  );
};

export default AffectedCitiesOverlay;
