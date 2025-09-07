// Cirrus Project Color System
export const colors = {
  // Primary colors
  primary: {
    main: '#00bcd4', // Teal for interactive elements
    light: '#00acc1',
    dark: '#0097a7',
  },
  
  // Secondary colors
  secondary: {
    main: '#4fc3f7', // Blue for cold weather
    light: '#81d4fa',
    dark: '#29b6f6',
  },
  
  // Background colors
  background: {
    default: '#2a2e37', // Dark slate background
    paper: '#3a3d47', // Slightly lighter for cards
    sidebar: '#1a1d23', // Darker slate for sidebar
    topbar: '#2a2e37', // Lighter slate for top bar
  },
  
  // Text colors
  text: {
    primary: '#ffffff', // White for primary text
    secondary: '#b0b0b0', // Light grey for secondary text
    disabled: '#757575', // Grey for disabled text
  },
  
  // Border colors
  border: {
    default: '#404040', // Standard border color
    light: '#2a2e37', // Lighter border
    dark: '#1a1d23', // Darker border
  },
  
  // Weather-specific colors
  weather: {
    warning: '#ff9800', // Orange for heat warnings
    error: '#f44336', // Red for high risk
    success: '#4caf50', // Green for safe conditions
    info: '#9c27b0', // Purple for special events
  },
  
  // Interactive states
  interactive: {
    hover: 'rgba(0, 188, 212, 0.1)',
    selected: '#00bcd4',
    disabled: '#404040',
  },
} as const;

export type ColorKey = keyof typeof colors;
