import React from 'react';
import styled from 'styled-components';
import { colors, spacing } from '../../styles/theme';
import NavItem from '../navigation/NavItem';

const SidebarContainer = styled.aside`
  position: fixed;
  left: 0;
  top: 0;
  width: 240px;
  height: 100vh;
  background: ${colors.background.secondary};
  padding: ${spacing.lg};
  overflow-y: auto;
  z-index: 100;
`;

const Logo = styled.div`
  font-size: 24px;
  font-weight: 700;
  color: ${colors.text.primary};
  margin-bottom: ${spacing.xl};
  padding-bottom: ${spacing.xl};
  border-bottom: 1px solid ${colors.border.divider};
`;

const NavSection = styled.div`
  margin-bottom: ${spacing.xl};
`;

const SectionTitle = styled.div`
  font-size: ${spacing.sm};
  font-weight: 600;
  color: ${colors.text.tertiary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: ${spacing.md};
  padding-left: ${spacing.md};
`;

const NavList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.xs};
`;

interface SidebarProps {
  activeSection: string;
  onNavigate: (section: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeSection, onNavigate }) => {
  const navItems = [
    { id: 'separation', label: 'Audio Separation', icon: 'separation' },
  ];

  return (
    <SidebarContainer>
      <Logo>🎵 Audio Separator</Logo>
      
      <NavSection>
        <NavList>
          {navItems.map((item) => (
            <NavItem
              key={item.id}
              icon={item.icon}
              label={item.label}
              active={activeSection === item.id}
              onClick={() => onNavigate(item.id)}
            />
          ))}
        </NavList>
      </NavSection>
    </SidebarContainer>
  );
};

export default Sidebar;

