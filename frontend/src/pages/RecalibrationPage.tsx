import React from 'react';
import { Box } from '@mui/material';
import { colors, spacing } from '../theme';
import RecalibrationOverlay from '../components/map/RecalibrationOverlay';

/**
 * RecalibrationPage component for manually adjusting reference point positions
 * This page provides a dedicated interface for map calibration
 */
const RecalibrationPage: React.FC = () => {
  const handlePointsUpdate = (points: any[]) => {
    // This will be called whenever points are moved
    console.log('Reference points updated:', points);
  };

  return (
    <Box
      sx={{
        height: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: colors.background.default,
      }}
    >
      {/* Header */}
      <Box
        sx={{
          padding: spacing.layout.content.padding / spacing.unit,
          backgroundColor: colors.background.sidebar,
          borderBottom: `1px solid ${colors.border.default}`,
        }}
      >
        <h2 style={{ 
          color: colors.text.primary, 
          margin: 0,
          fontSize: '1.5rem'
        }}>
          Map Recalibration Tool
        </h2>
        <p style={{ 
          color: colors.text.secondary, 
          margin: '5px 0 0 0',
          fontSize: '0.9rem'
        }}>
          Drag the red reference points to their correct positions on the map. 
          Use the Export button to copy the updated coordinates.
        </p>
      </Box>

      {/* Map Container */}
      <Box
        sx={{
          flexGrow: 1,
          position: 'relative',
          backgroundColor: colors.background.default,
        }}
      >
        {/* Background Map */}
        <Box
          component="img"
          src="/assets/maps/canada-wireframe.svg"
          alt="Canada Wireframe Map"
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            zIndex: 1,
          }}
        />

        {/* Recalibration Overlay */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            zIndex: 2,
          }}
        >
          <RecalibrationOverlay onPointsUpdate={handlePointsUpdate} />
        </Box>
      </Box>
    </Box>
  );
};

export default RecalibrationPage;
