import { useState, useCallback } from 'react';

export const useNavigation = (initialTab: number = 0) => {
  const [selectedTab, setSelectedTab] = useState(initialTab);

  const handleTabChange = useCallback((tab: number) => {
    setSelectedTab(tab);
  }, []);

  return {
    selectedTab,
    handleTabChange,
  };
};
