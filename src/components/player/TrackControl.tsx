import React from 'react';
import styled from 'styled-components';
import { colors, spacing, borderRadius, transitions } from '../../styles/theme';
import { Icons, createIcon } from '../../utils/icons';

const TrackContainer = styled.div<{ $muted?: boolean; $soloed?: boolean; $isChild?: boolean }>`
  background: ${colors.background.tertiary};
  border-radius: ${borderRadius.md};
  padding: ${spacing.md} ${spacing.lg};
  border: 1px solid ${props => props.$soloed ? colors.interactive.primary : colors.border.default};
  opacity: ${props => props.$muted ? 0.5 : 1};
  transition: ${transitions.default};
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  position: relative;

  ${props => props.$isChild && `
    &::before {
      content: '└─';
      color: ${colors.interactive.primary};
      margin-right: ${spacing.xs};
      font-size: 12px;
    }
  `}

  &:hover {
    border-color: ${props => props.$soloed ? colors.interactive.primary : colors.border.active};
    background: ${colors.background.active};
  }
`;

const TrackIcon = styled.div<{ type: string }>`
  width: 36px;
  height: 36px;
  border-radius: ${borderRadius.sm};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: ${props => {
    const iconColors: Record<string, string> = {
      drums: '#e74c3c',
      bass: '#3498db',
      guitar: '#9b59b6',
      piano: '#1abc9c',
      other: '#2ecc71',
      vocals: '#f39c12',
    };
    return iconColors[props.type] || colors.interactive.primary;
  }};
`;

const TrackName = styled.div`
  min-width: 100px;
  font-size: 14px;
  font-weight: 600;
  color: ${colors.text.primary};
`;

const ControlButtons = styled.div`
  display: flex;
  gap: ${spacing.xs};
  margin-left: auto;
`;

const ControlButton = styled.button<{ $active?: boolean; $variant?: string }>`
  padding: 6px 12px;
  border: 1px solid ${props => {
    if (props.$variant === 'solo') return '#2ecc71';
    if (props.$variant === 'mute') return colors.interactive.primary;
    return colors.border.default;
  }};
  background: ${props => props.$active ? (props.$variant === 'solo' ? '#2ecc71' : colors.interactive.primary) : 'transparent'};
  color: ${props => props.$active ? colors.text.primary : (props.$variant === 'solo' ? '#2ecc71' : colors.interactive.primary)};
  border-radius: ${borderRadius.sm};
  cursor: pointer;
  font-weight: 500;
  font-size: 12px;
  transition: ${transitions.default};

  &:hover {
    background: ${props => props.$variant === 'solo' ? '#2ecc71' : colors.interactive.primary};
    color: ${colors.text.primary};
  }
`;

const VolumeControl = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  flex: 1;
  max-width: 300px;
`;

const VolumeLabel = styled.span`
  min-width: 50px;
  font-weight: 500;
  font-size: 12px;
  color: ${colors.text.secondary};
`;

const VolumeSlider = styled.input`
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: ${colors.border.default};
  outline: none;
  -webkit-appearance: none;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: ${colors.interactive.primary};
    cursor: pointer;
    transition: ${transitions.default};
  }

  &::-webkit-slider-thumb:hover {
    background: ${colors.interactive.hover};
    transform: scale(1.1);
  }

  &::-moz-range-thumb {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: ${colors.interactive.primary};
    cursor: pointer;
    border: none;
  }
`;

const VolumeValue = styled.span`
  min-width: 35px;
  text-align: right;
  font-weight: 500;
  font-size: 12px;
  color: ${colors.interactive.primary};
`;

const SplitButton = styled.button<{ $variant?: string; $splitting?: boolean }>`
  padding: 6px 12px;
  border: 1px solid ${props => {
    if (props.$variant === 'vocals') return '#9b59b6';
    if (props.$variant === 'drums') return '#e74c3c';
    return colors.border.default;
  }};
  background: transparent;
  color: ${props => {
    if (props.$variant === 'vocals') return '#9b59b6';
    if (props.$variant === 'drums') return '#e74c3c';
    return colors.interactive.primary;
  }};
  border-radius: ${borderRadius.sm};
  cursor: ${props => props.$splitting ? 'wait' : 'pointer'};
  font-weight: 500;
  font-size: 12px;
  transition: ${transitions.default};
  opacity: ${props => props.$splitting ? 0.6 : 1};
  position: relative;

  &:hover {
    background: ${props => {
      if (props.$splitting) return 'transparent';
      if (props.$variant === 'vocals') return '#9b59b6';
      if (props.$variant === 'drums') return '#e74c3c';
      return colors.interactive.primary;
    }};
    color: ${props => props.$splitting ? 'inherit' : colors.text.primary};
  }
`;

const SplitSpinner = styled.div`
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 50%;
  border-top-color: currentColor;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
  vertical-align: middle;

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

interface TrackControlProps {
  trackName: string;
  volume: number;
  muted: boolean;
  soloed: boolean;
  onMute: () => void;
  onSolo: () => void;
  onVolumeChange: (volume: number) => void;
  onSplit?: (trackName: string) => void;
  canSplit?: boolean;
  isSplitting?: boolean;
  isChild?: boolean;
}

const TrackControl: React.FC<TrackControlProps> = ({
  trackName,
  volume,
  muted,
  soloed,
  onMute,
  onSolo,
  onVolumeChange,
  onSplit,
  canSplit,
  isSplitting,
  isChild = false,
}) => {
  const getTrackIcon = (name: string): string => {
    const nameLower = name.toLowerCase();
    if (nameLower.includes('vocals')) return 'vocals';
    if (nameLower.includes('kick')) return 'drums';
    if (nameLower.includes('snare')) return 'drums';
    if (nameLower.includes('hihat') || nameLower.includes('hi-hat')) return 'drums';
    if (nameLower.includes('cymbal')) return 'drums';
    if (nameLower.includes('tom')) return 'drums';
    if (nameLower.includes('drums')) return 'drums';
    if (nameLower.includes('bass')) return 'bass';
    if (nameLower.includes('guitar')) return 'guitar';
    if (nameLower.includes('piano')) return 'piano';
    return 'other';
  };

  const getTrackEmoji = (name: string): string => {
    const nameLower = name.toLowerCase();
    if (nameLower.includes('lead')) return '🎤';
    if (nameLower.includes('backing')) return '🎤';
    if (nameLower.includes('harmony')) return '🎤';
    if (nameLower.includes('vocals')) return '🎤';
    if (nameLower.includes('kick')) return '🥁';
    if (nameLower.includes('snare')) return '🥁';
    if (nameLower.includes('hihat') || nameLower.includes('hi-hat')) return '🥁';
    if (nameLower.includes('cymbal')) return '🥁';
    if (nameLower.includes('tom')) return '🥁';
    if (nameLower.includes('drums')) return '🥁';
    if (nameLower.includes('bass')) return '🎸';
    if (nameLower.includes('guitar')) return '🎸';
    if (nameLower.includes('piano')) return '🎹';
    return '🎵';
  };

  return (
    <TrackContainer $muted={muted} $soloed={soloed} $isChild={isChild}>
      <TrackIcon type={getTrackIcon(trackName)}>
        {getTrackEmoji(trackName)}
      </TrackIcon>
      <TrackName>{trackName.charAt(0).toUpperCase() + trackName.slice(1)}</TrackName>
      <VolumeControl>
        <VolumeLabel>Vol</VolumeLabel>
        <VolumeSlider
          type="range"
          min="0"
          max="100"
          value={volume * 100}
          onChange={(e) => onVolumeChange(Number(e.target.value))}
        />
        <VolumeValue>{Math.round(volume * 100)}%</VolumeValue>
      </VolumeControl>
      <ControlButtons>
        {canSplit && onSplit && (
          <SplitButton 
            $variant={trackName.toLowerCase() === 'vocals' ? 'vocals' : trackName.toLowerCase() === 'drums' ? 'drums' : undefined}
            $splitting={isSplitting}
            onClick={() => !isSplitting && onSplit(trackName)}
            title={`Split ${trackName}`}
            disabled={isSplitting}
          >
            {isSplitting ? (
              <>
                <SplitSpinner />
                Splitting...
              </>
            ) : (
              '→ Split'
            )}
          </SplitButton>
        )}
        <ControlButton $variant="solo" $active={soloed} onClick={onSolo}>
          Solo
        </ControlButton>
        <ControlButton $variant="mute" $active={muted} onClick={onMute}>
          {muted ? 'Unmute' : 'Mute'}
        </ControlButton>
      </ControlButtons>
    </TrackContainer>
  );
};

export default TrackControl;

