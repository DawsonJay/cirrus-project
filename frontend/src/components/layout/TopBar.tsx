import React from 'react';
import { Box, Typography } from '@mui/material';
import { colors, spacing } from '../../theme/index.ts';

interface TopBarProps {
  title: string;
  subtitle: string;
}

const TopBar: React.FC<TopBarProps> = ({ title, subtitle }) => {
  return (
    <Box
      sx={{
        backgroundColor: colors.background.topbar,
        borderBottom: `1px solid ${colors.border.default}`,
        p: spacing.layout.topbar.padding / spacing.unit,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <Typography variant="h5" sx={{ color: colors.text.primary, fontWeight: 600 }}>
        {title}
      </Typography>
      <Typography variant="body1" sx={{ color: colors.text.secondary }}>
        {subtitle}
      </Typography>
    </Box>
  );
};

export default TopBar;
