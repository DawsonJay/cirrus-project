import React from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import { useGridData } from '../../contexts/GridDataContext';
import GridOverlay from './GridOverlay';

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
      
      {/* Canada SVG Map */}
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

      {/* Weather Data Grid Overlay */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 3,
        }}
      >
        <GridOverlay
          sampleSize={sampleSize}
          showTemperature={true}
          pointSize={1}
        />
      </Box>


      {/* Data Info Overlay */}
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: 2,
          borderRadius: 1,
          zIndex: 4,
          minWidth: 200,
        }}
      >
        <Typography variant="h6" gutterBottom>
          Weather Data
        </Typography>
        <Typography variant="body2">
          Points: {gridData.length.toLocaleString()}
        </Typography>
        <Typography variant="body2">
          Sample Size: {sampleSize.toLocaleString()}
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, fontSize: '0.75rem' }}>
          Blue = Cold, Red = Hot, White = No Data
        </Typography>
      </Box>
    </Box>
  );
};

export default WeatherDataMap;

