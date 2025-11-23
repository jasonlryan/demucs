import React, { useState } from 'react';
import styled from 'styled-components';
import { colors, spacing, borderRadius, transitions } from '../../styles/theme';
import Section from './Section';

const DirectorySelector = styled.div`
  margin-bottom: ${spacing.lg};
  padding: ${spacing.lg};
  background: ${colors.background.tertiary};
  border-radius: ${borderRadius.md};
  border-left: 4px solid #2ecc71;
`;

const DirectoryLabel = styled.label`
  display: block;
  margin-bottom: ${spacing.sm};
  font-weight: 600;
  color: ${colors.text.primary};
`;

const DirectoryInputRow = styled.div`
  display: flex;
  gap: ${spacing.sm};
  align-items: center;
  margin-bottom: ${spacing.md};
`;

const DirectoryInput = styled.input`
  flex: 1;
  padding: 10px;
  border: 1px solid ${colors.border.default};
  border-radius: ${borderRadius.md};
  background: ${colors.background.secondary};
  color: ${colors.text.primary};
  font-family: monospace;
  font-size: 14px;

  &:focus {
    outline: none;
    border-color: ${colors.interactive.primary};
  }
`;

const BrowseButton = styled.button`
  padding: 10px 20px;
  background: #3498db;
  color: ${colors.text.primary};
  border: none;
  border-radius: ${borderRadius.md};
  cursor: pointer;
  font-weight: 600;
  transition: ${transitions.default};

  &:hover {
    background: #2980b9;
    transform: translateY(-1px);
  }
`;

const LoadButton = styled.button`
  padding: 10px 20px;
  background: #2ecc71;
  color: ${colors.text.primary};
  border: none;
  border-radius: ${borderRadius.md};
  cursor: pointer;
  font-weight: 600;
  transition: ${transitions.default};

  &:hover {
    background: #27ae60;
    transform: translateY(-1px);
  }
`;

const FolderBrowser = styled.div<{ $visible?: boolean }>`
  display: ${props => props.$visible ? 'block' : 'none'};
  margin-top: ${spacing.md};
  padding: ${spacing.lg};
  background: ${colors.background.secondary};
  border: 2px solid #3498db;
  border-radius: ${borderRadius.md};
  max-height: 300px;
  overflow-y: auto;
`;

const FolderBrowserTitle = styled.div`
  margin-bottom: ${spacing.sm};
  font-weight: 600;
  color: #3498db;
`;

const FolderItem = styled.div`
  padding: 12px;
  margin: 5px 0;
  background: ${colors.background.tertiary};
  border-radius: ${borderRadius.sm};
  cursor: pointer;
  transition: ${transitions.default};
  border: 2px solid transparent;

  &:hover {
    background: ${colors.background.active};
    border-color: #3498db;
  }
`;

const AddStemSection = styled.div`
  margin-bottom: ${spacing.md};
`;

const AddStemButton = styled.button`
  padding: 10px 20px;
  background: #3498db;
  color: ${colors.text.primary};
  border: none;
  border-radius: ${borderRadius.md};
  cursor: pointer;
  font-weight: 600;
  transition: ${transitions.default};

  &:hover {
    background: #2980b9;
    transform: translateY(-1px);
  }
`;

const FileInput = styled.input`
  display: none;
`;

interface LoadSectionProps {
  onLoadTracks: (tracks: Array<{ name: string; url: string; volume: number; muted: boolean; soloed: boolean }>) => void;
  onLoadManifest: (manifest: any) => void;
  onJobIdChange?: (jobId: string | null) => void;
  apiUrl: string;
}

const LoadSection: React.FC<LoadSectionProps> = ({ onLoadTracks, onLoadManifest, onJobIdChange, apiUrl }) => {
  const [directoryPath, setDirectoryPath] = useState('/Users/jasonryan/Documents/sound2/separated/htdemucs_6s');
  const [showFolderBrowser, setShowFolderBrowser] = useState(false);
  const [folders, setFolders] = useState<Array<{ name: string; path: string }>>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadUrl = (url: string): string => {
    if (!url.startsWith('http')) {
      if (url.startsWith('/api')) {
        return `http://localhost:5001${url}`;
      } else {
        return `${apiUrl}${url}`;
      }
    }
    return url;
  };

  const loadFromManifest = async (manifest: any) => {
    if (!manifest) return;

    setIsLoading(true);
    try {
      const tracks: Array<{ name: string; url: string; volume: number; muted: boolean; soloed: boolean }> = [];

      // Load mix track if available
      if (manifest.mix && manifest.mix.url) {
        tracks.push({
          name: 'mix',
          url: loadUrl(manifest.mix.url),
          volume: 1.0,
          muted: false,
          soloed: false
        });
      }

      // Load stems - handle both array format and object format
      if (manifest.stems) {
        if (Array.isArray(manifest.stems)) {
          // Array format: [{name: 'vocals', url: '...'}, ...]
          for (const stem of manifest.stems) {
            let stemUrl: string;
            if (typeof stem === 'string') {
              // Construct URL - ensure we don't double /api
              const baseUrl = apiUrl.replace(/\/api$/, '');
              stemUrl = `${baseUrl}/api/stems/${manifest.job_id}/${stem}`;
            } else {
              stemUrl = loadUrl(stem.url || stem);
            }
            tracks.push({
              name: typeof stem === 'string' ? stem : stem.name,
              url: stemUrl,
              volume: 1.0,
              muted: false,
              soloed: false
            });
          }
        } else {
          // Object format: {vocals: {...}, drums: {...}}
          for (const [stemName, stemData] of Object.entries(manifest.stems)) {
            const stem = stemData as any;
            let stemUrl: string;
            if (stem.url) {
              stemUrl = loadUrl(stem.url);
            } else {
              const baseUrl = apiUrl.replace(/\/api$/, '');
              stemUrl = `${baseUrl}/api/stems/${manifest.job_id}/${stemName}`;
            }
            tracks.push({
              name: stemName,
              url: stemUrl,
              volume: 1.0,
              muted: false,
              soloed: false
            });
          }
        }
      }

      // Load child splits if available
      if (manifest.child_splits) {
        for (const [parentTrack, childData] of Object.entries(manifest.child_splits as Record<string, any>)) {
          if (Array.isArray(childData)) {
            // Array of child stems
            for (const childStem of childData) {
              const childName = typeof childStem === 'string' 
                ? `${parentTrack}_${childStem}`
                : `${parentTrack}_${childStem.name}`;
              let childUrl: string;
              if (typeof childStem === 'string') {
                const baseUrl = apiUrl.replace(/\/api$/, '');
                childUrl = `${baseUrl}/api/stems/${manifest.job_id}/${parentTrack}/${childStem}`;
              } else {
                childUrl = loadUrl(childStem.url || childStem);
              }
              tracks.push({
                name: childName,
                url: childUrl,
                volume: 1.0,
                muted: false,
                soloed: false
              });
            }
          } else if (childData && typeof childData === 'object' && 'stems' in childData) {
            // Object with stems array
            for (const childStem of childData.stems) {
              tracks.push({
                name: `${parentTrack}_${childStem.name}`,
                url: loadUrl(childStem.url),
                volume: 1.0,
                muted: false,
                soloed: false
              });
            }
          }
        }
      }

      onLoadTracks(tracks);
      onLoadManifest(manifest);
      if (onJobIdChange && manifest.job_id) {
        onJobIdChange(manifest.job_id);
      }
    } catch (error) {
      console.error('Error loading from manifest:', error);
      alert(`Error loading tracks: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadFromDirectory = async () => {
    if (!directoryPath.trim()) {
      alert('Please enter a directory path');
      return;
    }

    setIsLoading(true);
    try {
      // Use load-project endpoint
      const response = await fetch(`${apiUrl}/load-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: directoryPath })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to load project');
      }

      const manifest = await response.json();
      await loadFromManifest(manifest);
    } catch (error: any) {
      alert(`Error loading: ${error.message}`);
      console.error('Load error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const browseFolders = async () => {
    if (!directoryPath.trim()) {
      alert('Please enter a base directory path first');
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/browse-folders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: directoryPath })
      });

      const data = await response.json();
      if (!response.ok) {
        alert(`Error: ${data.error}`);
        return;
      }

      setFolders(data.folders || []);
      setShowFolderBrowser(true);
    } catch (error: any) {
      alert(`Browse error: ${error.message}`);
      console.error('Browse error:', error);
    }
  };

  const handleFolderSelect = (folderPath: string) => {
    setDirectoryPath(folderPath);
    setShowFolderBrowser(false);
    loadFromDirectory();
  };

  const handleAddStem = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      onLoadTracks([{
        name: file.name.replace(/\.[^/.]+$/, ''),
        url: url,
        volume: 1.0,
        muted: false,
        soloed: false
      }]);
    }
  };

  return (
    <Section title="Load Existing Audio">
      <DirectorySelector>
        <DirectoryLabel>Load existing separated audio:</DirectoryLabel>
        <DirectoryInputRow>
          <DirectoryInput
            type="text"
            value={directoryPath}
            onChange={(e) => setDirectoryPath(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                loadFromDirectory();
              }
            }}
            placeholder="separated/htdemucs_6s/job_id"
          />
          <BrowseButton onClick={browseFolders}>📁 Browse</BrowseButton>
          <LoadButton onClick={loadFromDirectory} disabled={isLoading}>
            {isLoading ? 'Loading...' : 'Load'}
          </LoadButton>
        </DirectoryInputRow>

        <FolderBrowser $visible={showFolderBrowser}>
          <FolderBrowserTitle>Select a song folder:</FolderBrowserTitle>
          {folders.length === 0 ? (
            <div style={{ color: colors.text.tertiary, padding: spacing.sm }}>
              No subdirectories found
            </div>
          ) : (
            folders.map((folder) => (
              <FolderItem
                key={folder.path}
                onClick={() => handleFolderSelect(folder.path)}
              >
                📁 {folder.name}
              </FolderItem>
            ))
          )}
        </FolderBrowser>
      </DirectorySelector>

      <AddStemSection>
        <FileInput
          id="add-stem-input"
          type="file"
          accept=".mp3,.wav,.aiff,.aif,.flac,.m4a,.ogg"
          onChange={handleAddStem}
        />
        <AddStemButton onClick={() => document.getElementById('add-stem-input')?.click()}>
          ➕ Add Stem
        </AddStemButton>
      </AddStemSection>
    </Section>
  );
};

export default LoadSection;

