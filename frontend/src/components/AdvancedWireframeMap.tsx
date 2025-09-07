import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon } from 'react-leaflet';
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

interface AdvancedWireframeMapProps {
  center: [number, number];
  zoom: number;
  title: string;
  description: string;
}

// Custom wireframe tile layer
const WireframeTileLayer = () => {
  return (
    <TileLayer
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      className="wireframe-tiles"
    />
  );
};

// Custom marker for wireframe style
const createWireframeMarker = (color: string = '#00bcd4') => {
  return L.divIcon({
    className: 'wireframe-marker',
    html: `
      <div style="
        width: 12px;
        height: 12px;
        background-color: ${color};
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 10px ${color}40;
        animation: pulse 2s infinite;
      "></div>
      <style>
        @keyframes pulse {
          0% { box-shadow: 0 0 10px ${color}40; }
          50% { box-shadow: 0 0 20px ${color}80; }
          100% { box-shadow: 0 0 10px ${color}40; }
        }
      </style>
    `,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
};

const AdvancedWireframeMap: React.FC<AdvancedWireframeMapProps> = ({ 
  center, 
  zoom, 
  title, 
  description 
}) => {
  // Mock Canadian provinces outline data (simplified)
  const canadaOutline = [
    [49.0, -123.0], [49.0, -95.0], [60.0, -95.0], [60.0, -123.0], [49.0, -123.0]
  ];

  return (
    <Box sx={{ height: '100%', position: 'relative' }}>
      {/* Advanced wireframe styling */}
      <style>
        {`
          .wireframe-tiles {
            filter: grayscale(100%) contrast(300%) brightness(0.6) invert(1);
            opacity: 0.8;
          }
          .wireframe-tiles img {
            mix-blend-mode: overlay;
          }
          .leaflet-container {
            background-color: #2a2e37 !important;
          }
          .leaflet-control-container {
            filter: grayscale(100%) contrast(200%);
          }
          .leaflet-popup-content-wrapper {
            background-color: #3a3d47 !important;
            color: #ffffff !important;
            border: 1px solid #404040 !important;
          }
          .leaflet-popup-tip {
            background-color: #3a3d47 !important;
            border: 1px solid #404040 !important;
          }
        `}
      </style>
      
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
        attributionControl={true}
      >
        <WireframeTileLayer />
        
        {/* Wireframe outline of Canada */}
        <Polygon
          positions={canadaOutline}
          pathOptions={{
            color: '#ffffff',
            weight: 2,
            opacity: 0.8,
            fillColor: 'transparent',
            fillOpacity: 0,
            dashArray: '5, 5'
          }}
        />
        
        {/* Custom wireframe marker */}
        <Marker 
          position={center} 
          icon={createWireframeMarker('#00bcd4')}
        >
          <Popup>
            <Box sx={{ color: '#ffffff', minWidth: '200px' }}>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 600, color: '#ffffff' }}>
                {title}
              </Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                {description}
              </Typography>
            </Box>
          </Popup>
        </Marker>
      </MapContainer>
    </Box>
  );
};

export default AdvancedWireframeMap;
