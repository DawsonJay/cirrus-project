// Weather-related type definitions for Cirrus Project

export interface WeatherType {
  id: number;
  name: string;
  description: string;
  center: [number, number]; // [latitude, longitude]
  zoom: number;
}

export interface WeatherData {
  title: string;
  value: string;
  change: number;
  icon: React.ReactNode;
  color: string;
}

export interface NavigationItem {
  id: number;
  label: string;
  icon: React.ComponentType;
}

export interface MapProps {
  title?: string;
  description?: string;
  weatherType: string;
}

export interface SidebarProps {
  selectedTab: number;
  onTabChange: (tab: number) => void;
}

export interface MainContentProps {
  selectedTab: number;
}

export interface TopBarProps {
  title: string;
  subtitle: string;
}
