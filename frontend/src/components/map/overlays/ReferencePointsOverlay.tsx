import React from 'react';
import { normalizedReferencePoints } from '../../../utils/coordinateTransform';

interface ReferencePointsOverlayProps {
  className?: string;
  zIndex?: number;
}

/**
 * ReferencePointsOverlay - Shows the calibrated reference points for debugging alignment
 * This overlay helps verify that the coordinate transformation is working correctly
 */
export const ReferencePointsOverlay: React.FC<ReferencePointsOverlayProps> = ({
  className = '',
  zIndex = 10
}) => {
  // Get reference points safely
  const referencePoints = React.useMemo(() => {
    try {
      return Object.values(normalizedReferencePoints);
    } catch (error) {
      console.error('Error getting reference points:', error);
      return [];
    }
  }, []);

  // Don't render if no reference points
  if (referencePoints.length === 0) {
    return null;
  }

  return (
    <svg 
      className={className} 
      width="100%" 
      height="100%" 
      viewBox="0 0 800 600"
      preserveAspectRatio="xMidYMid meet"
      style={{ zIndex }}
    >
      {/* Render reference points as larger, colored circles */}
      {referencePoints.map((point, index) => (
        <g key={`ref-${point.name}-${index}`}>
          {/* Outer ring for visibility */}
          <circle
            cx={point.x}
            cy={point.y}
            r={8}
            fill="none"
            stroke="#ff0000"
            strokeWidth={2}
            opacity={1.0}
          />
          {/* Main reference point */}
          <circle
            cx={point.x}
            cy={point.y}
            r={5}
            fill="#ff0000"
            stroke="#ffffff"
            strokeWidth={2}
            opacity={1.0}
          />
          {/* Label */}
          <text
            x={point.x + 12}
            y={point.y - 8}
            fill="#ffffff"
            fontSize="12"
            fontFamily="Arial, sans-serif"
            fontWeight="bold"
            style={{ textShadow: '2px 2px 2px rgba(0,0,0,0.9)' }}
          >
            {point.name}
          </text>
          {/* Coordinate info */}
          <text
            x={point.x + 12}
            y={point.y + 6}
            fill="#ffff00"
            fontSize="10"
            fontFamily="Arial, sans-serif"
            fontWeight="bold"
            style={{ textShadow: '2px 2px 2px rgba(0,0,0,0.9)' }}
          >
            {point.lat.toFixed(1)}, {point.lon.toFixed(1)}
          </text>
        </g>
      ))}
    </svg>
  );
};

export default ReferencePointsOverlay;
