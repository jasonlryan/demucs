import React from 'react';
import styled from 'styled-components';
import { colors, typography, spacing } from '../../styles/theme';
import { Icons, createIcon } from '../../utils/icons';

const SectionContainer = styled.section`
  margin-bottom: ${spacing.xl};
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  margin-bottom: ${spacing.lg};
`;

const SectionTitle = styled.h3`
  font-size: ${typography.scale.h3.fontSize};
  font-weight: ${typography.scale.h3.fontWeight};
  line-height: ${typography.scale.h3.lineHeight};
  color: ${colors.text.primary};
`;

const InfoButton = styled.button`
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid ${colors.border.default};
  background: transparent;
  color: ${colors.text.secondary};
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;

  &:hover {
    border-color: ${colors.interactive.primary};
    color: ${colors.interactive.primary};
  }
`;

interface SectionProps {
  title: string;
  infoIcon?: boolean;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({ title, infoIcon, children }) => {
  const InfoIcon = createIcon(Icons.info);

  return (
    <SectionContainer>
      <SectionHeader>
        <SectionTitle>{title}</SectionTitle>
        {infoIcon && (
          <InfoButton aria-label="More information">
            <InfoIcon size={12} />
          </InfoButton>
        )}
      </SectionHeader>
      {children}
    </SectionContainer>
  );
};

export default Section;

