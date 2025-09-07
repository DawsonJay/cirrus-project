import React from 'react';
import { Box, Avatar } from '@mui/material';
import {
  Dashboard as DashboardIcon,
  LocalFireDepartment as FireIcon,
  AcUnit as HailIcon,
  Tornado as TornadoIcon,
  Water as FloodIcon,
  Air as WindIcon,
} from '@mui/icons-material';
import { colors, spacing } from '../../theme/index.ts';
import { NavigationItem, SidebarProps } from '../../types/weather.ts';

const navigationItems: NavigationItem[] = [
  { id: 0, label: 'Dashboard', icon: DashboardIcon },
  { id: 1, label: 'Wildfires', icon: FireIcon },
  { id: 2, label: 'Hailstorms', icon: HailIcon },
  { id: 3, label: 'Tornadoes', icon: TornadoIcon },
  { id: 4, label: 'Floods', icon: FloodIcon },
  { id: 5, label: 'Derechos', icon: WindIcon },
];

const Sidebar: React.FC<SidebarProps> = ({ selectedTab, onTabChange }) => {
  return (
    <Box
      sx={{
        width: spacing.layout.sidebar.width,
        height: '100vh',
        backgroundColor: colors.background.sidebar,
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 1000,
        alignItems: 'center',
        py: spacing.layout.sidebar.padding / spacing.unit,
      }}
    >
      {/* User Avatar */}
      <Avatar
        sx={{
          width: 40,
          height: 40,
          backgroundColor: colors.primary.main,
          fontSize: '1rem',
          fontWeight: 600,
          mb: 3,
        }}
      >
        CP
      </Avatar>

      {/* Navigation Icons */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, flexGrow: 1 }}>
        {navigationItems.map((item) => {
          const IconComponent = item.icon;
          const isSelected = selectedTab === item.id;
          
          return (
            <Box
              key={item.id}
              onClick={() => onTabChange(item.id)}
              sx={{
                width: 48,
                height: 48,
                borderRadius: '12px',
                backgroundColor: isSelected ? colors.primary.main : 'transparent',
                color: isSelected ? colors.text.primary : colors.text.secondary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                position: 'relative',
                '&:hover': {
                  backgroundColor: isSelected ? colors.primary.light : colors.interactive.hover,
                  color: colors.text.primary,
                },
                transition: 'all 0.2s ease-in-out',
                ...(isSelected && {
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    left: -16,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: 3,
                    height: 20,
                    backgroundColor: colors.primary.main,
                    borderRadius: '0 2px 2px 0',
                  }
                })
              }}
            >
              <IconComponent fontSize="medium" />
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};

export default Sidebar;
