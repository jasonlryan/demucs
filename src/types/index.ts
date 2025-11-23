export interface TrackType {
  id: string;
  label: string;
  icon: string;
  locked?: boolean;
  hasDropdown?: boolean;
}

export interface BasicSeparation {
  id: string;
  title: string;
  tracks: string[];
  trackCount: number;
  icon: string;
}

export interface NavItem {
  id: string;
  label: string;
  icon?: string;
  badge?: string;
  children?: NavItem[];
}

export interface SeparationConfig {
  basic?: string;
  custom?: string[];
}

