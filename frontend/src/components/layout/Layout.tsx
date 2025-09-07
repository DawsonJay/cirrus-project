import React from 'react';
import { Box } from '@mui/material';
import { spacing } from '../../theme/index.ts';
import { useNavigation } from '../../hooks/useNavigation.ts';
import Sidebar from './Sidebar.tsx';
import TopBar from './TopBar.tsx';
import MainContent from './MainContent.tsx';

const Layout: React.FC = () => {
  const { selectedTab, handleTabChange } = useNavigation();

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar Navigation */}
      <Sidebar selectedTab={selectedTab} onTabChange={handleTabChange} />
      
      {/* Main Content Area - Map Dominated */}
      <Box
        sx={{
          flexGrow: 1,
          ml: `${spacing.layout.sidebar.width}px`,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Top Bar */}
        <TopBar
          title="The Cirrus Project"
          subtitle="Canadian Weather AI Prediction System"
        />

        {/* Main Content - Map Dominated Layout */}
        <MainContent selectedTab={selectedTab} />
      </Box>
    </Box>
  );
};

export default Layout;
