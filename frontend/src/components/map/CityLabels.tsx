import React from 'react';
import { getAllCanadianCities, MapPosition } from '../../utils/mapPositioning';

interface CityLabelsProps {
  className?: string;
}

/**
 * CityLabels component that renders major Canadian cities on the map
 * These are independent test markers to verify map alignment
 * @param props - Component props
 * @returns JSX element
 */
export const CityLabels: React.FC<CityLabelsProps> = ({
  className = ''
}) => {
  // Get all Canadian cities positioned using the centralized coordinate system
  const majorCities: MapPosition[] = getAllCanadianCities();

  return (
    <svg 
      className={className} 
      width="100%" 
      height="100%" 
      viewBox="0 0 800 600"
      preserveAspectRatio="xMidYMid meet"
      style={{ pointerEvents: 'none' }}
    >
            {/* Render city labels */}
            {majorCities.map((city, index) => (
              <g key={`city-${city.name || index}-${index}`}>
                {/* City dot */}
                <circle
                  cx={city.x}
                  cy={city.y}
                  r="3"
                  fill="#00bcd4"
                  opacity="0.9"
                  stroke="#ffffff"
                  strokeWidth="1"
                />
                {/* City label */}
                <text
                  x={city.x + 5}
                  y={city.y - 5}
                  fill="#ffffff"
                  fontSize="9"
                  fontWeight="600"
                  style={{ 
                    textShadow: '1px 1px 2px rgba(0,0,0,0.8)',
                    pointerEvents: 'none'
                  }}
                >
                  {city.name || `City ${index + 1}`}
                </text>
              </g>
            ))}
    </svg>
  );
};

export default CityLabels;
