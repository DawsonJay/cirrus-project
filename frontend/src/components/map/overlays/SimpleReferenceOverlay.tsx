import React from 'react';

interface SimpleReferenceOverlayProps {
  className?: string;
  zIndex?: number;
}

/**
 * SimpleReferenceOverlay - Minimal reference points for testing
 */
export const SimpleReferenceOverlay: React.FC<SimpleReferenceOverlayProps> = ({
  className = '',
  zIndex = 10
}) => {
  console.log('SimpleReferenceOverlay rendering...');
  
  // Just a few key reference points for testing
  const testPoints = [
    { name: "Vancouver", x: 277, y: 520 },
    { name: "Toronto", x: 482, y: 558 },
    { name: "Montreal", x: 517, y: 544 },
    { name: "Calgary", x: 321, y: 505 },
    { name: "Halifax", x: 556, y: 552 },
    { name: "Alert", x: 564, y: 51 }
  ];

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: zIndex,
        pointerEvents: 'none'
      }}
    >
      <svg 
        className={className} 
        width="100%" 
        height="100%" 
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYMid meet"
        style={{ 
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%'
        }}
      >
        {/* Render test reference points */}
        {testPoints.map((point, index) => (
          <g key={`simple-ref-${point.name}-${index}`}>
            {/* Small red circle */}
            <circle
              cx={point.x}
              cy={point.y}
              r={1}
              fill="#ff0000"
              stroke="#ffffff"
              strokeWidth={0.5}
              opacity={1.0}
            />
            {/* Label */}
            <text
              x={point.x + 5}
              y={point.y - 5}
              fill="#ffffff"
              fontSize="10"
              fontFamily="Arial, sans-serif"
              fontWeight="bold"
              style={{ textShadow: '1px 1px 1px rgba(0,0,0,0.9)' }}
            >
              {point.name}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};

export default SimpleReferenceOverlay;
