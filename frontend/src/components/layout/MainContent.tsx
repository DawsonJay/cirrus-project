import React from 'react';
import { Box } from '@mui/material';
import { colors, spacing } from '../../theme';
import { useWeatherTypes } from '../../hooks/useWeatherData';
import { MainContentProps } from '../../types/weather';
import SimpleWireframeMap from '../map/SimpleWireframeMap';
import WeatherDataMap from '../map/WeatherDataMap';
import RecalibrationPage from '../../pages/RecalibrationPage';
import OverlayDemoPage from '../../pages/OverlayDemoPage';

const MainContent: React.FC<MainContentProps> = ({ selectedTab }) => {
  const weatherTypes = useWeatherTypes();
  const currentWeather = weatherTypes[selectedTab];

  // Show recalibration page for tab 6
  if (selectedTab === 6) {
    return <RecalibrationPage />;
  }

  // Show overlay demo page for tab 7
  if (selectedTab === 7) {
    return <OverlayDemoPage />;
  }

  return (
    <Box
      sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: colors.background.default,
        p: spacing.layout.content.padding / spacing.unit,
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Map Section - Centered and bigger */}
      <Box
        sx={{
          height: '75vh',
          width: '90%',
          maxWidth: '1200px',
          position: 'relative',
          borderRadius: spacing.component.borderRadius,
          overflow: 'hidden',
        }}
      >
        <WeatherDataMap sampleSize={1000} />
      </Box>
    </Box>
  );
};

export default MainContent;
