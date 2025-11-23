# Vocal Separation Feature

## Overview

The vocal separation feature splits vocals into **lead vocals** and **backing vocals/harmonies** using spectral analysis techniques.

## How It Works

When you click "→ Split" on a vocals track, the system:

1. **Loads the vocals stem** from the initial separation
2. **Applies spectral analysis** using librosa to separate:
   - **Lead Vocals**: Centered, mono-like vocals with clear fundamental frequencies
   - **Backing Vocals**: Panned, stereo vocals with harmonies and reverb

## Separation Methods

The implementation uses a combination of techniques:

### 1. Center Channel Extraction
- Lead vocals are typically centered in the stereo field (L+R)
- Backing vocals are often panned (L-R)
- Extracts center channel for lead, side channels for backing

### 2. Spectral Analysis
- Uses harmonic-percussive separation
- Analyzes spectral centroid to identify lead vs backing characteristics
- Lead vocals: More consistent spectral centroid, clearer formants
- Backing vocals: More diffuse, higher variance in spectral content

### 3. Frequency-Based Masking
- Creates frequency masks based on spectral characteristics
- Separates frequency bands that correspond to lead vs backing vocals

## Output

After separation, you'll get:
- **`vocals_lead`**: The main lead vocal track
- **`vocals_backing`**: Backing vocals, harmonies, and ad-libs

Both tracks appear nested under the parent "vocals" track and can be:
- Played independently
- Muted/soloed separately
- Volume adjusted individually
- Exported separately

## Requirements

The vocal separation feature requires:
- `librosa` - Audio analysis library
- `soundfile` - Audio file I/O
- `scipy` - Scientific computing (for signal processing)
- `numpy` - Numerical computing

Install with:
```bash
pip install librosa soundfile scipy numpy
```

## Usage

1. **Separate your audio** using any Demucs model
2. **Find the vocals track** in the track list
3. **Click "→ Split"** button on the vocals track
4. **Wait for processing** (usually takes 10-30 seconds)
5. **Expand the vocals track** to see lead and backing vocals
6. **Play, mute, solo, or adjust volume** for each part independently

## Technical Details

### Algorithm

1. Load vocals audio at 44.1kHz sample rate
2. Convert to stereo if mono
3. Extract center channel: `(L + R) / 2` for lead vocals
4. Extract side channel: `(L - R) / 2` for backing vocals
5. Apply spectral analysis using STFT (Short-Time Fourier Transform)
6. Create frequency masks based on spectral centroid analysis
7. Blend center extraction (70%) with spectral separation (30%)
8. Normalize outputs to prevent clipping
9. Save as WAV files

### File Locations

- Input: `separated/{model}/{job_id}/vocals.mp3`
- Output: `separated/vocal_splits/{job_id}/lead.wav` and `backing.wav`
- Served via: `/api/stems/{job_id}/vocals/lead` and `/vocals/backing`

## Limitations

- Works best with stereo vocal tracks
- Quality depends on how well vocals were separated initially
- May not perfectly separate overlapping vocals
- Processing time increases with audio length

## Future Improvements

Potential enhancements:
- Use deep learning models specifically trained for vocal separation
- Add support for separating harmonies into individual parts
- Implement real-time preview
- Add quality settings (fast vs high quality)

