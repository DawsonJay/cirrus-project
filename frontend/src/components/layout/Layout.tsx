import React from 'react';
import { Box } from '@mui/material';
import { spacing } from '../../theme';
import { useNavigation } from '../../hooks/useNavigation';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import MainContent from './MainContent';

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
