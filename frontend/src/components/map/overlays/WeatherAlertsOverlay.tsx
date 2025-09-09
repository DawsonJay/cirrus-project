import React from 'react';
import { BaseOverlay } from '../BaseOverlay';
import { OverlayComponentProps } from '../../../types/overlay';
import { positionOnMap } from '../../../utils/mapPositioning';

/**
 * WeatherAlertsOverlay - Renders weather alerts and warnings
 * 
 * This overlay shows various weather alerts across Canada, with different
 * symbols and colors based on alert type and severity.
 */
export const WeatherAlertsOverlay: React.FC<OverlayComponentProps> = ({
  zIndex,
  opacity = 0.9,
  visible = true,
  className = '',
  alerts = [] // Mock data for now
}) => {
  // Mock weather alerts data - in real implementation, this would come from Environment Canada API
  const mockAlerts = [
    {
      id: 'alert-1',
      type: 'heat_warning',
      severity: 'high',
      lat: 49.2827,
      lon: -123.1207,
      description: 'Extreme heat warning',
      validUntil: '2025-01-10T18:00:00Z'
    },
    {
      id: 'alert-2',
      type: 'storm_warning',
      severity: 'medium',
      lat: 51.0447,
      lon: -114.0719,
      description: 'Severe thunderstorm warning',
      validUntil: '2025-01-09T22:00:00Z'
    },
    {
      id: 'alert-3',
      type: 'flood_warning',
      severity: 'high',
      lat: 45.502,
      lon: -73.567,
      description: 'Flood warning',
      validUntil: '2025-01-11T12:00:00Z'
    },
    {
      id: 'alert-4',
      type: 'wind_warning',
      severity: 'low',
      lat: 44.6488,
      lon: -63.5752,
      description: 'Strong wind warning',
      validUntil: '2025-01-09T20:00:00Z'
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

  const getAlertIcon = (type: string): string => {
    switch (type) {
      case 'heat_warning': return '🌡️';
      case 'storm_warning': return '⛈️';
      case 'flood_warning': return '🌊';
      case 'wind_warning': return '💨';
      case 'snow_warning': return '❄️';
      default: return '⚠️';
    }
  };

  const getSeveritySize = (severity: string): number => {
    switch (severity) {
      case 'high': return 16;
      case 'medium': return 14;
      case 'low': return 12;
      default: return 10;
    }
  };

  return (
    <BaseOverlay
      zIndex={zIndex}
      opacity={opacity}
      visible={visible}
      className={`weather-alerts ${className}`}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYMid meet"
        style={{ pointerEvents: 'none' }}
      >
        {/* Render weather alerts */}
        {mockAlerts.map((alert) => {
          const position = positionOnMap(alert.lat, alert.lon);
          const iconSize = getSeveritySize(alert.severity);
          
          return (
            <g key={alert.id}>
              {/* Alert background circle */}
              <circle
                cx={position.x}
                cy={position.y}
                r={iconSize / 2 + 3}
                fill={getSeverityColor(alert.severity)}
                opacity="0.2"
                stroke={getSeverityColor(alert.severity)}
                strokeWidth="2"
              />
              {/* Alert icon */}
              <text
                x={position.x}
                y={position.y + 4}
                fontSize={iconSize}
                textAnchor="middle"
                style={{ pointerEvents: 'none' }}
              >
                {getAlertIcon(alert.type)}
              </text>
              {/* Alert label */}
              <text
                x={position.x}
                y={position.y - iconSize / 2 - 8}
                fill="#FFFFFF"
                fontSize="9"
                fontWeight="600"
                textAnchor="middle"
                style={{ 
                  textShadow: '1px 1px 2px rgba(0,0,0,0.8)',
                  pointerEvents: 'none'
                }}
              >
                {alert.severity.toUpperCase()}
              </text>
            </g>
          );
        })}
      </svg>
    </BaseOverlay>
  );
};

export default WeatherAlertsOverlay;
