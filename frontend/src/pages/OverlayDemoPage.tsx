import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Switch, 
  FormControlLabel, 
  Slider, 
  Paper,
  Grid,
  Chip
} from '@mui/material';
import WeatherDataMap from '../components/map/WeatherDataMap';

/**
 * OverlayDemoPage - Demonstrates the composable overlay system
 * 
 * This page shows how different overlays can be combined and controlled
 * to create different views of the weather data and related information.
 */
const OverlayDemoPage: React.FC = () => {
  const [overlays, setOverlays] = useState({
    temperatureHeatMap: true,  // Show by default
    wildfireAreas: true,       // Show by default
    affectedCities: true,      // Show by default
    weatherAlerts: true        // Show by default
  });

  const [opacity, setOpacity] = useState(0.7);

  const handleOverlayToggle = (overlayName: keyof typeof overlays) => {
    setOverlays(prev => ({
      ...prev,
      [overlayName]: !prev[overlayName]
    }));
  };

  const overlayControls: Array<{
    key: keyof typeof overlays;
    label: string;
    color: 'primary' | 'error' | 'warning' | 'info' | 'default';
  }> = [
    { key: 'temperatureHeatMap', label: 'Temperature Heat Map', color: 'primary' },
    { key: 'wildfireAreas', label: 'Wildfire Areas', color: 'error' },
    { key: 'affectedCities', label: 'Affected Cities', color: 'warning' },
    { key: 'weatherAlerts', label: 'Weather Alerts', color: 'info' }
  ];

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h4" gutterBottom>
          Overlay System Demo
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Toggle different overlays to see how they combine on the map
        </Typography>
      </Box>

      {/* Controls */}
      <Paper sx={{ p: 2, m: 2 }}>
        <Typography variant="h6" gutterBottom>
          Overlay Controls
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {overlayControls.map((control) => (
                <Chip
                  key={control.key}
                  label={control.label}
                  color={overlays[control.key] ? control.color : 'default'}
                  variant={overlays[control.key] ? 'filled' : 'outlined'}
                  onClick={() => handleOverlayToggle(control.key)}
                  sx={{ mb: 1 }}
                />
              ))}
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Typography variant="body2" gutterBottom>
              Overlay Opacity: {Math.round(opacity * 100)}%
            </Typography>
            <Slider
              value={opacity}
              onChange={(_, value) => setOpacity(value as number)}
              min={0.1}
              max={1}
              step={0.1}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${Math.round(value * 100)}%`}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Map with overlays */}
      <Box sx={{ flex: 1, position: 'relative' }}>
        <WeatherDataMap 
          sampleSize={1000}
          // Pass overlay states as props (you'd need to modify WeatherDataMap to accept these)
        />
      </Box>
    </Box>
  );
};

export default OverlayDemoPage;
