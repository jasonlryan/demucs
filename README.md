# Demucs Audio Separator & Editor

A web-based audio separation and mixing tool that supports multiple separation libraries (Demucs, Spleeter, MDX23) with an intuitive interface for loading, playing, and exporting separated stems.

## Features

- **Multiple Splitter Support**: Choose from Demucs (4-stem/6-stem), Spleeter, or MDX23
- **Automatic Project Loading**: Upload → Separate → Auto-load workflow
- **Track Hierarchy**: Mix track + parent stems + collapsible child tracks (from secondary splits)
- **Real-time Playback**: Mix and play stems with individual volume controls, solo, and mute
- **Export**: Export individual stems or the mixed audio
- **Project Management**: Load existing separated projects or add individual stems

## Requirements

- Python 3.7+
- Flask
- One or more separation libraries:
  - Demucs: `pip install demucs`
  - Spleeter: `pip install spleeter`
  - MDX23: `pip install mdx23`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jasonlryan/demucs.git
cd demucs
```

2. Install dependencies:
```bash
pip install flask flask-cors librosa numpy
```

3. Install at least one separation library (e.g., Demucs):
```bash
pip install demucs
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser to `http://localhost:5001`

3. Upload an audio file or load an existing separated project:
   - **New Upload**: Drag & drop or select an audio file, choose splitter/model, then click "Separate Audio"
   - **Existing Project**: Enter the path to a separated folder and click "Load"

## Project Structure

```
sound2/
├── app.py                 # Flask backend with API endpoints
├── audio_editor.html      # Frontend web interface
├── separate_audio.py      # Standalone separation script
├── serve_editor.py        # Simple HTTP server (alternative)
├── run.sh                 # Run script
├── data/                  # Input audio files (not in repo)
└── separated/             # Output separated stems (not in repo)
```

## API Endpoints

- `GET /api/splitters` - Get available splitters and models
- `POST /api/upload` - Upload audio file
- `POST /api/separate/<job_id>` - Run separation with selected splitter/model
- `POST /api/load-project` - Load existing separated project
- `POST /api/add-stem/<job_id>` - Add/replace individual stem
- `POST /api/split-vocals/<job_id>` - Secondary split on vocals
- `POST /api/split-drums/<job_id>` - Secondary split on drums
- `GET /api/stems/<job_id>/<stem_path>` - Serve stem files via HTTP

## Features in Detail

### State Machine
The frontend uses a state machine (idle → uploading → separating → loading → ready) to manage UI state and provide clear feedback.

### Manifest System
Projects use a manifest structure that includes:
- Job ID and splitter/model info
- Mix track (original file)
- Parent stems (vocals, drums, bass, etc.)
- Child stems (from secondary splits, e.g., vocals/lead, vocals/backing)

### Track Tree UI
- Mix track displayed first
- Parent stems with controls
- Collapsible child tracks for secondary splits
- Visual hierarchy with indentation

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

