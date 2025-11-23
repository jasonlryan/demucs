#!/usr/bin/env python3
"""
Simple HTTP server to serve the audio editor and separated audio files.
Run this script and open http://localhost:8000/audio_editor.html in your browser.
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow loading audio files
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def log_message(self, format, *args):
        # Custom log format
        print(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    # Change to the script directory
    os.chdir(Path(__file__).parent)
    
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🎵 Audio Editor Server")
        print(f"=" * 50)
        print(f"Server running at http://localhost:{PORT}/")
        print(f"Open http://localhost:{PORT}/audio_editor.html in your browser")
        print(f"=" * 50)
        print(f"Press Ctrl+C to stop the server")
        print()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")


