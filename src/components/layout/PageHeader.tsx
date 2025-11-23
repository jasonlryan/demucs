import React from 'react';
import styled from 'styled-components';
import { colors, typography, spacing } from '../../styles/theme';

const HeaderContainer = styled.header`
  margin-bottom: ${spacing.xl};
`;

const Title = styled.h1`
  font-size: ${typography.scale.h1.fontSize};
  font-weight: ${typography.scale.h1.fontWeight};
  line-height: ${typography.scale.h1.lineHeight};
  letter-spacing: ${typography.scale.h1.letterSpacing};
  color: ${colors.text.primary};
  margin-bottom: ${spacing.sm};
`;

const Subtitle = styled.p`
  font-size: ${typography.scale.body.fontSize};
  font-weight: ${typography.scale.body.fontWeight};
  line-height: ${typography.scale.body.lineHeight};
  color: ${colors.text.secondary};
`;

interface PageHeaderProps {
  title: string;
  subtitle?: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle }) => {
  return (
    <HeaderContainer>
      <Title>{title}</Title>
      {subtitle && <Subtitle>{subtitle}</Subtitle>}
    </HeaderContainer>
  );
};

export default PageHeader;

