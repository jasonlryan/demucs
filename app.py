#!/usr/bin/env python3
"""
Flask backend for audio separation using Demucs.
Handles file uploads and audio processing.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import shutil
import librosa
import numpy as np

app = Flask(__name__, static_folder='.')
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = tempfile.mkdtemp()
SEPARATED_FOLDER = 'separated'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'aiff', 'aif', 'm4a', 'flac', 'ogg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_splitters():
    """Detect available audio separation libraries and their models"""
    splitters = {}
    
    # Check for Demucs
    demucs_path = shutil.which('demucs')
    if not demucs_path:
        home = str(Path.home())
        demucs_path = f"{home}/Library/Python/3.12/bin/demucs"
    
    if demucs_path and os.path.exists(demucs_path):
        splitters['demucs'] = {
            'name': 'Demucs',
            'description': 'Facebook Research Demucs - High quality source separation',
            'models': [
                {'id': 'htdemucs', 'name': 'Demucs 4', 'stems': ['vocals', 'drums', 'bass', 'other']},
                {'id': 'htdemucs_6s', 'name': 'Demucs 6s', 'stems': ['vocals', 'drums', 'bass', 'guitar', 'piano', 'other']},
                {'id': 'htdemucs_ft', 'name': 'Demucs High Quality', 'stems': ['vocals', 'drums', 'bass', 'other']},
            ]
        }
    
    # Check for Spleeter
    spleeter_path = shutil.which('spleeter')
    if spleeter_path:
        splitters['spleeter'] = {
            'name': 'Spleeter',
            'description': 'Deezer Spleeter - Fast 2/4/5 stem separation',
            'models': [
                {'id': '2stems', 'name': '2 Stems (Vocals/Instrumental)', 'stems': ['vocals', 'accompaniment']},
                {'id': '4stems', 'name': '4 Stems', 'stems': ['vocals', 'drums', 'bass', 'other']},
                {'id': '5stems', 'name': '5 Stems', 'stems': ['vocals', 'drums', 'bass', 'piano', 'other']},
            ]
        }
    
    # Check for MDX23 (if available)
    # Note: MDX23 typically requires Python import, not CLI
    try:
        import mdx23
        splitters['mdx23'] = {
            'name': 'MDX23',
            'description': 'MDX23 - High quality separation models',
            'models': [
                {'id': 'mdx23', 'name': 'MDX23 Standard', 'stems': ['vocals', 'drums', 'bass', 'other']},
            ]
        }
    except ImportError:
        pass
    
    return splitters

@app.route('/')
def index():
    # Serve React app if built, otherwise serve old HTML editor
    build_path = os.path.join(os.path.dirname(__file__), 'build', 'index.html')
    if os.path.exists(build_path):
        return send_from_directory('build', 'index.html')
    return send_from_directory('.', 'audio_editor.html')

@app.route('/<path:path>')
def serve_static(path):
    # Serve React build files if they exist
    build_path = os.path.join('build', path)
    if os.path.exists(build_path):
        return send_from_directory('build', path)
    # Fallback to root directory
    return send_from_directory('.', path)

@app.route('/api/splitters', methods=['GET'])
def get_splitters():
    """Return available splitters and their models"""
    try:
        splitters = detect_splitters()
        return jsonify({
            'status': 'success',
            'splitters': splitters
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/stems/<job_id>/<path:stem_path>', methods=['GET'])
def serve_stem(job_id, stem_path):
    """Serve stem files via HTTP - supports nested paths for child splits"""
    try:
        # Handle child splits (e.g., /api/stems/job_id/vocals/lead)
        path_parts = stem_path.split('/')
        stem_name = path_parts[-1]
        parent_dir = path_parts[0] if len(path_parts) > 1 else None
        
        # Special handling for 'mix' - check uploaded files and various locations
        if stem_name == 'mix':
            # First check uploaded files
            uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
            for f in uploaded_files:
                if Path(f).stem == job_id:
                    mix_file = os.path.join(app.config['UPLOAD_FOLDER'], f)
                    if os.path.exists(mix_file):
                        return send_from_directory(app.config['UPLOAD_FOLDER'], f)
            
            # Check separated folders for mixture files
            for model_folder in ['htdemucs_6s', 'htdemucs_ft', 'htdemucs', 'spleeter']:
                mix_path = os.path.join(SEPARATED_FOLDER, model_folder, job_id, 'mixture.mp3')
                if os.path.exists(mix_path):
                    return send_from_directory(os.path.join(SEPARATED_FOLDER, model_folder, job_id), 'mixture.mp3')
                # Also check for mix.wav, mix.flac
                for ext in ['.wav', '.flac']:
                    mix_path = os.path.join(SEPARATED_FOLDER, model_folder, job_id, f'mix{ext}')
                    if os.path.exists(mix_path):
                        return send_from_directory(os.path.join(SEPARATED_FOLDER, model_folder, job_id), f'mix{ext}')
        
        # Handle child splits (e.g., vocals/lead, drums/kick)
        if parent_dir:
            # Search generically for child splits in any song folder structure
            # Look for {any_folder}/{job_id}/{parent_dir}/{stem_name}
            for root, dirs, files in os.walk(SEPARATED_FOLDER):
                # Check if this path contains job_id and parent_dir
                if job_id in root and parent_dir in dirs:
                    child_dir = os.path.join(root, parent_dir)
                    if os.path.exists(child_dir):
                        extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
                        for ext in extensions:
                            stem_file = os.path.join(child_dir, f'{stem_name}{ext}')
                            if os.path.exists(stem_file):
                                return send_from_directory(child_dir, f'{stem_name}{ext}')
            
            # Legacy support: Check old vocal_splits directory
            if parent_dir == 'vocals':
                vocal_split_dir = os.path.join(SEPARATED_FOLDER, 'vocal_splits', job_id)
                if os.path.exists(vocal_split_dir):
                    extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
                    for ext in extensions:
                        stem_file = os.path.join(vocal_split_dir, f'{stem_name}{ext}')
                        if os.path.exists(stem_file):
                            return send_from_directory(vocal_split_dir, f'{stem_name}{ext}')
            
            # Legacy support: Check old drum_splits directory
            if parent_dir == 'drums':
                drum_split_dir = os.path.join(SEPARATED_FOLDER, 'drum_splits', job_id)
                if os.path.exists(drum_split_dir):
                    extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
                    for ext in extensions:
                        stem_file = os.path.join(drum_split_dir, f'{stem_name}{ext}')
                        if os.path.exists(stem_file):
                            return send_from_directory(drum_split_dir, f'{stem_name}{ext}')
        
        # Try to find the stem generically - search for job_id folder containing the stem
        extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
        
        # First try common locations
        possible_base_dirs = [
            os.path.join(SEPARATED_FOLDER, 'htdemucs_6s', job_id),
            os.path.join(SEPARATED_FOLDER, 'htdemucs_ft', job_id),
            os.path.join(SEPARATED_FOLDER, 'htdemucs', job_id),
            os.path.join(SEPARATED_FOLDER, 'spleeter', job_id),
        ]
        
        for base_dir in possible_base_dirs:
            if os.path.exists(base_dir):
                for ext in extensions:
                    stem_file = os.path.join(base_dir, f'{stem_name}{ext}')
                    if os.path.exists(stem_file):
                        return send_from_directory(base_dir, f'{stem_name}{ext}')
        
        # If not found, search generically in separated folder
        for root, dirs, files in os.walk(SEPARATED_FOLDER):
            if job_id in root:
                for ext in extensions:
                    stem_file = os.path.join(root, f'{stem_name}{ext}')
                    if os.path.exists(stem_file):
                        return send_from_directory(root, f'{stem_name}{ext}')
        
        return jsonify({'error': f'Stem {stem_path} not found for job {job_id}'}), 404
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initiate separation"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Create a unique output directory for this file
        base_name = Path(filename).stem
        output_dir = os.path.join(SEPARATED_FOLDER, 'htdemucs', base_name)

        # Return job info
        return jsonify({
            'job_id': base_name,
            'filename': filename,
            'file_path': file_path,
            'message': 'File uploaded successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/separate/<job_id>', methods=['POST'])
def separate_audio(job_id):
    """Run separation on uploaded file with selected splitter and model"""
    try:
        # Get the uploaded file path
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        matching_file = None

        for f in files:
            if Path(f).stem == job_id:
                matching_file = f
                break

        if not matching_file:
            return jsonify({'error': 'Job not found'}), 404

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], matching_file)

        # Get splitter and model from request
        data = request.get_json() if request.is_json else {}
        splitter = data.get('splitter', 'demucs')
        model = data.get('model', 'htdemucs_6s')

        # Detect available splitters
        available_splitters = detect_splitters()
        if splitter not in available_splitters:
            return jsonify({'error': f'Splitter {splitter} not available'}), 400

        # Run separation based on splitter
        if splitter == 'demucs':
            result = run_demucs_separation(file_path, job_id, model)
        elif splitter == 'spleeter':
            result = run_spleeter_separation(file_path, job_id, model)
        elif splitter == 'mdx23':
            result = run_mdx23_separation(file_path, job_id, model)
        else:
            return jsonify({'error': f'Unsupported splitter: {splitter}'}), 400

        # Build manifest with HTTP paths
        manifest = {
            'status': 'success',
            'job_id': job_id,
            'splitter': splitter,
            'model': model,
            'output_dir': result['output_dir'],
            'stems': [],
            'mix': None,
            'child_splits': result.get('child_splits', {})
        }

        # Add stems with HTTP URLs
        for stem_name in result['stems']:
            stem_info = {
                'name': stem_name,
                'url': f'/api/stems/{job_id}/{stem_name}',
                'path': result.get('stem_paths', {}).get(stem_name, '')
            }
            manifest['stems'].append(stem_info)

        # Add mix (original uploaded file)
        mix_path = result.get('mix_path')
        if not mix_path:
            # Use the original uploaded file as mix
            matching_file = None
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                if Path(f).stem == job_id:
                    mix_path = os.path.join(app.config['UPLOAD_FOLDER'], f)
                    break
        
        if mix_path and os.path.exists(mix_path):
            manifest['mix'] = {
                'url': f'/api/stems/{job_id}/mix',
                'path': mix_path
            }

        return jsonify(manifest)

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

def run_demucs_separation(file_path, job_id, model):
    """Run Demucs separation"""
    # Find demucs executable
    demucs_path = shutil.which('demucs')
    if not demucs_path:
        home = str(Path.home())
        demucs_path = f"{home}/Library/Python/3.12/bin/demucs"
        if not os.path.exists(demucs_path):
            raise Exception('Demucs not found. Please install it first.')

    # Run Demucs separation
    cmd = [
        demucs_path,
        file_path,
        '-n', model,
        '-o', SEPARATED_FOLDER,
        '--mp3',
        '--mp3-bitrate', '320'
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    output_lines = []
    for line in process.stdout:
        output_lines.append(line.strip())
        print(line.strip())

    return_code = process.wait()

    if return_code != 0:
        stderr = process.stderr.read()
        raise Exception(f'Separation failed: {stderr}')

    # Determine output directory
    if model == 'htdemucs_6s':
        model_folder = 'htdemucs_6s'
        expected_stems = ['vocals', 'drums', 'bass', 'guitar', 'piano', 'other']
    elif model == 'htdemucs_ft':
        model_folder = 'htdemucs_ft'
        expected_stems = ['vocals', 'drums', 'bass', 'other']
    else:
        model_folder = 'htdemucs'
        expected_stems = ['vocals', 'drums', 'bass', 'other']

    output_dir = os.path.join(SEPARATED_FOLDER, model_folder, job_id)

    if not os.path.exists(output_dir):
        raise Exception('Output directory not found')

    # Find available stems
    available_stems = []
    stem_paths = {}
    for stem in expected_stems:
        stem_path = os.path.join(output_dir, f'{stem}.mp3')
        if os.path.exists(stem_path):
            available_stems.append(stem)
            stem_paths[stem] = stem_path

    return {
        'output_dir': output_dir,
        'stems': available_stems,
        'stem_paths': stem_paths,
        'mix_path': file_path  # Original file as mix
    }

def run_spleeter_separation(file_path, job_id, model):
    """Run Spleeter separation"""
    spleeter_path = shutil.which('spleeter')
    if not spleeter_path:
        raise Exception('Spleeter not found. Please install it first.')

    output_dir = os.path.join(SEPARATED_FOLDER, 'spleeter', job_id)
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        spleeter_path,
        'separate',
        '-p', f'spleeter:{model}',
        '-o', SEPARATED_FOLDER,
        file_path
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    output_lines = []
    for line in process.stdout:
        output_lines.append(line.strip())
        print(line.strip())

    return_code = process.wait()

    if return_code != 0:
        stderr = process.stderr.read()
        raise Exception(f'Spleeter separation failed: {stderr}')

    # Spleeter outputs to separated/audio_filename/stem_name.wav
    input_filename = Path(file_path).stem
    spleeter_output = os.path.join(SEPARATED_FOLDER, input_filename)

    # Map stems based on model
    if model == '2stems':
        expected_stems = ['vocals', 'accompaniment']
    elif model == '4stems':
        expected_stems = ['vocals', 'drums', 'bass', 'other']
    else:  # 5stems
        expected_stems = ['vocals', 'drums', 'bass', 'piano', 'other']

    available_stems = []
    stem_paths = {}
    for stem in expected_stems:
        stem_path = os.path.join(spleeter_output, f'{stem}.wav')
        if os.path.exists(stem_path):
            available_stems.append(stem)
            stem_paths[stem] = stem_path

    return {
        'output_dir': spleeter_output,
        'stems': available_stems,
        'stem_paths': stem_paths,
        'mix_path': file_path  # Original file as mix
    }

def run_mdx23_separation(file_path, job_id, model):
    """Run MDX23 separation"""
    # MDX23 typically requires Python API, not CLI
    # This is a placeholder - implement based on MDX23 API
    raise Exception('MDX23 separation not yet implemented')

def analyze_stem_content(audio_path):
    """Analyze audio stem and suggest a better label"""
    try:
        # Load audio
        y, sr = librosa.load(audio_path, duration=30, sr=22050)  # First 30 seconds

        # Calculate features
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        rms = np.mean(librosa.feature.rms(y=y))

        # Rough heuristics for classification
        # High spectral centroid = bright sounds (cymbals, hi-hats, vocals)
        # Low spectral centroid = bass, kick drum
        # High ZCR = percussion, drums

        suggestions = []

        if spectral_centroid > 3000:
            if zero_crossing_rate > 0.1:
                suggestions.append("Vocals")
            else:
                suggestions.append("Synth/Keys")
        elif spectral_centroid > 1500:
            if zero_crossing_rate > 0.15:
                suggestions.append("Guitar")
            else:
                suggestions.append("Piano")
        else:
            if zero_crossing_rate > 0.1:
                suggestions.append("Bass")
            else:
                suggestions.append("Kick/Low End")

        return suggestions[0] if suggestions else "Unknown"

    except Exception as e:
        print(f"Analysis error: {e}")
        return None

@app.route('/api/analyze/<job_id>', methods=['POST'])
def analyze_stems(job_id):
    """Analyze stems and suggest better labels"""
    try:
        # Try all model directories
        output_dir_6s = os.path.join(SEPARATED_FOLDER, 'htdemucs_6s', job_id)
        output_dir_ft = os.path.join(SEPARATED_FOLDER, 'htdemucs_ft', job_id)
        output_dir_4s = os.path.join(SEPARATED_FOLDER, 'htdemucs', job_id)

        if os.path.exists(output_dir_6s):
            output_dir = output_dir_6s
            stems = ['vocals', 'drums', 'bass', 'guitar', 'piano', 'other']
        elif os.path.exists(output_dir_ft):
            output_dir = output_dir_ft
            stems = ['vocals', 'drums', 'bass', 'other']
        elif os.path.exists(output_dir_4s):
            output_dir = output_dir_4s
            stems = ['vocals', 'drums', 'bass', 'other']
        else:
            return jsonify({'error': 'Stems not found'}), 404

        labels = {}

        for stem in stems:
            stem_path = os.path.join(output_dir, f'{stem}.mp3')
            if os.path.exists(stem_path):
                suggested_label = analyze_stem_content(stem_path)
                if suggested_label:
                    labels[stem] = suggested_label
                else:
                    labels[stem] = stem.capitalize()

        return jsonify({
            'status': 'success',
            'labels': labels
        })

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/split-vocals/<job_id>', methods=['POST'])
def split_vocals(job_id):
    """Run vocal separation to split vocals into lead and backing vocals using spectral analysis"""
    try:
        # Find the vocals stem file - search generically in any folder structure
        vocal_stem_path = None
        song_folder = None
        
        # First, try to find vocals.mp3 in common locations
        for model_folder in ['htdemucs_6s', 'htdemucs_ft', 'htdemucs', 'spleeter']:
            test_path = os.path.join(SEPARATED_FOLDER, model_folder, job_id, 'vocals.mp3')
            if os.path.exists(test_path):
                vocal_stem_path = test_path
                song_folder = os.path.join(SEPARATED_FOLDER, model_folder, job_id)
                break
        
        # If not found, search more generically in separated folder
        if not vocal_stem_path:
            for root, dirs, files in os.walk(SEPARATED_FOLDER):
                # Look for job_id folder containing vocals.mp3
                if job_id in root and 'vocals.mp3' in files:
                    vocal_stem_path = os.path.join(root, 'vocals.mp3')
                    song_folder = root
                    break
        
        if not vocal_stem_path or not song_folder:
            return jsonify({'error': 'Vocals stem not found'}), 404

        # Create output directory for vocal splits as subfolder within song folder
        vocal_split_dir = os.path.join(song_folder, 'vocals')
        os.makedirs(vocal_split_dir, exist_ok=True)

        # Use librosa for vocal separation
        # Method: Separate lead vocals (mono, centered) from backing vocals/harmonies (stereo, panned)
        try:
            import librosa
            import soundfile as sf
            from scipy import signal
            
            print(f"Loading vocals: {vocal_stem_path}")
            y, sr = librosa.load(vocal_stem_path, sr=44100, mono=False)
            
            # If mono, duplicate to stereo for processing
            if len(y.shape) == 1:
                y = np.array([y, y])
            
            # Convert to stereo if needed
            if y.shape[0] == 1:
                y = np.vstack([y, y])
            
            # Method 1: Center channel extraction for lead vocals
            # Lead vocals are typically centered (L+R), backing vocals are panned (L-R)
            center = (y[0] + y[1]) / 2  # Center channel (lead vocals)
            sides = (y[0] - y[1]) / 2    # Side channel (backing/harmonies)
            
            # Method 2: Spectral separation based on frequency content
            # Lead vocals: typically 80-1000 Hz fundamental, clearer harmonics
            # Backing vocals: often higher frequencies, more diffuse
            
            # Apply spectral gating to separate
            # Lead vocals: stronger fundamental frequencies
            # Backing: more harmonic content, reverb
            
            # Use harmonic-percussive separation as a proxy
            # Lead vocals tend to be more harmonic, backing more diffuse
            y_mono = librosa.to_mono(y)
            
            # Harmonic-percussive separation
            y_harmonic, y_percussive = librosa.effects.hpss(y_mono)
            
            # Further separate using spectral characteristics
            # Lead vocals: stronger fundamental, clearer formants
            # Backing: more reverb, less clear formants
            
            # Use spectral centroid to identify lead vs backing
            # Lead vocals typically have more consistent spectral centroid
            stft = librosa.stft(y_mono)
            magnitude = np.abs(stft)
            spectral_centroid = librosa.feature.spectral_centroid(S=magnitude, sr=sr)[0]
            
            # Create masks based on spectral characteristics
            # Lead vocals: more consistent, lower variance in spectral centroid
            centroid_mean = np.mean(spectral_centroid)
            centroid_std = np.std(spectral_centroid)
            
            # Lead vocals mask: frequencies closer to mean centroid
            lead_mask = np.abs(spectral_centroid - centroid_mean) < centroid_std * 0.7
            backing_mask = ~lead_mask
            
            # Apply masks to frequency domain
            lead_stft = stft.copy()
            backing_stft = stft.copy()
            
            for i in range(len(lead_mask)):
                if not lead_mask[i]:
                    lead_stft[:, i] = 0
                if not backing_mask[i]:
                    backing_stft[:, i] = 0
            
            # Convert back to time domain
            lead_audio = librosa.istft(lead_stft)
            backing_audio = librosa.istft(backing_stft)
            
            # Also use center channel extraction as primary method
            # Combine both methods
            center_mono = librosa.to_mono(np.array([center, center]))
            
            # Blend methods: 70% center channel, 30% spectral separation
            lead_final = 0.7 * center_mono + 0.3 * lead_audio
            backing_final = 0.7 * sides + 0.3 * backing_audio
            
            # Normalize to prevent clipping
            lead_final = librosa.util.normalize(lead_final)
            backing_final = librosa.util.normalize(backing_final)
            
            # Save separated vocals
            lead_path = os.path.join(vocal_split_dir, 'lead.wav')
            backing_path = os.path.join(vocal_split_dir, 'backing.wav')
            
            sf.write(lead_path, lead_final, sr)
            sf.write(backing_path, backing_final, sr)
            
            print(f"Vocal separation complete: lead and backing vocals saved")
            
            child_stems = [
                {
                    'name': 'lead',
                    'url': f'/api/stems/{job_id}/vocals/lead',
                    'path': lead_path,
                    'parent': 'vocals'
                },
                {
                    'name': 'backing',
                    'url': f'/api/stems/{job_id}/vocals/backing',
                    'path': backing_path,
                    'parent': 'vocals'
                }
            ]
            
        except ImportError as e:
            return jsonify({
                'error': f'Vocal separation requires additional libraries: {str(e)}',
                'note': 'Please install: pip install librosa soundfile scipy'
            }), 400
        except Exception as e:
            import traceback
            return jsonify({
                'error': f'Vocal separation failed: {str(e)}',
                'traceback': traceback.format_exc()
            }), 500

        # Build updated manifest
        manifest = {
            'status': 'success',
            'job_id': job_id,
            'splitter': 'vocal_separation',
            'model': 'spectral_analysis',
            'child_splits': {
                'vocals': child_stems
            }
        }

        return jsonify(manifest)

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/split-drums/<job_id>', methods=['POST'])
def split_drums(job_id):
    """Run second-pass separation on drums stem to split into kick/snare/cymbals/etc using drum-specific model"""
    try:
        # Find the drums stem file - search generically in any folder structure
        drums_stem_path = None
        song_folder = None
        
        # First, try to find drums.mp3 in common locations
        for model_folder in ['htdemucs_6s', 'htdemucs_ft', 'htdemucs', 'spleeter']:
            test_path = os.path.join(SEPARATED_FOLDER, model_folder, job_id, 'drums.mp3')
            if os.path.exists(test_path):
                drums_stem_path = test_path
                song_folder = os.path.join(SEPARATED_FOLDER, model_folder, job_id)
                break
        
        # If not found, search more generically in separated folder
        if not drums_stem_path:
            for root, dirs, files in os.walk(SEPARATED_FOLDER):
                # Look for job_id folder containing drums.mp3
                if job_id in root and 'drums.mp3' in files:
                    drums_stem_path = os.path.join(root, 'drums.mp3')
                    song_folder = root
                    break
        
        if not drums_stem_path or not song_folder:
            return jsonify({'error': 'Drums stem not found'}), 404

        # Create output directory for drum splits as subfolder within song folder
        drum_split_dir = os.path.join(song_folder, 'drums')
        os.makedirs(drum_split_dir, exist_ok=True)

        # Use frequency-based separation (Demucs doesn't do drum part separation)
        print("Using frequency-based drum separation...")
        child_stems = []
        try:
            import librosa
            import numpy as np
            import soundfile as sf
            
            print(f"Loading drums: {drums_stem_path}")
            y, sr = librosa.load(drums_stem_path, sr=44100)
            
            # Use STFT for better frequency separation
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            freqs = librosa.fft_frequencies(sr=sr)
            
            # Define frequency ranges for different drum parts
            kick_freq_range = (20, 200)    # Kick drum: very low frequencies
            snare_freq_range = (200, 2000)  # Snare: mid frequencies
            hihat_freq_range = (2000, 8000) # Hihat: high frequencies
            cymbal_freq_range = (4000, 20000) # Cymbals: very high frequencies
            
            # Create frequency masks
            kick_mask = (freqs >= kick_freq_range[0]) & (freqs <= kick_freq_range[1])
            snare_mask = (freqs >= snare_freq_range[0]) & (freqs <= snare_freq_range[1])
            hihat_mask = (freqs >= hihat_freq_range[0]) & (freqs <= hihat_freq_range[1])
            cymbal_mask = (freqs >= cymbal_freq_range[0]) & (freqs <= cymbal_freq_range[1])
            
            # Expand masks to match STFT shape
            kick_mask_2d = np.tile(kick_mask[:, np.newaxis], (1, stft.shape[1]))
            snare_mask_2d = np.tile(snare_mask[:, np.newaxis], (1, stft.shape[1]))
            hihat_mask_2d = np.tile(hihat_mask[:, np.newaxis], (1, stft.shape[1]))
            cymbal_mask_2d = np.tile(cymbal_mask[:, np.newaxis], (1, stft.shape[1]))
            
            # Apply masks (preserve phase from original)
            kick_stft = stft * kick_mask_2d
            snare_stft = stft * snare_mask_2d
            hihat_stft = stft * hihat_mask_2d
            cymbal_stft = stft * cymbal_mask_2d
            
            # Convert back to time domain
            kick_audio = librosa.istft(kick_stft)
            snare_audio = librosa.istft(snare_stft)
            hihat_audio = librosa.istft(hihat_stft)
            cymbal_audio = librosa.istft(cymbal_stft)
            
            # Normalize to prevent clipping
            kick_audio = librosa.util.normalize(kick_audio)
            snare_audio = librosa.util.normalize(snare_audio)
            hihat_audio = librosa.util.normalize(hihat_audio)
            cymbal_audio = librosa.util.normalize(cymbal_audio)
            
            # Save separated parts
            drum_parts = [
                ('kick', kick_audio),
                ('snare', snare_audio),
                ('hihat', hihat_audio),
                ('cymbals', cymbal_audio)
            ]
            
            for name, audio in drum_parts:
                output_path = os.path.join(drum_split_dir, f'{name}.wav')
                sf.write(output_path, audio, sr)
                child_stems.append({
                    'name': name,
                    'url': f'/api/stems/{job_id}/drums/{name}',
                    'path': output_path,
                    'parent': 'drums'
                })
            
            print(f"Drum separation complete: {len(child_stems)} parts created")
                
        except ImportError as e:
            return jsonify({
                'error': f'Drum separation requires additional libraries: {str(e)}',
                'note': 'Please install: pip install librosa soundfile scipy numpy'
            }), 400
        except Exception as e:
            import traceback
            return jsonify({
                'error': f'Drum separation failed: {str(e)}',
                'traceback': traceback.format_exc()
            }), 500
        
        if not child_stems:
            return jsonify({
                'error': 'No drum parts were created',
                'note': 'Drum separation completed but no valid parts were found.'
            }), 400

        # Build updated manifest
        manifest = {
            'status': 'success',
            'job_id': job_id,
            'splitter': 'drum_separation',
            'model': 'htdemucs_6s',
            'child_splits': {
                'drums': child_stems
            }
        }

        return jsonify(manifest)

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/add-stem/<job_id>', methods=['POST'])
def add_stem(job_id):
    """Add or replace an individual stem file to an existing project"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        stem_name = request.form.get('stem_name', '').strip()

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not stem_name:
            # Try to infer from filename
            stem_name = Path(file.filename).stem.lower()
            # Remove common prefixes/suffixes
            for prefix in ['stem_', 'track_', 'audio_']:
                if stem_name.startswith(prefix):
                    stem_name = stem_name[len(prefix):]
            for suffix in ['_stem', '_track', '_audio']:
                if stem_name.endswith(suffix):
                    stem_name = stem_name[:-len(suffix)]

        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Find the project folder
        project_path = None
        for model_folder in ['htdemucs_6s', 'htdemucs_ft', 'htdemucs', 'spleeter']:
            test_path = os.path.join(SEPARATED_FOLDER, model_folder, job_id)
            if os.path.exists(test_path):
                project_path = test_path
                break

        if not project_path:
            # Create default project folder
            project_path = os.path.join(SEPARATED_FOLDER, 'htdemucs', job_id)
            os.makedirs(project_path, exist_ok=True)

        # Save the stem file
        ext = os.path.splitext(file.filename)[1].lower()
        stem_filename = f'{stem_name}{ext}'
        stem_path = os.path.join(project_path, stem_filename)
        file.save(stem_path)

        # Return updated manifest
        return jsonify({
            'status': 'success',
            'stem_name': stem_name,
            'url': f'/api/stems/{job_id}/{stem_name}',
            'path': stem_path,
            'message': f'Stem {stem_name} added successfully'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/cleanup/<job_id>', methods=['DELETE'])
def cleanup_job(job_id):
    """Clean up temporary files for a job"""
    try:
        # Remove uploaded file
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        for f in files:
            if Path(f).stem == job_id:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f)
                if os.path.exists(file_path):
                    os.remove(file_path)

        return jsonify({'status': 'success', 'message': 'Cleanup completed'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-project', methods=['POST'])
def load_project():
    """Load an existing separated project from a folder path"""
    try:
        data = request.get_json() if request.is_json else {}
        folder_path = data.get('path', '').strip()

        if not folder_path:
            return jsonify({'error': 'No folder path provided'}), 400

        # Validate path exists
        if not os.path.exists(folder_path):
            return jsonify({'error': f'Path does not exist: {folder_path}'}), 404

        if not os.path.isdir(folder_path):
            return jsonify({'error': f'Path is not a directory: {folder_path}'}), 400

        # Extract job_id from folder path (last directory name)
        job_id = os.path.basename(os.path.normpath(folder_path))
        
        # Determine splitter/model from parent directory structure
        # Check if path is within separated/ folder
        separated_base = os.path.abspath(SEPARATED_FOLDER)
        folder_abs = os.path.abspath(folder_path)
        
        splitter = 'demucs'
        model = 'htdemucs'
        
        if folder_abs.startswith(separated_base):
            rel_path = os.path.relpath(folder_abs, separated_base)
            parts = rel_path.split(os.sep)
            if len(parts) > 0:
                model_folder = parts[0]
                if model_folder.startswith('htdemucs'):
                    splitter = 'demucs'
                    model = model_folder
                elif model_folder == 'spleeter':
                    splitter = 'spleeter'
                    model = '4stems'  # Default, will detect from stems
        
        # Scan for stems
        stem_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
        found_stems = []
        stem_paths = {}
        mix_path = None
        
        # Standard stem names to look for
        standard_stems = ['vocals', 'drums', 'bass', 'guitar', 'piano', 'other', 'accompaniment']
        
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                name_lower = item.lower()
                # Check for mix/original
                if 'mix' in name_lower or 'original' in name_lower or 'mixture' in name_lower:
                    mix_path = item_path
                else:
                    # Check for stem files
                    for stem in standard_stems:
                        if name_lower.startswith(stem.lower()):
                            ext = os.path.splitext(item)[1].lower()
                            if ext in stem_extensions:
                                if stem not in found_stems:
                                    found_stems.append(stem)
                                stem_paths[stem] = item_path
                            break
        
        # Also check for child splits (subdirectories within the folder)
        child_splits = {}
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                # Check if this is a child split directory (e.g., vocals/, drums/)
                if item.lower() in ['vocals', 'drums']:
                    child_stems = []
                    for child_item in os.listdir(item_path):
                        child_item_path = os.path.join(item_path, child_item)
                        if os.path.isfile(child_item_path):
                            name_lower = child_item.lower()
                            ext = os.path.splitext(child_item)[1].lower()
                            if ext in stem_extensions:
                                stem_name = os.path.splitext(child_item)[0]
                                child_stems.append({
                                    'name': stem_name,
                                    'url': f'/api/stems/{job_id}/{item}/{stem_name}',
                                    'path': child_item_path,
                                    'parent': item
                                })
                    if child_stems:
                        child_splits[item] = child_stems
        
        # Check for drum splits in subfolder: {folder_path}/drums/
        drum_split_dir = os.path.join(folder_path, 'drums')
        if os.path.exists(drum_split_dir) and os.path.isdir(drum_split_dir):
            drum_child_stems = []
            for item in os.listdir(drum_split_dir):
                item_path = os.path.join(drum_split_dir, item)
                if os.path.isfile(item_path):
                    name_lower = item.lower()
                    ext = os.path.splitext(item)[1].lower()
                    if ext in stem_extensions:
                        stem_name = os.path.splitext(item)[0]
                        # Only include valid drum part names
                        valid_drum_parts = ['kick', 'snare', 'hihat', 'hi-hat', 'hi_hat', 'cymbal', 'cymbals', 
                                           'tom', 'toms', 'overhead', 'overheads', 'room', 'crash', 'ride']
                        if any(part in stem_name.lower() for part in valid_drum_parts) or stem_name.lower() in valid_drum_parts:
                            drum_child_stems.append({
                                'name': stem_name,
                                'url': f'/api/stems/{job_id}/drums/{stem_name}',
                                'path': item_path,
                                'parent': 'drums'
                            })
            if drum_child_stems:
                child_splits['drums'] = drum_child_stems
        
        # Check for vocal splits in subfolder: {folder_path}/vocals/
        vocal_split_dir = os.path.join(folder_path, 'vocals')
        if os.path.exists(vocal_split_dir) and os.path.isdir(vocal_split_dir):
            vocal_child_stems = []
            for item in os.listdir(vocal_split_dir):
                item_path = os.path.join(vocal_split_dir, item)
                if os.path.isfile(item_path):
                    name_lower = item.lower()
                    ext = os.path.splitext(item)[1].lower()
                    if ext in stem_extensions:
                        stem_name = os.path.splitext(item)[0]
                        # Only include valid vocal part names
                        valid_vocal_parts = ['lead', 'backing', 'backing_vocals', 'lead_vocals']
                        if any(part in stem_name.lower() for part in valid_vocal_parts) or stem_name.lower() in valid_vocal_parts:
                            vocal_child_stems.append({
                                'name': stem_name,
                                'url': f'/api/stems/{job_id}/vocals/{stem_name}',
                                'path': item_path,
                                'parent': 'vocals'
                            })
            if vocal_child_stems:
                # Merge with existing vocal splits if any
                if 'vocals' in child_splits:
                    child_splits['vocals'].extend(vocal_child_stems)
                else:
                    child_splits['vocals'] = vocal_child_stems
        
        # Legacy support: Check old drum_splits directory
        legacy_drum_split_dir = os.path.join(SEPARATED_FOLDER, 'drum_splits', job_id)
        if os.path.exists(legacy_drum_split_dir) and 'drums' not in child_splits:
            drum_child_stems = []
            for item in os.listdir(legacy_drum_split_dir):
                item_path = os.path.join(legacy_drum_split_dir, item)
                if os.path.isfile(item_path):
                    name_lower = item.lower()
                    ext = os.path.splitext(item)[1].lower()
                    if ext in stem_extensions:
                        stem_name = os.path.splitext(item)[0]
                        valid_drum_parts = ['kick', 'snare', 'hihat', 'hi-hat', 'hi_hat', 'cymbal', 'cymbals', 
                                           'tom', 'toms', 'overhead', 'overheads', 'room', 'crash', 'ride']
                        if any(part in stem_name.lower() for part in valid_drum_parts) or stem_name.lower() in valid_drum_parts:
                            drum_child_stems.append({
                                'name': stem_name,
                                'url': f'/api/stems/{job_id}/drums/{stem_name}',
                                'path': item_path,
                                'parent': 'drums'
                            })
            if drum_child_stems:
                child_splits['drums'] = drum_child_stems
        
        # Legacy support: Check old vocal_splits directory
        legacy_vocal_split_dir = os.path.join(SEPARATED_FOLDER, 'vocal_splits', job_id)
        if os.path.exists(legacy_vocal_split_dir) and 'vocals' not in child_splits:
            vocal_child_stems = []
            for item in os.listdir(legacy_vocal_split_dir):
                item_path = os.path.join(legacy_vocal_split_dir, item)
                if os.path.isfile(item_path):
                    name_lower = item.lower()
                    ext = os.path.splitext(item)[1].lower()
                    if ext in stem_extensions:
                        stem_name = os.path.splitext(item)[0]
                        valid_vocal_parts = ['lead', 'backing', 'backing_vocals', 'lead_vocals']
                        if any(part in stem_name.lower() for part in valid_vocal_parts) or stem_name.lower() in valid_vocal_parts:
                            vocal_child_stems.append({
                                'name': stem_name,
                                'url': f'/api/stems/{job_id}/vocals/{stem_name}',
                                'path': item_path,
                                'parent': 'vocals'
                            })
            if vocal_child_stems:
                child_splits['vocals'] = vocal_child_stems
        
        # Build manifest
        manifest = {
            'status': 'success',
            'job_id': job_id,
            'splitter': splitter,
            'model': model,
            'output_dir': folder_path,
            'stems': [],
            'mix': None,
            'child_splits': child_splits
        }
        
        # Add stems with HTTP URLs
        for stem_name in found_stems:
            stem_info = {
                'name': stem_name,
                'url': f'/api/stems/{job_id}/{stem_name}',
                'path': stem_paths[stem_name]
            }
            manifest['stems'].append(stem_info)
        
        # Add mix if found
        if mix_path:
            manifest['mix'] = {
                'url': f'/api/stems/{job_id}/mix',
                'path': mix_path
            }
        else:
            # Try to find original uploaded file
            uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
            for f in uploaded_files:
                if Path(f).stem == job_id:
                    mix_path = os.path.join(app.config['UPLOAD_FOLDER'], f)
                    manifest['mix'] = {
                        'url': f'/api/stems/{job_id}/mix',
                        'path': mix_path
                    }
                    break
        
        return jsonify(manifest)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/browse-folders', methods=['POST'])
def browse_folders():
    """List subdirectories in a given path"""
    try:
        data = request.json
        base_path = data.get('path', '')

        if not os.path.exists(base_path):
            return jsonify({'error': 'Path does not exist'}), 404

        # Get all subdirectories
        folders = []
        for item in os.listdir(base_path):
            full_path = os.path.join(base_path, item)
            if os.path.isdir(full_path):
                folders.append({
                    'name': item,
                    'path': full_path
                })

        # Sort folders by modification time (newest first)
        folders.sort(key=lambda x: os.path.getmtime(x['path']), reverse=True)

        return jsonify({'folders': folders})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure separated folder exists
    os.makedirs(SEPARATED_FOLDER, exist_ok=True)

    print("🎵 Demucs Audio Separator Server")
    print("=" * 50)
    print("Server running at http://localhost:5001/")
    print("Upload audio files to separate them into stems")
    print("=" * 50)
    print()

    app.run(debug=True, host='0.0.0.0', port=5001)
