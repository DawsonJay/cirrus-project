import React from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import { useGridData } from '../../contexts/GridDataContext';
import GridOverlay from './GridOverlay';
import { 
  OverlayManager, 
  TemperatureHeatMapOverlay,
  WildfireAreasOverlay,
  AffectedCitiesOverlay,
  WeatherAlertsOverlay
} from './overlays';

interface WeatherDataMapProps {
  sampleSize?: number;
}

const WeatherDataMap: React.FC<WeatherDataMapProps> = ({ sampleSize = 1000 }) => {
  const { gridData, isLoading, error } = useGridData();

  if (isLoading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        flexDirection: 'column',
        gap: 2
      }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary">
          Loading weather data...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        p: 2
      }}>
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          <Typography variant="h6">Failed to load weather data</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  if (!gridData || gridData.length === 0) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%'
      }}>
        <Typography variant="body2" color="text.secondary">
          No weather data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', position: 'relative' }}>
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
      
      {/* Canada SVG Map - Lowest layer */}
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
          zIndex: 1, // Lowest layer
        }}
      />

      {/* Overlay System - All overlays on top of map */}
      <OverlayManager>
        {/* Base weather data grid */}
        <GridOverlay
          sampleSize={sampleSize}
          showTemperature={true}
          pointSize={1}
          zIndex={2}
        />
        
        {/* Demo overlays - showing some by default */}
        <TemperatureHeatMapOverlay
          zIndex={3}
          opacity={0.6}
          visible={true} // Show temperature heat map
        />
        
        <WildfireAreasOverlay
          zIndex={4}
          opacity={0.8}
          visible={true} // Show wildfire areas
        />
        
        <AffectedCitiesOverlay
          zIndex={5}
          opacity={1}
          visible={true} // Show affected cities
        />
        
        <WeatherAlertsOverlay
          zIndex={6}
          opacity={0.9}
          visible={true} // Show weather alerts
        />
      </OverlayManager>

    </Box>
  );
};

export default WeatherDataMap;

