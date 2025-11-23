import React from 'react';
import {
  Mic,
  Guitar,
  Drum,
  Music,
  Piano,
  Keyboard,
  Wind,
  ChevronDown,
  Lock,
  Info,
  ArrowUpDown,
  Home,
  Music2,
  Radio,
  Library,
  Settings,
} from 'lucide-react';

export const Icons = {
  // Track Types
  vocals: Mic,
  guitar: Guitar,
  bass: Guitar, // Using guitar icon as placeholder
  drums: Drum,
  piano: Piano,
  keys: Keyboard,
  wind: Wind,
  strings: Music2, // Using Music2 icon for strings (Violin not available)
  other: Music,
  
  // UI Icons
  chevronDown: ChevronDown,
  lock: Lock,
  info: Info,
  separation: ArrowUpDown,
  
  // Navigation
  home: Home,
  music: Music2,
  radio: Radio,
  library: Library,
  settings: Settings,
};

export interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export const createIcon = (IconComponent: React.ComponentType<any>) => {
  return ({ size = 24, color = 'currentColor', className, ...props }: IconProps) => (
    <IconComponent size={size} color={color} className={className} {...props} />
  );
};

