import React from 'react';
import { Box } from '@mui/material';
import { colors, spacing } from '../../theme/index.ts';
import { useWeatherTypes } from '../../hooks/useWeatherData.tsx';
import { MainContentProps } from '../../types/weather.ts';
import SimpleWireframeMap from '../map/SimpleWireframeMap.tsx';

const MainContent: React.FC<MainContentProps> = ({ selectedTab }) => {
  const weatherTypes = useWeatherTypes();
  const currentWeather = weatherTypes[selectedTab];

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
        <SimpleWireframeMap
          weatherType={currentWeather.name}
        />
      </Box>
    </Box>
  );
};

export default MainContent;
