import React from 'react';
import { Box, Typography, Link } from '@mui/material';

interface SimpleWireframeMapProps {
  title?: string;
  description?: string;
  weatherType?: string;
}

const SimpleWireframeMap: React.FC<SimpleWireframeMapProps> = ({ 
  title, 
  description, 
  weatherType 
}) => {
  // Accurate Canada wireframe using the provided SVG with proper attribution
  const canadaWireframe = (
    <Box sx={{ position: 'relative', height: '100%', width: '100%' }}>
      {/* Background */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: '#2a2e37',
        }}
      />
      
      
      {/* Canada SVG with solid fill */}
      <Box
        component="img"
        src="/assets/maps/canada-wireframe.svg"
        alt="Canada Wireframe Map by Vemaps.com"
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          zIndex: 2,
        }}
      />
    </Box>
  );

  // Weather-specific highlight areas - positioned for 800x600 viewBox
  const getHighlightAreas = (type: string) => {
    switch (type) {
      case 'Wildfires':
        return (
          <>
            {/* British Columbia - high fire risk */}
            <circle cx="120" cy="200" r="8" fill="#ff9800" opacity="0.8">
              <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite" />
            </circle>
            {/* Alberta - fire risk */}
            <circle cx="200" cy="180" r="6" fill="#f44336" opacity="0.7">
              <animate attributeName="opacity" values="0.7;0.3;0.7" dur="2.5s" repeatCount="indefinite" />
            </circle>
            {/* Northern Territories */}
            <circle cx="280" cy="120" r="5" fill="#ff9800" opacity="0.6">
              <animate attributeName="opacity" values="0.6;0.2;0.6" dur="3s" repeatCount="indefinite" />
            </circle>
          </>
        );
      case 'Hailstorms':
        return (
          <>
            {/* Alberta Hailstorm Alley */}
            <circle cx="220" cy="200" r="10" fill="#4fc3f7" opacity="0.8">
              <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite" />
            </circle>
            <circle cx="250" cy="220" r="7" fill="#00bcd4" opacity="0.7">
              <animate attributeName="opacity" values="0.7;0.3;0.7" dur="2.5s" repeatCount="indefinite" />
            </circle>
          </>
        );
      case 'Tornadoes':
        return (
          <>
            {/* Southern Ontario */}
            <circle cx="480" cy="260" r="8" fill="#9c27b0" opacity="0.8">
              <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite" />
            </circle>
            <circle cx="520" cy="280" r="6" fill="#9c27b0" opacity="0.7">
              <animate attributeName="opacity" values="0.7;0.3;0.7" dur="2.5s" repeatCount="indefinite" />
            </circle>
          </>
        );
      case 'Floods':
        return (
          <>
            {/* British Columbia */}
            <circle cx="140" cy="220" r="9" fill="#00bcd4" opacity="0.8">
              <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite" />
            </circle>
            <circle cx="120" cy="240" r="7" fill="#4fc3f7" opacity="0.7">
              <animate attributeName="opacity" values="0.7;0.3;0.7" dur="2.5s" repeatCount="indefinite" />
            </circle>
          </>
        );
      case 'Derechos':
        return (
          <>
            {/* Quebec-Windsor Corridor */}
            <circle cx="560" cy="240" r="8" fill="#4caf50" opacity="0.8">
              <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite" />
            </circle>
            <circle cx="600" cy="260" r="6" fill="#4caf50" opacity="0.7">
              <animate attributeName="opacity" values="0.7;0.3;0.7" dur="2.5s" repeatCount="indefinite" />
            </circle>
          </>
        );
      default:
        return (
          <>
            {/* General monitoring points */}
            <circle cx="240" cy="200" r="6" fill="#00bcd4" opacity="0.6">
              <animate attributeName="opacity" values="0.6;0.2;0.6" dur="3s" repeatCount="indefinite" />
            </circle>
            <circle cx="400" cy="220" r="6" fill="#00bcd4" opacity="0.6">
              <animate attributeName="opacity" values="0.6;0.2;0.6" dur="3s" repeatCount="indefinite" />
            </circle>
            <circle cx="520" cy="240" r="6" fill="#00bcd4" opacity="0.6">
              <animate attributeName="opacity" values="0.6;0.2;0.6" dur="3s" repeatCount="indefinite" />
            </circle>
          </>
        );
    }
  };

  return (
    <Box sx={{ height: '100%', position: 'relative' }}>
      {/* Wireframe map - clean without icons */}
      <Box sx={{ position: 'relative', height: '100%' }}>
        {canadaWireframe}
      </Box>
    </Box>
  );
};

export default SimpleWireframeMap;