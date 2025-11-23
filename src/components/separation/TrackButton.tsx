import React from 'react';
import styled from 'styled-components';
import { colors, spacing, borderRadius, transitions } from '../../styles/theme';
import { Icons, createIcon } from '../../utils/icons';

const ButtonContainer = styled.button<{ selected?: boolean; locked?: boolean }>`
  width: 140px;
  height: 100px;
  padding: ${spacing.md};
  border-radius: ${borderRadius.md};
  background: ${colors.background.tertiary};
  border: 2px solid ${props => props.selected ? colors.border.active : 'transparent'};
  cursor: ${props => props.locked ? 'not-allowed' : 'pointer'};
  transition: ${transitions.default};
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  position: relative;
  opacity: ${props => props.locked ? 0.6 : 1};

  &:hover {
    background: ${props => props.locked ? colors.background.tertiary : colors.background.active};
  }

  &:active {
    transform: ${props => props.locked ? 'none' : 'scale(0.98)'};
  }
`;

const IconWrapper = styled.div`
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: ${spacing.sm};
`;

const Label = styled.div`
  font-size: 14px;
  font-weight: 500;
  color: ${colors.text.primary};
  text-align: center;
`;

const ActionIcons = styled.div`
  position: absolute;
  top: ${spacing.sm};
  right: ${spacing.sm};
  display: flex;
  gap: ${spacing.xs};
  align-items: center;
`;

interface TrackButtonProps {
  icon: string;
  label: string;
  selected?: boolean;
  locked?: boolean;
  hasDropdown?: boolean;
  onClick: () => void;
}

const TrackButton: React.FC<TrackButtonProps> = ({
  icon,
  label,
  selected,
  locked,
  hasDropdown,
  onClick,
}) => {
  const IconComponent = icon ? Icons[icon as keyof typeof Icons] : null;
  const Icon = IconComponent ? createIcon(IconComponent) : null;
  const LockIcon = createIcon(Icons.lock);
  const ChevronIcon = createIcon(Icons.chevronDown);

  return (
    <ButtonContainer 
      selected={selected} 
      locked={locked}
      onClick={onClick}
      disabled={locked}
      aria-label={locked ? `${label} (locked)` : label}
    >
      {Icon && (
        <IconWrapper>
          <Icon size={32} />
        </IconWrapper>
      )}
      <Label>{label}</Label>
      <ActionIcons>
        {locked && <LockIcon size={16} color={colors.status.locked} />}
        {hasDropdown && !locked && <ChevronIcon size={16} color={colors.text.secondary} />}
      </ActionIcons>
    </ButtonContainer>
  );
};

export default TrackButton;

