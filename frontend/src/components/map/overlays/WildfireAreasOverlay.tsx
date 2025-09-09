import React from 'react';
import { BaseOverlay } from '../BaseOverlay';
import { OverlayComponentProps } from '../../../types/overlay';
import { positionOnMap } from '../../../utils/mapPositioning';

/**
 * WildfireAreasOverlay - Renders wildfire areas on the map
 * 
 * This overlay shows areas affected by wildfires. In a real implementation,
 * this would use actual wildfire data from APIs like NASA FIRMS or similar.
 */
export const WildfireAreasOverlay: React.FC<OverlayComponentProps> = ({
  zIndex,
  opacity = 0.8,
  visible = true,
  className = '',
  wildfireData = [] // Mock data for now
}) => {
  // Mock wildfire data - in real implementation, this would come from an API
  const mockWildfireData = [
    {
      id: 'wildfire-1',
      name: 'Northern BC Fire',
      lat: 54.5,
      lon: -125.0,
      severity: 'high',
      area: 50000, // hectares
      confidence: 0.9
    },
    {
      id: 'wildfire-2', 
      name: 'Alberta Fire',
      lat: 52.0,
      lon: -115.0,
      severity: 'medium',
      area: 25000,
      confidence: 0.8
    },
    {
      id: 'wildfire-3',
      name: 'Ontario Fire',
      lat: 48.0,
      lon: -85.0,
      severity: 'low',
      area: 10000,
      confidence: 0.7
    }
  ];

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'high': return '#FF0000'; // Red
      case 'medium': return '#FF8000'; // Orange
      case 'low': return '#FFFF00'; // Yellow
      default: return '#808080'; // Gray
    }
  };

  const getSeverityOpacity = (severity: string): number => {
    switch (severity) {
      case 'high': return 0.9;
      case 'medium': return 0.7;
      case 'low': return 0.5;
      default: return 0.3;
    }
  };

  return (
    <BaseOverlay
      zIndex={zIndex}
      opacity={opacity}
      visible={visible}
      className={`wildfire-areas ${className}`}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYMid meet"
        style={{ pointerEvents: 'none' }}
      >
        {/* Render wildfire areas */}
        {mockWildfireData.map((fire) => {
          const position = positionOnMap(fire.lat, fire.lon);
          const radius = Math.min(Math.max(fire.area / 10000, 5), 20); // Scale radius based on area
          
          return (
            <g key={fire.id}>
              {/* Fire area circle */}
              <circle
                cx={position.x}
                cy={position.y}
                r={radius}
                fill={getSeverityColor(fire.severity)}
                opacity={getSeverityOpacity(fire.severity)}
                stroke="#FFFFFF"
                strokeWidth="1"
              />
              {/* Fire label */}
              <text
                x={position.x}
                y={position.y - radius - 5}
                fill="#FFFFFF"
                fontSize="10"
                fontWeight="600"
                textAnchor="middle"
                style={{ 
                  textShadow: '1px 1px 2px rgba(0,0,0,0.8)',
                  pointerEvents: 'none'
                }}
              >
                {fire.name}
              </text>
            </g>
          );
        })}
      </svg>
    </BaseOverlay>
  );
};

export default WildfireAreasOverlay;
