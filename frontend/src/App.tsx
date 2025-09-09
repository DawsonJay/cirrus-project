import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { theme } from './theme/index';
import Layout from './components/layout/Layout';
import { GridDataProvider } from './contexts/GridDataContext';

// Create React Query client
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <GridDataProvider>
          <Layout />
        </GridDataProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
