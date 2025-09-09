import { useMemo } from 'react';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Water as WaterIcon,
  Thermostat as ThermostatIcon,
  Security as SecurityIcon,
  Cloud as CloudIcon,
} from '@mui/icons-material';
import { WeatherType, WeatherData } from '../types/weather';

export const useWeatherTypes = (): WeatherType[] => {
  return useMemo(() => [
    {
      id: 0,
      name: 'Dashboard',
      description: 'Overview of all weather conditions across Canada',
      center: [56.1304, -106.3468] as [number, number],
      zoom: 4,
    },
    {
      id: 1,
      name: 'Wildfires',
      description: 'AI-powered wildfire prediction and risk assessment across Canada',
      center: [56.1304, -106.3468] as [number, number],
      zoom: 4,
    },
    {
      id: 2,
      name: 'Hailstorms',
      description: 'Monitor hailstorm risk in Alberta\'s "Hailstorm Alley" and other high-risk areas',
      center: [51.0447, -114.0719] as [number, number],
      zoom: 6,
    },
    {
      id: 3,
      name: 'Tornadoes',
      description: 'Track tornado risk across southern provinces',
      center: [43.6532, -79.3832] as [number, number],
      zoom: 5,
    },
    {
      id: 4,
      name: 'Floods',
      description: 'Monitor river levels, precipitation patterns, and flood risk across Canada',
      center: [49.2827, -123.1207] as [number, number],
      zoom: 6,
    },
    {
      id: 5,
      name: 'Derechos',
      description: 'Track widespread windstorm development and progression across major corridors',
      center: [45.5017, -73.5673] as [number, number],
      zoom: 5,
    },
  ], []);
};

export const useMockWeatherData = (): WeatherData[] => {
  return useMemo(() => [
    {
      title: 'Temperature',
      value: '22°C',
      change: 5.2,
      icon: <ThermostatIcon />,
      color: '#4fc3f7',
    },
    {
      title: 'Humidity',
      value: '68%',
      change: -2.1,
      icon: <WaterIcon />,
      color: '#00bcd4',
    },
    {
      title: 'Risk Level',
      value: 'Medium',
      change: 12.5,
      icon: <SecurityIcon />,
      color: '#ff9800',
    },
    {
      title: 'Precipitation',
      value: '15mm',
      change: 8.3,
      icon: <CloudIcon />,
      color: '#9c27b0',
    },
  ], []);
};
