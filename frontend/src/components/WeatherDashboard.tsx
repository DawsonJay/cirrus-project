import React, { useState } from 'react';
import { Box, Paper, Typography, Tabs, Tab, Alert } from '@mui/material';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`weather-tabpanel-${index}`}
      aria-labelledby={`weather-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const WeatherDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Default center for Canada
  const canadaCenter: [number, number] = [56.1304, -106.3468];

  return (
    <Box>
      {/* Project Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Cirrus Project
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Canadian Weather AI Prediction System
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Advanced AI-powered weather prediction and early warning system for Canadian weather challenges.
          Monitor wildfires, hailstorms, tornadoes, floods, and derechos across Canada.
        </Typography>
      </Paper>

      {/* Development Status Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Development Status:</strong> This is the initial setup of the Cirrus Project.
          The dashboard will display real-time weather predictions and risk assessments once the AI models are implemented.
        </Typography>
      </Alert>

      {/* Weather Tabs */}
      <Paper elevation={2}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="weather prediction tabs">
            <Tab label="Wildfires" id="weather-tab-0" />
            <Tab label="Hailstorms" id="weather-tab-1" />
            <Tab label="Tornadoes" id="weather-tab-2" />
            <Tab label="Floods" id="weather-tab-3" />
            <Tab label="Derechos" id="weather-tab-4" />
          </Tabs>
        </Box>

        {/* Wildfire Tab */}
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h5" gutterBottom>
            Wildfire Risk Assessment
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            AI-powered wildfire prediction and risk assessment across Canada. 
            Monitor fire danger ratings, weather conditions, and historical patterns.
          </Typography>
          
          {/* Interactive Map */}
          <Box sx={{ height: '500px', width: '100%', mt: 2 }}>
            <MapContainer
              center={canadaCenter}
              zoom={4}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={canadaCenter}>
                <Popup>
                  Canada - Wildfire Risk Assessment
                  <br />
                  AI models will display real-time risk data here
                </Popup>
              </Marker>
            </MapContainer>
          </Box>
        </TabPanel>

        {/* Hailstorm Tab */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h5" gutterBottom>
            Hailstorm Prediction
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Monitor hailstorm risk in Alberta's "Hailstorm Alley" and other high-risk areas.
            Track atmospheric conditions and storm development patterns.
          </Typography>
          
          <Box sx={{ height: '500px', width: '100%', mt: 2 }}>
            <MapContainer
              center={[51.0447, -114.0719]} // Calgary, Alberta
              zoom={6}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={[51.0447, -114.0719]}>
                <Popup>
                  Alberta Hailstorm Alley
                  <br />
                  High-risk hailstorm region
                </Popup>
              </Marker>
            </MapContainer>
          </Box>
        </TabPanel>

        {/* Tornado Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h5" gutterBottom>
            Tornado Risk Assessment
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Track tornado risk across southern provinces. Monitor atmospheric instability,
            wind shear, and storm rotation patterns.
          </Typography>
          
          <Box sx={{ height: '500px', width: '100%', mt: 2 }}>
            <MapContainer
              center={[43.6532, -79.3832]} // Toronto, Ontario
              zoom={5}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={[43.6532, -79.3832]}>
                <Popup>
                  Southern Ontario
                  <br />
                  Tornado risk monitoring
                </Popup>
              </Marker>
            </MapContainer>
          </Box>
        </TabPanel>

        {/* Flood Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h5" gutterBottom>
            Flood Risk Monitoring
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Monitor river levels, precipitation patterns, and flood risk across Canada.
            Track soil saturation and drainage system capacity.
          </Typography>
          
          <Box sx={{ height: '500px', width: '100%', mt: 2 }}>
            <MapContainer
              center={[49.2827, -123.1207]} // Vancouver, BC
              zoom={6}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={[49.2827, -123.1207]}>
                <Popup>
                  British Columbia
                  <br />
                  Flood risk monitoring
                </Popup>
              </Marker>
            </MapContainer>
          </Box>
        </TabPanel>

        {/* Derecho Tab */}
        <TabPanel value={tabValue} index={4}>
          <Typography variant="h5" gutterBottom>
            Derecho Windstorm Forecasting
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Track widespread windstorm development and progression across major corridors.
            Monitor atmospheric pressure systems and wind patterns.
          </Typography>
          
          <Box sx={{ height: '500px', width: '100%', mt: 2 }}>
            <MapContainer
              center={[45.5017, -73.5673]} // Montreal, Quebec
              zoom={5}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={[45.5017, -73.5673]}>
                <Popup>
                  Quebec-Windsor Corridor
                  <br />
                  Derecho windstorm monitoring
                </Popup>
              </Marker>
            </MapContainer>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default WeatherDashboard;
