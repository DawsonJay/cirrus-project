import React from 'react';
import { OverlayManagerProps } from '../../types/overlay';

/**
 * OverlayManager - Manages the layering and rendering of map overlays
 * 
 * This component provides a container for multiple overlay components,
 * ensuring they are properly layered and positioned relative to the map.
 * Each overlay should use the same coordinate system for consistent positioning.
 */
export const OverlayManager: React.FC<OverlayManagerProps> = ({
  children,
  className = ''
}) => {
  return (
    <div 
      className={`overlay-manager ${className}`}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none', // Allow clicks to pass through to map
        zIndex: 1
      }}
    >
      {children}
    </div>
  );
};

export default OverlayManager;
