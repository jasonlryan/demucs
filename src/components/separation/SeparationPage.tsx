import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { colors, spacing, borderRadius, transitions } from '../../styles/theme';
import PageHeader from '../layout/PageHeader';
import Section from './Section';
import LoadSection from './LoadSection';
import TrackPlayer from '../player/TrackPlayer';
import { Icons, createIcon } from '../../utils/icons';

const UploadArea = styled.div<{ $dragover?: boolean }>`
  margin-bottom: ${spacing.lg};
  padding: ${spacing.xl};
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 2px dashed ${props => props.$dragover ? colors.interactive.primary : colors.border.default};
  border-radius: ${borderRadius.lg};
  text-align: center;
  cursor: pointer;
  transition: ${transitions.default};
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;

  &:hover {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
    border-color: ${colors.interactive.primary};
    transform: translateY(-2px);
  }
`;

const UploadIcon = styled.div`
  font-size: 40px;
  margin-bottom: ${spacing.md};
`;

const UploadText = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: ${colors.interactive.primary};
  margin-bottom: ${spacing.xs};
`;

const UploadHint = styled.div`
  font-size: 12px;
  color: ${colors.text.secondary};
`;

const FileInput = styled.input`
  display: none;
`;

const ChooseFileButton = styled.button`
  padding: 12px 30px;
  font-size: 16px;
  font-weight: 600;
  border: 2px solid ${colors.interactive.primary};
  background: ${colors.background.tertiary};
  color: ${colors.interactive.primary};
  border-radius: ${borderRadius.md};
  cursor: pointer;
  transition: ${transitions.default};
  margin-top: ${spacing.lg};

  &:hover {
    background: ${colors.interactive.primary};
    color: ${colors.text.primary};
    transform: translateY(-2px);
  }
`;

const SplitterSelector = styled.div`
  display: flex;
  gap: ${spacing.lg};
  align-items: center;
  flex-wrap: wrap;
  margin-top: ${spacing.lg};
`;

const SelectWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.sm};
`;

const SelectLabel = styled.label`
  font-weight: 600;
  color: ${colors.interactive.primary};
  font-size: 14px;
`;

const Select = styled.select`
  padding: 10px 15px;
  border: 2px solid ${colors.interactive.primary};
  background: ${colors.background.tertiary};
  color: ${colors.text.primary};
  border-radius: ${borderRadius.md};
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  min-width: 200px;

  &:focus {
    outline: none;
    border-color: ${colors.interactive.hover};
  }
`;

const SeparateButton = styled.button<{ disabled?: boolean }>`
  padding: 15px 40px;
  font-size: 18px;
  font-weight: 600;
  border: none;
  border-radius: ${borderRadius.lg};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  transition: ${transitions.default};
  background: ${props => props.disabled ? colors.interactive.disabled : `linear-gradient(135deg, ${colors.interactive.primary} 0%, #764ba2 100%)`};
  color: ${colors.text.primary};
  box-shadow: ${props => props.disabled ? 'none' : `0 4px 15px rgba(102, 126, 234, 0.4)`};
  margin-top: ${spacing.lg};
  opacity: ${props => props.disabled ? 0.6 : 1};

  &:hover {
    ${props => !props.disabled && `
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    `}
  }
`;

const ProgressInfo = styled.div<{ $active?: boolean }>`
  margin-top: ${spacing.lg};
  padding: ${spacing.lg};
  background: ${colors.background.tertiary};
  border-radius: ${borderRadius.md};
  display: ${props => props.$active ? 'block' : 'none'};
  text-align: center;
  color: ${colors.text.secondary};
`;

const Spinner = styled.div`
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(102, 126, 234, 0.3);
  border-radius: 50%;
  border-top-color: ${colors.interactive.primary};
  animation: spin 1s linear infinite;
  margin-right: ${spacing.sm};

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const StatusMessage = styled.div<{ type?: string }>`
  margin-top: ${spacing.lg};
  padding: ${spacing.md};
  border-radius: ${borderRadius.md};
  font-weight: 600;
  text-align: center;
  background: ${props => 
    props.type === 'error' ? 'rgba(244, 67, 54, 0.2)' :
    props.type === 'success' ? 'rgba(76, 175, 80, 0.2)' :
    'rgba(255, 193, 7, 0.2)'
  };
  color: ${props => 
    props.type === 'error' ? '#F44336' :
    props.type === 'success' ? '#4CAF50' :
    '#FFC107'
  };
`;

interface Splitter {
  id: string;
  name: string;
  description: string;
  models: Array<{ id: string; name: string; stems: string[] }>;
}

const SeparationPage: React.FC = () => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [splitters, setSplitters] = useState<Record<string, Splitter>>({});
  const [selectedSplitter, setSelectedSplitter] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState<{ message: string; type: 'success' | 'error' | 'loading' } | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loadedTracks, setLoadedTracks] = useState<Array<{ name: string; url: string; volume: number; muted: boolean; soloed: boolean }>>([]);
  const [manifest, setManifest] = useState<any>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

  useEffect(() => {
    loadSplitters();
  }, []);

  const loadSplitters = async () => {
    try {
      const response = await fetch(`${API_URL}/splitters`);
      if (response.ok) {
        const data = await response.json();
        setSplitters(data.splitters || {});
        // Auto-select first splitter
        const firstSplitter = Object.keys(data.splitters || {})[0];
        if (firstSplitter) {
          setSelectedSplitter(firstSplitter);
          const firstModel = data.splitters[firstSplitter]?.models[0]?.id;
          if (firstModel) {
            setSelectedModel(firstModel);
          }
        }
      }
    } catch (error) {
      console.error('Error loading splitters:', error);
    }
  };

  const handleFileSelect = (file: File) => {
    if (file) {
      const validTypes = ['audio/mpeg', 'audio/wav', 'audio/aiff', 'audio/x-aiff', 'audio/flac', 'audio/mp4', 'audio/ogg'];
      const validExtensions = ['.mp3', '.wav', '.aiff', '.aif', '.flac', '.m4a', '.ogg'];
      const fileName = file.name.toLowerCase();
      const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));

      if (!hasValidExtension && !validTypes.includes(file.type)) {
        setStatus({ message: 'Invalid file type. Please upload MP3, WAV, AIFF, or FLAC.', type: 'error' });
        return;
      }

      setUploadedFile(file);
      setStatus(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleSeparate = async () => {
    if (!uploadedFile || !selectedSplitter || !selectedModel) {
      setStatus({ message: 'Please select a file, splitter, and model', type: 'error' });
      return;
    }

    setIsProcessing(true);
    setStatus({ message: 'Uploading file...', type: 'loading' });

    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const uploadResponse = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData
      });

      if (!uploadResponse.ok) {
        const error = await uploadResponse.json();
        throw new Error(error.error || 'Upload failed');
      }

      const uploadData = await uploadResponse.json();
      const newJobId = uploadData.job_id;
      setJobId(newJobId);

      setStatus({ message: `Separating audio with ${splitters[selectedSplitter]?.name} (${selectedModel})... This may take a few minutes.`, type: 'loading' });

      // Start separation
      const separateResponse = await fetch(`${API_URL}/separate/${newJobId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          splitter: selectedSplitter,
          model: selectedModel 
        })
      });

      if (!separateResponse.ok) {
        const error = await separateResponse.json();
        throw new Error(error.error || 'Separation failed');
      }

      const manifestData = await separateResponse.json();
      setManifest(manifestData);
      setCurrentJobId(manifestData.job_id);
      
      setStatus({ 
        message: `✨ Successfully separated into ${manifestData.stems?.length || 0} stems!`, 
        type: 'success' 
      });

      // Load stems into player
      const tracks = manifestData.stems?.map((stem: any) => ({
        name: stem.name,
        url: stem.url.startsWith('http') ? stem.url : `${API_URL}${stem.url}`,
        volume: 1.0,
        muted: false,
        soloed: false
      })) || [];
      
      setLoadedTracks(tracks);

    } catch (error: any) {
      setStatus({ message: `Error: ${error.message}`, type: 'error' });
      console.error('Separation error:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const availableModels = selectedSplitter ? (splitters[selectedSplitter]?.models || []) : [];

  return (
    <>
      <PageHeader 
        title="🎵 Audio Separation" 
        subtitle="Upload an audio file and select a separation model" 
      />

      <Section title="Upload Audio File">
        <UploadArea
          $dragover={isDragging}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <UploadIcon>🎵</UploadIcon>
          <UploadText>
            {uploadedFile ? `Selected: ${uploadedFile.name}` : 'Drag & drop your audio file here'}
          </UploadText>
          <UploadHint>
            {uploadedFile 
              ? `Size: ${(uploadedFile.size / 1024 / 1024).toFixed(2)} MB`
              : 'Supports MP3, WAV, AIFF, FLAC (max 500MB)'
            }
          </UploadHint>
          <FileInput
            id="file-input"
            type="file"
            accept=".mp3,.wav,.aiff,.aif,.flac,.m4a,.ogg"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileSelect(file);
            }}
          />
          <ChooseFileButton>📁 Choose File</ChooseFileButton>
        </UploadArea>

        {Object.keys(splitters).length > 0 && (
          <SplitterSelector>
            <SelectWrapper>
              <SelectLabel>Splitter:</SelectLabel>
              <Select
                value={selectedSplitter}
                onChange={(e) => {
                  setSelectedSplitter(e.target.value);
                  const splitter = splitters[e.target.value];
                  if (splitter?.models[0]) {
                    setSelectedModel(splitter.models[0].id);
                  }
                }}
              >
                <option value="">Select splitter...</option>
                {Object.entries(splitters).map(([id, splitter]) => (
                  <option key={id} value={id}>
                    {splitter.name} - {splitter.description}
                  </option>
                ))}
              </Select>
            </SelectWrapper>

            <SelectWrapper>
              <SelectLabel>Model:</SelectLabel>
              <Select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={!selectedSplitter}
              >
                <option value="">Select model...</option>
                {availableModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </Select>
            </SelectWrapper>
          </SplitterSelector>
        )}

        {uploadedFile && selectedSplitter && selectedModel && (
          <SeparateButton
            onClick={handleSeparate}
            disabled={isProcessing}
          >
            {isProcessing ? '✨ Processing...' : '✨ Separate Audio into Stems'}
          </SeparateButton>
        )}

        <ProgressInfo $active={isProcessing}>
          <Spinner />
          <span>{status?.message}</span>
        </ProgressInfo>

        {status && status.type !== 'loading' && (
          <StatusMessage type={status.type}>
            {status.message}
          </StatusMessage>
        )}
      </Section>

      <LoadSection
        onLoadTracks={setLoadedTracks}
        onLoadManifest={setManifest}
        onJobIdChange={setCurrentJobId}
        apiUrl={API_URL}
      />

      {loadedTracks.length > 0 && (
        <Section title="Audio Player">
          <TrackPlayer 
            tracks={loadedTracks} 
            manifest={manifest}
            jobId={currentJobId || undefined}
            apiUrl={API_URL}
            onTracksUpdated={(updatedTracks, updatedManifest) => {
              setLoadedTracks(updatedTracks);
              if (updatedManifest) {
                setManifest(updatedManifest);
              }
            }}
          />
        </Section>
      )}
    </>
  );
};

export default SeparationPage;
