// Cirrus Project Spacing System
export const spacing = {
  // Base spacing unit (8px)
  unit: 8,
  
  // Common spacing values
  xs: 4,    // 4px
  sm: 8,    // 8px
  md: 16,   // 16px
  lg: 24,   // 24px
  xl: 32,   // 32px
  xxl: 48,  // 48px
  
  // Component-specific spacing
  component: {
    padding: 16,      // Standard component padding
    margin: 16,       // Standard component margin
    borderRadius: 8,  // Standard border radius
    gap: 12,          // Standard gap between elements
  },
  
  // Layout spacing
  layout: {
    sidebar: {
      width: 80,      // Sidebar width
      padding: 16,    // Sidebar padding
    },
    topbar: {
      height: 64,     // Top bar height
      padding: 16,    // Top bar padding
    },
    content: {
      padding: 24,    // Main content padding
      margin: 24,     // Main content margin
    },
  },
} as const;

export type SpacingKey = keyof typeof spacing;
