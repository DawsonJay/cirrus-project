import React from 'react';

interface TestOverlayProps {
  className?: string;
  zIndex?: number;
}

/**
 * TestOverlay - Simple test overlay to verify the overlay system is working
 */
export const TestOverlay: React.FC<TestOverlayProps> = ({
  className = '',
  zIndex = 15
}) => {
  return (
    <svg 
      className={className} 
      width="100%" 
      height="100%" 
      viewBox="0 0 800 600"
      preserveAspectRatio="xMidYMid meet"
      style={{ zIndex }}
    >
      {/* Test points at known locations */}
      <circle cx={100} cy={100} r={10} fill="#00ff00" stroke="#ffffff" strokeWidth={2} />
      <text x={120} y={105} fill="#ffffff" fontSize="14" fontFamily="Arial, sans-serif">
        Test Point 1
      </text>
      
      <circle cx={700} cy={500} r={10} fill="#00ff00" stroke="#ffffff" strokeWidth={2} />
      <text x={720} y={505} fill="#ffffff" fontSize="14" fontFamily="Arial, sans-serif">
        Test Point 2
      </text>
      
      <circle cx={400} cy={300} r={10} fill="#00ff00" stroke="#ffffff" strokeWidth={2} />
      <text x={420} y={305} fill="#ffffff" fontSize="14" fontFamily="Arial, sans-serif">
        Test Point 3
      </text>
    </svg>
  );
};

export default TestOverlay;

