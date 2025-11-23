import React from 'react';
import styled from 'styled-components';
import { colors, spacing, transitions } from '../../styles/theme';
import { Icons, createIcon } from '../../utils/icons';

const NavItemContainer = styled.div<{ active?: boolean; nested?: boolean }>`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  padding: ${spacing.sm} ${spacing.md};
  border-radius: 8px;
  cursor: pointer;
  transition: ${transitions.default};
  background: ${props => props.active ? colors.background.selected : 'transparent'};
  color: ${props => props.active ? colors.text.primary : colors.text.secondary};
  margin-left: ${props => props.nested ? spacing.lg : '0'};
  position: relative;

  &:hover {
    background: ${props => props.active ? colors.background.selected : colors.background.active};
    color: ${colors.text.primary};
  }

  ${props => props.active && `
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: ${colors.interactive.primary};
      border-radius: 0 2px 2px 0;
    }
  `}
`;

const IconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
`;

const Label = styled.span<{ active?: boolean }>`
  flex: 1;
  font-size: 14px;
  font-weight: ${props => props.active ? 600 : 400};
`;

const Badge = styled.span`
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: ${colors.status.beta};
  color: ${colors.text.primary};
  text-transform: uppercase;
`;

interface NavItemProps {
  icon?: string;
  label: string;
  badge?: string;
  active?: boolean;
  nested?: boolean;
  onClick: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ 
  icon, 
  label, 
  badge, 
  active, 
  nested,
  onClick 
}) => {
  const IconComponent = icon ? Icons[icon as keyof typeof Icons] : null;
  const Icon = IconComponent ? createIcon(IconComponent) : null;

  return (
    <NavItemContainer active={active} nested={nested} onClick={onClick}>
      {Icon && (
        <IconWrapper>
          <Icon size={20} />
        </IconWrapper>
      )}
      <Label active={active}>{label}</Label>
      {badge && <Badge>{badge}</Badge>}
    </NavItemContainer>
  );
};

export default NavItem;

