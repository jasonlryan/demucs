import React from 'react';
import styled from 'styled-components';
import './styles/globals.css';
import { spacing } from './styles/theme';
import SeparationPage from './components/separation/SeparationPage';

const AppContainer = styled.div`
  min-height: 100vh;
  background: #0A0A0A;
  padding: ${spacing.xl};
`;

const ContentWrapper = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`;

function App() {
  return (
    <AppContainer>
      <ContentWrapper>
        <SeparationPage />
      </ContentWrapper>
    </AppContainer>
  );
}

export default App;

