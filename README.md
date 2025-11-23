# Audio Separation Project

A full-stack audio separation application with a React frontend and Flask backend.

## Project Structure

```
.
├── src/                    # React frontend source
│   ├── components/         # React components
│   ├── styles/             # Design system & styles
│   └── App.tsx            # Main React app
├── public/                 # Static files
├── app.py                 # Flask backend API
├── separate_audio.py      # Audio separation script
├── package.json           # Node.js dependencies
└── tsconfig.json          # TypeScript config
```

## Quick Start

### Development Mode

**Terminal 1 - React Frontend:**
```bash
npm start
```
Runs React dev server at http://localhost:3000 (proxies API calls to Flask)

**Terminal 2 - Flask Backend:**
```bash
python app.py
```
Runs Flask API at http://localhost:5001

### Production Build

1. Build React app:
```bash
npm run build
```

2. Run Flask server (serves React build):
```bash
python app.py
```

The Flask server will serve the React app at http://localhost:5001

## Features

- 🎨 Modern React UI with dark theme
- 🎵 Audio separation using Demucs
- 🎤 **Vocal Separation**: Split vocals into lead and backing vocals using spectral analysis
- 🥁 **Drum Separation**: Split drums into kick, snare, hihat, cymbals, etc.
- 🔌 RESTful API backend
- 📦 Support for multiple splitters (Demucs, Spleeter, etc.)
- 🎛️ Track mixing with mute, solo, volume controls
- 📁 Collapsible track groups for parent/child tracks
- 💾 Export individual stems or mixed audio

## API Endpoints

- `GET /api/splitters` - Get available splitters and models
- `POST /api/upload` - Upload audio file
- `POST /api/separate/<job_id>` - Run separation with selected splitter/model
- `POST /api/split-vocals/<job_id>` - Split vocals into lead/backing
- `POST /api/split-drums/<job_id>` - Split drums into parts (kick, snare, etc.)
- `GET /api/stems/<job_id>/<stem_path>` - Get stem file (supports nested paths)
- `POST /api/load-project` - Load existing separated project
- `POST /api/analyze/<job_id>` - Analyze stems and suggest labels

## Tech Stack

**Frontend:**
- React 18
- TypeScript
- Styled Components
- Lucide React (Icons)

**Backend:**
- Flask
- Demucs (audio separation)
- Librosa (audio analysis & vocal separation)
- SoundFile (audio I/O)
- SciPy (signal processing)
- NumPy (numerical computing)

## Vocal Separation

See [VOCAL_SEPARATION.md](VOCAL_SEPARATION.md) for detailed documentation on the vocal separation feature.

The vocal separation uses spectral analysis to split vocals into:
- **Lead Vocals**: Main vocal track (centered, clear)
- **Backing Vocals**: Harmonies, ad-libs, background vocals

## Drum Separation

Drum separation splits drums into individual parts:
- **Kick**: Low-frequency drum hits
- **Snare**: Snare drum hits
- **Hihat**: Hi-hat cymbals
- **Cymbals**: Crash, ride, and other cymbals
- **Toms**: Tom-tom drums

Uses frequency-based separation and spectral analysis techniques.

## Development

The React app proxies API requests to the Flask backend during development. Make sure both servers are running for full functionality.
