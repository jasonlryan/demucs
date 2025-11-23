import React, { useState } from 'react';
import styled from 'styled-components';
import { colors, spacing, borderRadius, transitions } from '../../styles/theme';
import TrackControl from './TrackControl';

const TrackGroupContainer = styled.div`
  display: flex;
  flex-direction: column;
`;

const ChildrenContainer = styled.div<{ $expanded?: boolean }>`
  display: ${props => props.$expanded ? 'flex' : 'none'};
  flex-direction: column;
  gap: ${spacing.xs};
  margin-left: ${spacing.xl};
  margin-top: ${spacing.xs};
  padding-left: ${spacing.md};
  border-left: 2px solid ${colors.interactive.primary};
`;

const CollapseButton = styled.button<{ $expanded?: boolean }>`
  padding: 4px 8px;
  border: 1px solid ${colors.border.default};
  background: transparent;
  color: ${colors.text.secondary};
  border-radius: ${borderRadius.sm};
  cursor: pointer;
  font-size: 10px;
  transition: ${transitions.default};
  margin-left: ${spacing.xs};

  &:hover {
    border-color: ${colors.interactive.primary};
    color: ${colors.interactive.primary};
  }
`;

interface TrackGroupProps {
  parentTrack: { name: string; url: string; volume: number; muted: boolean; soloed: boolean };
  childTracks: Array<{ name: string; url: string; volume: number; muted: boolean; soloed: boolean }>;
  trackStates: Record<string, { volume: number; muted: boolean; soloed: boolean }>;
  splittingTrack: string | null;
  onMute: (trackName: string) => void;
  onSolo: (trackName: string) => void;
  onVolumeChange: (trackName: string, volume: number) => void;
  onSplit?: (trackName: string) => void;
}

const TrackGroup: React.FC<TrackGroupProps> = ({
  parentTrack,
  childTracks,
  trackStates,
  splittingTrack,
  onMute,
  onSolo,
  onVolumeChange,
  onSplit,
}) => {
  const [expanded, setExpanded] = useState(true);
  const trackLower = parentTrack.name.toLowerCase();
  const canSplit = trackLower === 'vocals' || trackLower === 'drums';
  const isSplitting = splittingTrack === parentTrack.name;

  return (
    <TrackGroupContainer>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <TrackControl
          trackName={parentTrack.name}
          volume={trackStates[parentTrack.name]?.volume ?? 1.0}
          muted={trackStates[parentTrack.name]?.muted ?? false}
          soloed={trackStates[parentTrack.name]?.soloed ?? false}
          onMute={() => onMute(parentTrack.name)}
          onSolo={() => onSolo(parentTrack.name)}
          onVolumeChange={(vol) => onVolumeChange(parentTrack.name, vol)}
          onSplit={onSplit}
          canSplit={canSplit}
          isSplitting={isSplitting}
        />
        {childTracks.length > 0 && (
          <CollapseButton
            $expanded={expanded}
            onClick={() => setExpanded(!expanded)}
            title={expanded ? 'Collapse' : 'Expand'}
          >
            {expanded ? '▲' : '▼'}
          </CollapseButton>
        )}
      </div>
      {childTracks.length > 0 && (
        <ChildrenContainer $expanded={expanded}>
          {childTracks.map(childTrack => {
            // Extract child name (remove parent prefix)
            const childName = childTrack.name.replace(`${parentTrack.name}_`, '');
            return (
              <TrackControl
                key={childTrack.name}
                trackName={childName}
                volume={trackStates[childTrack.name]?.volume ?? 1.0}
                muted={trackStates[childTrack.name]?.muted ?? false}
                soloed={trackStates[childTrack.name]?.soloed ?? false}
                onMute={() => onMute(childTrack.name)}
                onSolo={() => onSolo(childTrack.name)}
                onVolumeChange={(vol) => onVolumeChange(childTrack.name, vol)}
                isChild={true}
              />
            );
          })}
        </ChildrenContainer>
      )}
    </TrackGroupContainer>
  );
};

export default TrackGroup;

