import React from 'react';
import styled from 'styled-components';
import { spacing } from '../../styles/theme';

const GridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: ${spacing.md};
  max-width: 600px;
`;

interface TrackGridProps {
  children: React.ReactNode;
}

const TrackGrid: React.FC<TrackGridProps> = ({ children }) => {
  return <GridContainer>{children}</GridContainer>;
};

export default TrackGrid;

