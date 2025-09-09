import React, { useState, useCallback, useEffect } from 'react';
import { normalizedReferencePoints } from '../../utils/referencePoints';
import { getScaledReferencePoints } from '../../utils/coordinateTransform';

interface ReferencePoint {
  x: number;
  y: number;
  name: string;
  lat: number;
  lon: number;
}

interface RecalibrationOverlayProps {
  onPointsUpdate?: (points: ReferencePoint[]) => void;
  className?: string;
}

/**
 * RecalibrationOverlay component for manually adjusting reference point positions
 * This component allows dragging reference points to recalibrate the map alignment
 * @param props - Component props
 * @returns JSX element
 */
export const RecalibrationOverlay: React.FC<RecalibrationOverlayProps> = ({
  onPointsUpdate,
  className = ''
}) => {
  // State for draggable reference points
  const [draggablePoints, setDraggablePoints] = useState<ReferencePoint[]>(() => {
    const scaledPoints = getScaledReferencePoints(normalizedReferencePoints);
    return Object.values(scaledPoints);
  });
  
  const [draggedPoint, setDraggedPoint] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // Notify parent component when points are updated
  useEffect(() => {
    if (onPointsUpdate) {
      onPointsUpdate(draggablePoints);
    }
  }, [draggablePoints, onPointsUpdate]);

  // Helper function to convert screen coordinates to SVG coordinates
  const screenToSVG = useCallback((e: React.MouseEvent, svg: SVGElement) => {
    const rect = svg.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Simple scaling approach - more reliable
    const scaleX = 800 / rect.width;
    const scaleY = 600 / rect.height;
    
    return { 
      x: x * scaleX, 
      y: y * scaleY 
    };
  }, []);

  // Drag event handlers
  const handleMouseDown = useCallback((e: React.MouseEvent, pointName: string) => {
    e.preventDefault();
    setDraggedPoint(pointName);
    const svg = e.currentTarget as SVGElement;
    const point = draggablePoints.find(p => p.name === pointName);
    
    if (point) {
      const svgCoords = screenToSVG(e, svg);
      setDragOffset({
        x: svgCoords.x - point.x,
        y: svgCoords.y - point.y
      });
    }
  }, [draggablePoints, screenToSVG]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (draggedPoint) {
      const svg = e.currentTarget as SVGElement;
      const svgCoords = screenToSVG(e, svg);
      
      const newX = svgCoords.x - dragOffset.x;
      const newY = svgCoords.y - dragOffset.y;
      
      setDraggablePoints(prev => 
        prev.map(point => 
          point.name === draggedPoint 
            ? { ...point, x: newX, y: newY }
            : point
        )
      );
    }
  }, [draggedPoint, dragOffset, screenToSVG]);

  const handleMouseUp = useCallback(() => {
    setDraggedPoint(null);
  }, []);

  // Reset to original positions
  const handleReset = useCallback(() => {
    const scaledPoints = getScaledReferencePoints(normalizedReferencePoints);
    setDraggablePoints(Object.values(scaledPoints));
  }, []);

  // Export current positions as code
  const handleExport = useCallback(() => {
    const code = `export const normalizedReferencePoints: Record<string, ReferencePoint> = {
${draggablePoints.map(point => 
  `  ${point.name.toLowerCase().replace(/\s+/g, '')}: { x: ${Math.round(point.x)}, y: ${Math.round(point.y)}, name: "${point.name}", lat: ${point.lat}, lon: ${point.lon} },`
).join('\n')}
};`;
    
    console.log('Updated reference points:');
    console.log(code);
    
    // Copy to clipboard if available
    if (navigator.clipboard) {
      navigator.clipboard.writeText(code).then(() => {
        alert('Reference points copied to clipboard!');
      });
    }
  }, [draggablePoints]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Control panel */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 10,
        background: 'rgba(0, 0, 0, 0.8)',
        padding: '10px',
        borderRadius: '5px',
        color: 'white',
        fontSize: '12px'
      }}>
        <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>Recalibration Mode</div>
        <button 
          onClick={handleReset}
          style={{ 
            marginRight: '5px', 
            padding: '2px 6px', 
            fontSize: '10px',
            background: '#666',
            color: 'white',
            border: 'none',
            borderRadius: '3px',
            cursor: 'pointer'
          }}
        >
          Reset
        </button>
        <button 
          onClick={handleExport}
          style={{ 
            padding: '2px 6px', 
            fontSize: '10px',
            background: '#00bcd4',
            color: 'white',
            border: 'none',
            borderRadius: '3px',
            cursor: 'pointer'
          }}
        >
          Export
        </button>
        <div style={{ marginTop: '5px', fontSize: '10px' }}>
          Drag red dots to recalibrate
        </div>
      </div>

      {/* SVG overlay */}
      <svg 
        className={className} 
        width="100%" 
        height="100%" 
        viewBox="0 0 800 600"
        preserveAspectRatio="xMidYMid meet"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Render draggable reference points */}
        {draggablePoints.map((refPoint, index) => {
          const isDragging = draggedPoint === refPoint.name;
          const opacity = draggedPoint && !isDragging ? 0.1 : 0.9;
          
          return (
            <g key={`ref-${refPoint.name}-${index}`}>
              {/* Draggable hollow circle for reference point */}
              <circle
                cx={refPoint.x}
                cy={refPoint.y}
                r="4"
                fill="none"
                opacity={opacity}
                stroke="#ff0000"
                strokeWidth="2"
                style={{ cursor: 'pointer' }}
                onMouseDown={(e) => handleMouseDown(e, refPoint.name)}
              />
              {/* Label for reference point */}
              <text
                x={refPoint.x + 6}
                y={refPoint.y - 6}
                fill="#ffffff"
                fontSize="9"
                fontWeight="bold"
                opacity={opacity}
                style={{ pointerEvents: 'none' }}
              >
                {refPoint.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default RecalibrationOverlay;
