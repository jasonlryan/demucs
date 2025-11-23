import React from 'react';
import styled from 'styled-components';
import { colors, spacing } from '../../styles/theme';

const MainContentContainer = styled.main`
  margin-left: 240px;
  min-height: 100vh;
  background: ${colors.background.primary};
  padding: ${spacing.xl};
`;

const ContentWrapper = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`;

interface MainContentProps {
  children: React.ReactNode;
}

const MainContent: React.FC<MainContentProps> = ({ children }) => {
  return (
    <MainContentContainer>
      <ContentWrapper>{children}</ContentWrapper>
    </MainContentContainer>
  );
};

export default MainContent;

