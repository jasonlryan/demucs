import React, { useState, useEffect, useRef, useMemo } from 'react';
import styled from 'styled-components';
import { colors, spacing, borderRadius, transitions } from '../../styles/theme';
import TrackControl from './TrackControl';
import TrackGroup from './TrackGroup';

const PlayerContainer = styled.div`
  margin-top: ${spacing.xl};
`;

const ControlsBar = styled.div`
  display: flex;
  gap: ${spacing.md};
  align-items: center;
  margin-bottom: ${spacing.lg};
  flex-wrap: wrap;
`;

const PlayButton = styled.button<{ $playing?: boolean }>`
  padding: 15px 40px;
  font-size: 18px;
  font-weight: 600;
  border: none;
  border-radius: ${borderRadius.lg};
  cursor: pointer;
  transition: ${transitions.default};
  background: ${props => props.$playing ? '#e74c3c' : colors.interactive.primary};
  color: ${colors.text.primary};
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
  }
`;

const ExportButton = styled.button`
  padding: 15px 40px;
  font-size: 18px;
  font-weight: 600;
  border: none;
  border-radius: ${borderRadius.lg};
  cursor: pointer;
  transition: ${transitions.default};
  background: #2ecc71;
  color: ${colors.text.primary};
  box-shadow: 0 4px 15px rgba(46, 204, 113, 0.4);

  &:hover {
    background: #27ae60;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(46, 204, 113, 0.6);
  }

  &:disabled {
    background: ${colors.interactive.disabled};
    cursor: not-allowed;
    opacity: 0.6;
  }
`;

const ProgressContainer = styled.div`
  margin-top: ${spacing.xl};
  padding: ${spacing.lg};
  background: ${colors.background.tertiary};
  border-radius: ${borderRadius.md};
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 10px;
  border-radius: 5px;
  background: ${colors.border.default};
  cursor: pointer;
  position: relative;
  margin-bottom: ${spacing.sm};
`;

const ProgressFill = styled.div<{ $percent: number }>`
  height: 100%;
  background: linear-gradient(90deg, ${colors.interactive.primary} 0%, #764ba2 100%);
  border-radius: 5px;
  width: ${props => props.$percent}%;
  transition: width 0.1s;
`;

const TimeDisplay = styled.div`
  display: flex;
  justify-content: space-between;
  font-weight: 600;
  color: ${colors.text.secondary};
  font-size: 14px;
`;

const TracksList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.sm};
`;

interface Track {
  name: string;
  url: string;
  volume: number;
  muted: boolean;
  soloed: boolean;
}

interface TrackPlayerProps {
  tracks: Track[];
  manifest?: any;
  jobId?: string;
  apiUrl?: string;
  onTracksUpdated?: (tracks: Track[], manifest: any) => void;
}

const TrackPlayer: React.FC<TrackPlayerProps> = ({ tracks, manifest, jobId, apiUrl = 'http://localhost:5001/api', onTracksUpdated }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [trackStates, setTrackStates] = useState<Record<string, { volume: number; muted: boolean; soloed: boolean }>>({});
  const [splittingTrack, setSplittingTrack] = useState<string | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourcesRef = useRef<Record<string, AudioBufferSourceNode>>({});
  const gainNodesRef = useRef<Record<string, GainNode>>({});
  const buffersRef = useRef<Record<string, AudioBuffer>>({});
  const startTimeRef = useRef<number>(0);
  const pauseTimeRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    // Initialize track states
    const initialStates: Record<string, { volume: number; muted: boolean; soloed: boolean }> = {};
    tracks.forEach(track => {
      initialStates[track.name] = {
        volume: track.volume ?? 1.0,
        muted: track.muted ?? false,
        soloed: track.soloed ?? false
      };
    });
    setTrackStates(initialStates);
  }, [tracks]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const loadAudio = async (track: Track): Promise<AudioBuffer | null> => {
    if (buffersRef.current[track.name]) {
      return buffersRef.current[track.name];
    }

    try {
      // Ensure URL is properly formatted
      let url = track.url;
      if (!url.startsWith('http')) {
        // If relative URL, construct full URL
        const baseUrl = apiUrl.replace(/\/api$/, '');
        url = url.startsWith('/api') 
          ? `http://localhost:5001${url}`
          : `${baseUrl}/api${url.startsWith('/') ? '' : '/'}${url}`;
      }
      
      const response = await fetch(url);
      if (!response.ok) {
        console.error(`Failed to load ${track.name} from ${url}: ${response.status} ${response.statusText}`);
        return null;
      }
      
      const arrayBuffer = await response.arrayBuffer();
      
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      
      const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
      buffersRef.current[track.name] = audioBuffer;
      
      if (audioBuffer.duration > duration) {
        setDuration(audioBuffer.duration);
      }
      
      return audioBuffer;
    } catch (error: any) {
      console.error(`Error decoding audio for ${track.name} (${track.url}):`, error);
      return null;
    }
  };

  const pause = () => {
    // Stop all sources
    Object.values(sourcesRef.current).forEach(source => {
      try {
        source.stop();
      } catch (e) {
        // Already stopped
      }
    });
    
    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    // Save current time for resume
    if (audioContextRef.current) {
      pauseTimeRef.current = audioContextRef.current.currentTime - startTimeRef.current;
    }
    
    // Clear source references but keep gain nodes
    sourcesRef.current = {};
    
    setIsPlaying(false);
  };

  const play = async () => {
    // Always stop any existing playback first to ensure only one instance
    if (isPlaying) {
      pause();
    }

    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume();
    }

    const currentTime = audioContextRef.current.currentTime;
    const offset = pauseTimeRef.current;

    // Load and start all tracks from current position
    const loadPromises = tracks.map(track => loadAudio(track));
    const buffers = await Promise.all(loadPromises);
    
    // Start all successfully loaded tracks
    for (let i = 0; i < tracks.length; i++) {
      const track = tracks[i];
      const buffer = buffers[i];
      
      if (!buffer) {
        console.warn(`Skipping ${track.name} - failed to load audio`);
        continue;
      }
      
      const source = audioContextRef.current.createBufferSource();
      source.buffer = buffer;
      
      // Reuse existing gain node or create new one
      let gainNode = gainNodesRef.current[track.name];
      if (!gainNode) {
        gainNode = audioContextRef.current.createGain();
        gainNode.connect(audioContextRef.current.destination);
        gainNodesRef.current[track.name] = gainNode;
      }
      
      // Always update gain node with current state
      const state = trackStates[track.name] || { volume: 1.0, muted: false, soloed: false };
      const hasSolo = Object.values(trackStates).some(s => s.soloed);
      if (hasSolo) {
        gainNode.gain.value = state.soloed && !state.muted ? state.volume : 0;
      } else {
        gainNode.gain.value = state.muted ? 0 : state.volume;
      }
      
      source.connect(gainNode);
      
      // Start from current offset position
      try {
        source.start(0, offset);
        sourcesRef.current[track.name] = source;

        // Handle when source ends
        source.onended = () => {
          delete sourcesRef.current[track.name];
          // If all sources ended, stop playback
          if (Object.keys(sourcesRef.current).length === 0) {
            setIsPlaying(false);
            setCurrentTime(duration);
            pauseTimeRef.current = duration;
            if (animationFrameRef.current) {
              cancelAnimationFrame(animationFrameRef.current);
              animationFrameRef.current = null;
            }
          }
        };
      } catch (error: any) {
        console.error(`Error starting source for ${track.name}:`, error);
      }
    }
    
    // If no tracks started, don't set playing state
    if (Object.keys(sourcesRef.current).length === 0) {
      console.warn('No tracks could be started');
      return;
    }

    startTimeRef.current = currentTime - offset;
    setIsPlaying(true);
    updateProgress();
  };

  const updateProgress = () => {
    if (isPlaying && audioContextRef.current) {
      const current = audioContextRef.current.currentTime - startTimeRef.current;
      setCurrentTime(Math.max(0, current));
      
      // Continue updating if still playing
      if (isPlaying && Object.keys(sourcesRef.current).length > 0) {
        animationFrameRef.current = requestAnimationFrame(updateProgress);
      } else {
        // All tracks finished
        setIsPlaying(false);
        setCurrentTime(duration);
        pauseTimeRef.current = duration;
        animationFrameRef.current = null;
      }
    } else {
      setCurrentTime(pauseTimeRef.current);
    }
  };

  const togglePlay = () => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      pause();
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(console.error);
      }
    };
  }, []);

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!duration) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percent = x / rect.width;
    const seekTime = Math.max(0, Math.min(percent * duration, duration));
    
    const wasPlaying = isPlaying;
    pause();
    pauseTimeRef.current = seekTime;
    setCurrentTime(seekTime);
    
    // If was playing, resume from seek position
    if (wasPlaying) {
      play();
    }
  };

  const applySoloState = (states: Record<string, { volume: number; muted: boolean; soloed: boolean }>) => {
    const hasSolo = Object.values(states).some(s => s.soloed);
    
    Object.keys(gainNodesRef.current).forEach(trackName => {
      const state = states[trackName];
      if (!state) return;
      
      if (hasSolo) {
        // If any track is soloed, mute all non-soloed tracks
        if (state.soloed) {
          // Soloed track plays at its volume (unless muted)
          gainNodesRef.current[trackName].gain.value = state.muted ? 0 : state.volume;
        } else {
          // Non-soloed tracks are muted
          gainNodesRef.current[trackName].gain.value = 0;
        }
      } else {
        // No solo active, restore normal mute/volume state
        gainNodesRef.current[trackName].gain.value = state.muted ? 0 : state.volume;
      }
    });
  };

  const handleTrackMute = (trackName: string) => {
    setTrackStates(prev => {
      const newMuted = !prev[trackName]?.muted;
      const newState = {
        ...prev,
        [trackName]: {
          ...prev[trackName],
          muted: newMuted,
          volume: prev[trackName]?.volume ?? 1.0,
          soloed: prev[trackName]?.soloed ?? false
        }
      };
      
      // Update gain node immediately with new state
      if (gainNodesRef.current[trackName]) {
        const hasSolo = Object.values(newState).some(s => s.soloed);
        if (hasSolo) {
          // Solo logic will handle this
          applySoloState(newState);
        } else {
          const state = newState[trackName];
          gainNodesRef.current[trackName].gain.value = state.muted ? 0 : state.volume;
        }
      }
      
      return newState;
    });
  };

  const handleTrackSolo = (trackName: string) => {
    setTrackStates(prev => {
      const newSoloed = !prev[trackName]?.soloed;
      const newState = {
        ...prev,
        [trackName]: {
          ...prev[trackName],
          soloed: newSoloed,
          volume: prev[trackName]?.volume ?? 1.0,
          muted: prev[trackName]?.muted ?? false
        }
      };
      
      // Apply solo state to all gain nodes
      applySoloState(newState);
      
      return newState;
    });
  };

  const handleTrackVolume = (trackName: string, volume: number) => {
    const volumeValue = volume / 100;
    setTrackStates(prev => {
      const newState = {
        ...prev,
        [trackName]: {
          ...prev[trackName],
          volume: volumeValue,
          muted: prev[trackName]?.muted ?? false,
          soloed: prev[trackName]?.soloed ?? false
        }
      };
      
      // Update gain node immediately
      if (gainNodesRef.current[trackName]) {
        const state = newState[trackName];
        const hasSolo = Object.values(newState).some(s => s.soloed);
        
        if (hasSolo) {
          // Solo logic will handle this
          applySoloState(newState);
        } else {
          // Normal volume update (respect mute)
          gainNodesRef.current[trackName].gain.value = state.muted ? 0 : volumeValue;
        }
      }
      
      return newState;
    });
  };

  const handleSplit = async (trackName: string) => {
    if (!jobId) {
      alert('No job ID available');
      return;
    }

    const trackLower = trackName.toLowerCase();
    const endpoint = trackLower === 'vocals' 
      ? `${apiUrl}/split-vocals/${jobId}`
      : trackLower === 'drums'
      ? `${apiUrl}/split-drums/${jobId}`
      : null;

    if (!endpoint) {
      alert('Split only available for vocals and drums');
      return;
    }

    setSplittingTrack(trackName);

    try {
      const response = await fetch(endpoint, {
        method: 'POST'
      });

      if (!response.ok) {
        const error = await response.json();
        const errorMessage = error.error || `${trackName} split failed`;
        const note = error.note ? `\n\n${error.note}` : '';
        throw new Error(`${errorMessage}${note}`);
      }

      const splitManifest = await response.json();

      // Merge child splits into current manifest
      if (manifest && splitManifest.child_splits) {
        if (!manifest.child_splits) {
          manifest.child_splits = {};
        }
        Object.assign(manifest.child_splits, splitManifest.child_splits);
      }

      // Reload tracks from updated manifest
      const updatedTracks: Track[] = [...tracks];

      // Add child tracks from split
      if (splitManifest.child_splits && splitManifest.child_splits[trackName]) {
        const childStems = splitManifest.child_splits[trackName];
        if (Array.isArray(childStems)) {
          for (const childStem of childStems) {
            const childName = typeof childStem === 'string' 
              ? `${trackName}_${childStem}`
              : `${trackName}_${childStem.name}`;
            
            // Use URL from manifest if available, otherwise construct it
            let childUrl: string;
            if (typeof childStem === 'string') {
              // Construct URL - apiUrl already includes /api
              const baseUrl = apiUrl.replace(/\/api$/, '');
              childUrl = `${baseUrl}/api/stems/${jobId}/${trackName}/${childStem}`;
            } else {
              // Use URL from manifest
              if (childStem.url) {
                if (childStem.url.startsWith('http')) {
                  childUrl = childStem.url;
                } else if (childStem.url.startsWith('/api')) {
                  childUrl = `http://localhost:5001${childStem.url}`;
                } else {
                  const baseUrl = apiUrl.replace(/\/api$/, '');
                  childUrl = `${baseUrl}/api${childStem.url.startsWith('/') ? '' : '/'}${childStem.url}`;
                }
              } else {
                const baseUrl = apiUrl.replace(/\/api$/, '');
                childUrl = `${baseUrl}/api/stems/${jobId}/${trackName}/${childStem.name}`;
              }
            }
            
            updatedTracks.push({
              name: childName,
              url: childUrl,
              volume: 1.0,
              muted: false,
              soloed: false
            });
          }
        }
      }

      if (onTracksUpdated) {
        onTracksUpdated(updatedTracks, manifest);
      }

      setSplittingTrack(null);
    } catch (error: any) {
      setSplittingTrack(null);
      // Show error in a more user-friendly way
      const errorMsg = error.message || `Error splitting ${trackName}`;
      alert(errorMsg);
      console.error('Split error:', error);
    }
  };

  const handleExport = async () => {
    // TODO: Implement export functionality
    alert('Export functionality coming soon!');
  };

  // Organize tracks into parent/child groups
  const organizedTracks = useMemo(() => {
    const parentTracks: Track[] = [];
    const childTracksMap: Record<string, Track[]> = {};
    const standaloneTracks: Track[] = [];

    tracks.forEach(track => {
      if (track.name === 'mix') {
        standaloneTracks.push(track);
      } else if (track.name.includes('_')) {
        // Child track - extract parent name
        const parentName = track.name.split('_')[0];
        if (!childTracksMap[parentName]) {
          childTracksMap[parentName] = [];
        }
        childTracksMap[parentName].push(track);
      } else {
        // Parent track
        parentTracks.push(track);
      }
    });

    return { parentTracks, childTracksMap, standaloneTracks };
  }, [tracks]);

  if (tracks.length === 0) {
    return null;
  }

  return (
    <PlayerContainer>
      <ControlsBar>
        <PlayButton $playing={isPlaying} onClick={togglePlay}>
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </PlayButton>
        <ExportButton onClick={handleExport} disabled={tracks.length === 0}>
          💾 Export Mixed Audio
        </ExportButton>
      </ControlsBar>

      <TracksList>
        {/* Standalone tracks (like mix) */}
        {organizedTracks.standaloneTracks.map(track => (
          <TrackControl
            key={track.name}
            trackName={track.name}
            volume={trackStates[track.name]?.volume ?? 1.0}
            muted={trackStates[track.name]?.muted ?? false}
            soloed={trackStates[track.name]?.soloed ?? false}
            onMute={() => handleTrackMute(track.name)}
            onSolo={() => handleTrackSolo(track.name)}
            onVolumeChange={(vol) => handleTrackVolume(track.name, vol)}
          />
        ))}

        {/* Parent tracks with potential children */}
        {organizedTracks.parentTracks.map(parentTrack => {
          const childTracks = organizedTracks.childTracksMap[parentTrack.name] || [];
          
          if (childTracks.length > 0) {
            // Render as group with collapsible children
            return (
              <TrackGroup
                key={parentTrack.name}
                parentTrack={parentTrack}
                childTracks={childTracks}
                trackStates={trackStates}
                splittingTrack={splittingTrack}
                onMute={handleTrackMute}
                onSolo={handleTrackSolo}
                onVolumeChange={handleTrackVolume}
                onSplit={handleSplit}
              />
            );
          } else {
            // Render as standalone track
            const trackLower = parentTrack.name.toLowerCase();
            const canSplit = trackLower === 'vocals' || trackLower === 'drums';
            const isSplitting = splittingTrack === parentTrack.name;
            
            return (
              <TrackControl
                key={parentTrack.name}
                trackName={parentTrack.name}
                volume={trackStates[parentTrack.name]?.volume ?? 1.0}
                muted={trackStates[parentTrack.name]?.muted ?? false}
                soloed={trackStates[parentTrack.name]?.soloed ?? false}
                onMute={() => handleTrackMute(parentTrack.name)}
                onSolo={() => handleTrackSolo(parentTrack.name)}
                onVolumeChange={(vol) => handleTrackVolume(parentTrack.name, vol)}
                onSplit={handleSplit}
                canSplit={canSplit}
                isSplitting={isSplitting}
              />
            );
          }
        })}
      </TracksList>

      <ProgressContainer>
        <ProgressBar onClick={handleSeek}>
          <ProgressFill $percent={duration > 0 ? (currentTime / duration) * 100 : 0} />
        </ProgressBar>
        <TimeDisplay>
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </TimeDisplay>
      </ProgressContainer>
    </PlayerContainer>
  );
};

export default TrackPlayer;

