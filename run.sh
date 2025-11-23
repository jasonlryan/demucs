#!/bin/bash

# Audio Separation App - Startup Script
echo "🎵 Starting Audio Separation App"
echo "=================================="
echo ""

# Kill any existing servers on ports 3000 and 5001
echo "🧹 Cleaning up existing servers..."
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
    echo ""
fi

# Start Flask backend server in background
echo "🚀 Starting Flask backend (port 5001)..."
python3 app.py > flask.log 2>&1 &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 2

# Start React frontend server in background
echo "🚀 Starting React frontend (port 3000)..."
BROWSER=none npm start > react.log 2>&1 &
REACT_PID=$!

# Wait a moment for React to start
sleep 3

echo ""
echo "✅ Both servers started!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:5001"
echo ""
echo "📋 Process IDs:"
echo "   Flask: $FLASK_PID"
echo "   React: $REACT_PID"
echo ""
echo "📝 Logs:"
echo "   Flask: tail -f flask.log"
echo "   React: tail -f react.log"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    # Kill by PID
    kill $FLASK_PID 2>/dev/null
    kill $REACT_PID 2>/dev/null
    # Kill child processes
    pkill -P $FLASK_PID 2>/dev/null
    pkill -P $REACT_PID 2>/dev/null
    # Kill by port (more reliable for React)
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up trap for Ctrl+C
trap cleanup INT TERM

# Wait for both processes
wait $FLASK_PID $REACT_PID 2>/dev/null
