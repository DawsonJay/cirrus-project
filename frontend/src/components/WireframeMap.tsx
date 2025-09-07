import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Box, Typography } from '@mui/material';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

interface WireframeMapProps {
  center: [number, number];
  zoom: number;
  title: string;
  description: string;
}

const WireframeMap: React.FC<WireframeMapProps> = ({ center, zoom, title, description }) => {
  return (
    <Box sx={{ height: '100%', position: 'relative' }}>
      {/* Custom CSS for wireframe effect */}
      <style>
        {`
          .wireframe-map .leaflet-tile {
            filter: grayscale(100%) contrast(200%) brightness(0.8);
            opacity: 0.7;
          }
          .wireframe-map .leaflet-tile-container {
            filter: contrast(150%) brightness(0.9);
          }
          .wireframe-map .leaflet-control-container {
            filter: grayscale(100%) contrast(200%);
          }
        `}
      </style>
      
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        className="wireframe-map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={center}>
          <Popup>
            <Box sx={{ color: '#000', minWidth: '200px' }}>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                {title}
              </Typography>
              <Typography variant="body2" sx={{ color: '#666' }}>
                {description}
              </Typography>
            </Box>
          </Popup>
        </Marker>
      </MapContainer>
    </Box>
  );
};

export default WireframeMap;
