import React from 'react';
import styled from 'styled-components';
import { colors, spacing, borderRadius, shadows, transitions } from '../../styles/theme';
import { Icons, createIcon } from '../../utils/icons';

const ButtonContainer = styled.button<{ selected?: boolean }>`
  width: 280px;
  height: 120px;
  padding: ${spacing.lg};
  border-radius: ${borderRadius.lg};
  background: ${props => props.selected ? colors.background.active : colors.background.tertiary};
  border: 2px solid ${props => props.selected ? colors.border.active : 'transparent'};
  cursor: pointer;
  transition: ${transitions.default};
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  text-align: left;
  color: ${colors.text.primary};

  &:hover {
    background: ${colors.background.active};
    transform: translateY(-2px);
    box-shadow: ${shadows.md};
  }

  &:active {
    transform: translateY(0);
  }
`;

const IconWrapper = styled.div`
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: ${spacing.md};
`;

const ContentWrapper = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: ${spacing.xs};
`;

const Title = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: ${colors.text.primary};
`;

const TrackList = styled.div`
  font-size: 14px;
  color: ${colors.text.secondary};
`;

const TrackCount = styled.div`
  font-size: 12px;
  color: ${colors.text.tertiary};
  margin-top: ${spacing.xs};
`;

interface BasicSeparationButtonProps {
  icon: string;
  title: string;
  tracks: string[];
  trackCount: number;
  selected?: boolean;
  onClick: () => void;
}

const BasicSeparationButton: React.FC<BasicSeparationButtonProps> = ({
  icon,
  title,
  tracks,
  trackCount,
  selected,
  onClick,
}) => {
  const IconComponent = icon ? Icons[icon as keyof typeof Icons] : null;
  const Icon = IconComponent ? createIcon(IconComponent) : null;

  return (
    <ButtonContainer selected={selected} onClick={onClick}>
      {Icon && (
        <IconWrapper>
          <Icon size={32} />
        </IconWrapper>
      )}
      <ContentWrapper>
        <Title>{title}</Title>
        <TrackList>{tracks.join(', ')}</TrackList>
        <TrackCount>{trackCount} Tracks</TrackCount>
      </ContentWrapper>
    </ButtonContainer>
  );
};

export default BasicSeparationButton;

