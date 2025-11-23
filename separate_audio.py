#!/usr/bin/env python3
"""
Audio source separation using Demucs.
Separates an audio file into vocals, drums, bass, and other instruments.
"""

import os
import sys
from pathlib import Path

def separate_audio(input_file, output_dir="separated"):
    """
    Separate audio file into stems using Demucs.

    Args:
        input_file: Path to the input audio file
        output_dir: Directory where separated stems will be saved
    """
    # Import here to avoid slow startup
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    import torchaudio

    print(f"Loading audio file: {input_file}")

    # Load the audio file
    wav, sr = torchaudio.load(input_file)

    print(f"Audio loaded: {wav.shape[0]} channels, {wav.shape[1]} samples, {sr} Hz")
    print("Loading Demucs model (htdemucs)...")

    # Load the pretrained model
    model = get_model('htdemucs')

    print("Separating audio sources...")

    # Apply the model
    # Move to GPU if available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    model.to(device)
    wav = wav.to(device)

    # Apply the model
    sources = apply_model(model, wav[None], device=device)[0]

    # Get the source names from the model
    sources_list = ['drums', 'bass', 'other', 'vocals']

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Save each source
    print(f"\nSaving separated stems to: {output_dir}/")
    for i, source_name in enumerate(sources_list):
        output_path = os.path.join(output_dir, f"{source_name}.wav")
        torchaudio.save(output_path, sources[i].cpu(), sr)
        print(f"  ✓ {source_name}.wav")

    print("\n✅ Audio separation complete!")
    print(f"Stems saved in: {os.path.abspath(output_dir)}/")

if __name__ == "__main__":
    # Default to the MP3 file in the data directory
    input_file = "data/01 Benediction.mp3"

    # You can also pass a file as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    # Create output directory based on input filename
    input_name = Path(input_file).stem
    output_dir = f"separated/{input_name}"

    separate_audio(input_file, output_dir)
