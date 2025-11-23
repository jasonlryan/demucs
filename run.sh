#!/bin/bash

# Demucs Audio Separator - Startup Script
echo "🎵 Starting Demucs Audio Separator"
echo "=================================="

# Kill any existing Flask server on port 5001
lsof -ti:5001 | xargs kill -9 2>/dev/null

# Start Flask server in background
python3 app.py &
FLASK_PID=$!

echo "✅ Server started (PID: $FLASK_PID)"
echo ""
echo "🌐 Open your browser to:"
echo "   http://localhost:5001/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping server...'; kill $FLASK_PID 2>/dev/null; exit 0" INT

# Keep script running
wait $FLASK_PID
