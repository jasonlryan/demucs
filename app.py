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
                {'id': 'htdemucs_6s', 'name': '6 Stems (Standard)', 'stems': ['vocals', 'drums', 'bass', 'guitar', 'piano', 'other']},
                {'id': 'htdemucs_ft', 'name': '4 Stems (Fine-Tuned)', 'stems': ['vocals', 'drums', 'bass', 'other']},
                {'id': 'htdemucs', 'name': '4 Stems (Standard)', 'stems': ['vocals', 'drums', 'bass', 'other']},
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
    return send_from_directory('.', 'audio_editor.html')

@app.route('/<path:path>')
def serve_static(path):
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
            for model_folder in ['htdemucs_6s', 'htdemucs_ft', 'htdemucs']:
                child_dir = os.path.join(SEPARATED_FOLDER, model_folder, parent_dir)
                if os.path.exists(child_dir):
                    extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
                    for ext in extensions:
                        stem_file = os.path.join(child_dir, f'{stem_name}{ext}')
                        if os.path.exists(stem_file):
                            return send_from_directory(child_dir, f'{stem_name}{ext}')
        
        # Try to find the stem in various model folders
        possible_base_dirs = [
            os.path.join(SEPARATED_FOLDER, 'htdemucs_6s', job_id),
            os.path.join(SEPARATED_FOLDER, 'htdemucs_ft', job_id),
            os.path.join(SEPARATED_FOLDER, 'htdemucs', job_id),
            os.path.join(SEPARATED_FOLDER, 'spleeter', job_id),
        ]
        
        # Try different extensions
        extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
        
        for base_dir in possible_base_dirs:
            if not os.path.exists(base_dir):
                continue
            for ext in extensions:
                stem_file = os.path.join(base_dir, f'{stem_name}{ext}')
                if os.path.exists(stem_file):
                    return send_from_directory(base_dir, f'{stem_name}{ext}')
        
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
    """Run second-pass separation on vocals stem to automatically split lead/backing"""
    try:
        # Find the vocals.mp3 file from first separation
        vocal_stem_path = None

        for model_folder in ['htdemucs_6s', 'htdemucs_ft', 'htdemucs']:
            test_path = os.path.join(SEPARATED_FOLDER, model_folder, job_id, 'vocals.mp3')
            if os.path.exists(test_path):
                vocal_stem_path = test_path
                break

        if not vocal_stem_path:
            return jsonify({'error': 'Vocals stem not found'}), 404

        # Find demucs
        demucs_path = shutil.which('demucs')
        if not demucs_path:
            home = str(Path.home())
            demucs_path = f"{home}/Library/Python/3.12/bin/demucs"

        # Run Demucs two-stem on vocals.mp3 (no upload needed!)
        cmd = [
            demucs_path,
            vocal_stem_path,
            '-n', 'htdemucs',
            '--two-stems', 'vocals',
            '-o', SEPARATED_FOLDER,
            '--mp3',
            '--mp3-bitrate', '320'
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in process.stdout:
            print(line.strip())

        return_code = process.wait()

        if return_code != 0:
            stderr = process.stderr.read()
            return jsonify({'error': f'Vocal split failed: {stderr}'}), 500

        # Results are in separated/htdemucs/vocals/
        split_dir = os.path.join(SEPARATED_FOLDER, 'htdemucs', 'vocals')

        # Check for output stems
        child_stems = []
        stem_extensions = ['.mp3', '.wav', '.flac']
        for item in os.listdir(split_dir):
            item_path = os.path.join(split_dir, item)
            if os.path.isfile(item_path):
                name_lower = item.lower()
                ext = os.path.splitext(item)[1].lower()
                if ext in stem_extensions:
                    stem_name = os.path.splitext(item)[0]
                    child_stems.append({
                        'name': stem_name,
                        'url': f'/api/stems/{job_id}/vocals/{stem_name}',
                        'path': item_path,
                        'parent': 'vocals'
                    })

        # Build updated manifest
        manifest = {
            'status': 'success',
            'job_id': job_id,
            'splitter': 'demucs',
            'model': 'htdemucs',
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
    """Run second-pass separation on drums stem to split into kick/snare/cymbals/etc"""
    try:
        # Find the drums.mp3 file from first separation
        drums_stem_path = None

        for model_folder in ['htdemucs_6s', 'htdemucs_ft', 'htdemucs']:
            test_path = os.path.join(SEPARATED_FOLDER, model_folder, job_id, 'drums.mp3')
            if os.path.exists(test_path):
                drums_stem_path = test_path
                break

        if not drums_stem_path:
            return jsonify({'error': 'Drums stem not found'}), 404

        # Find demucs
        demucs_path = shutil.which('demucs')
        if not demucs_path:
            home = str(Path.home())
            demucs_path = f"{home}/Library/Python/3.12/bin/demucs"

        # Run Demucs on drums.mp3 with 4-stem to get better drum separation
        cmd = [
            demucs_path,
            drums_stem_path,
            '-n', 'htdemucs',
            '-o', SEPARATED_FOLDER,
            '--mp3',
            '--mp3-bitrate', '320'
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in process.stdout:
            print(line.strip())

        return_code = process.wait()

        if return_code != 0:
            stderr = process.stderr.read()
            return jsonify({'error': f'Drum split failed: {stderr}'}), 500

        # Results are in separated/htdemucs/drums/
        split_dir = os.path.join(SEPARATED_FOLDER, 'htdemucs', 'drums')

        # Check for output stems
        child_stems = []
        stem_extensions = ['.mp3', '.wav', '.flac']
        if os.path.exists(split_dir):
            for item in os.listdir(split_dir):
                item_path = os.path.join(split_dir, item)
                if os.path.isfile(item_path):
                    name_lower = item.lower()
                    ext = os.path.splitext(item)[1].lower()
                    if ext in stem_extensions:
                        stem_name = os.path.splitext(item)[0]
                        child_stems.append({
                            'name': stem_name,
                            'url': f'/api/stems/{job_id}/drums/{stem_name}',
                            'path': item_path,
                            'parent': 'drums'
                        })

        # Build updated manifest
        manifest = {
            'status': 'success',
            'job_id': job_id,
            'splitter': 'demucs',
            'model': 'htdemucs',
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
        
        # Also check for child splits (subdirectories)
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
