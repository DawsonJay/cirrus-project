import React from 'react';
import { BaseOverlayProps } from '../../types/overlay';

/**
 * BaseOverlay - Base component that all map overlays should extend
 * 
 * Provides common functionality and styling for all overlay components.
 * Each overlay should render its content within this base structure.
 */
export const BaseOverlay: React.FC<BaseOverlayProps & { children: React.ReactNode }> = ({
  zIndex,
  opacity = 1,
  visible = true,
  className = '',
  allowPointerEvents = false,
  children
}) => {
  if (!visible) return null;

  return (
    <div
      className={`base-overlay ${className}`}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex,
        opacity,
        pointerEvents: allowPointerEvents ? 'auto' : 'none' // Allow clicks to pass through to map
      }}
    >
      {children}
    </div>
  );
};

export default BaseOverlay;
