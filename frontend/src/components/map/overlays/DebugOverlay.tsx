import React from 'react';

interface DebugOverlayProps {
  className?: string;
  zIndex?: number;
}

/**
 * DebugOverlay - Ultra-simple overlay to test if overlays work at all
 */
export const DebugOverlay: React.FC<DebugOverlayProps> = ({
  className = '',
  zIndex = 20
}) => {
  console.log('DebugOverlay rendering...');
  
  return (
    <div
      style={{
        position: 'absolute',
        top: 10,
        left: 10,
        zIndex: zIndex,
        backgroundColor: 'red',
        color: 'white',
        padding: '10px',
        fontSize: '16px',
        fontWeight: 'bold'
      }}
    >
      DEBUG OVERLAY TEST
    </div>
  );
};

export default DebugOverlay;

