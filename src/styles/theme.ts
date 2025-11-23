// Design System - Theme Tokens

export const colors = {
  // Backgrounds
  background: {
    primary: '#0A0A0A',
    secondary: '#121212',
    tertiary: '#1A1A1A',
    active: '#2A2A2A',
    selected: '#1E3A5F',
  },
  
  // Text
  text: {
    primary: '#FFFFFF',
    secondary: '#B3B3B3',
    tertiary: '#808080',
    accent: '#4A9EFF',
  },
  
  // Interactive Elements
  interactive: {
    primary: '#4A9EFF',
    hover: '#5AAFFF',
    active: '#3A8EEF',
    disabled: '#404040',
  },
  
  // Status Indicators
  status: {
    locked: '#FF6B6B',
    beta: '#FFA500',
    success: '#4CAF50',
    error: '#F44336',
  },
  
  // Borders & Dividers
  border: {
    default: '#2A2A2A',
    active: '#4A9EFF',
    divider: '#1A1A1A',
  },
};

export const typography = {
  fontFamily: {
    primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    mono: '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace',
  },
  
  scale: {
    h1: {
      fontSize: '32px',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontSize: '24px',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontSize: '20px',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body: {
      fontSize: '16px',
      fontWeight: 400,
      lineHeight: 1.5,
    },
    small: {
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: 1.4,
    },
    caption: {
      fontSize: '12px',
      fontWeight: 500,
      lineHeight: 1.3,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.05em',
    },
  },
};

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
  xxxl: '64px',
};

export const borderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  full: '9999px',
};

export const shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
  md: '0 4px 8px rgba(0, 0, 0, 0.4)',
  lg: '0 8px 16px rgba(0, 0, 0, 0.5)',
  xl: '0 16px 32px rgba(0, 0, 0, 0.6)',
  inner: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)',
};

export const transitions = {
  default: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
  fast: 'all 0.15s ease-out',
  slow: 'all 0.3s ease-in-out',
};

export const breakpoints = {
  mobile: '640px',
  tablet: '768px',
  desktop: '1024px',
  wide: '1280px',
};

