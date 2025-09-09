import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { GridPoint, transformGridToSvg } from '../utils/coordinateTransform';

interface GridDataContextType {
  gridData: GridPoint[];
  isLoading: boolean;
  error: string | null;
  loadGridData: (sampleSize?: number) => Promise<void>;
  refreshGridData: () => Promise<void>;
}

const GridDataContext = createContext<GridDataContextType | undefined>(undefined);

interface GridDataProviderProps {
  children: ReactNode;
}

export const GridDataProvider: React.FC<GridDataProviderProps> = ({ children }) => {
  const [gridData, setGridData] = useState<GridPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Loads grid data from the backend API and transforms coordinates to SVG
   * @param sampleSize - Number of points to load (default: 1000)
   */
  const loadGridData = async (sampleSize: number = 1000) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/weather/grid?sample_size=${sampleSize}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load grid data: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // Transform the raw data to include SVG coordinates
      // Backend returns { points: [...], total_points: number, ... }
      const rawPoints = data.points || data;
      const transformedData = transformGridToSvg(rawPoints);
      
      setGridData(transformedData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error loading grid data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Refreshes the current grid data
   */
  const refreshGridData = async () => {
    if (gridData.length > 0) {
      await loadGridData(gridData.length);
    }
  };

  // Load initial data on mount
  useEffect(() => {
    loadGridData(1000);
  }, []);

  const value: GridDataContextType = {
    gridData,
    isLoading,
    error,
    loadGridData,
    refreshGridData
  };

  return (
    <GridDataContext.Provider value={value}>
      {children}
    </GridDataContext.Provider>
  );
};

/**
 * Hook to use the grid data context
 * @returns GridDataContextType
 * @throws Error if used outside of GridDataProvider
 */
export const useGridData = (): GridDataContextType => {
  const context = useContext(GridDataContext);
  
  if (context === undefined) {
    throw new Error('useGridData must be used within a GridDataProvider');
  }
  
  return context;
};
