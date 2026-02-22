#!/usr/bin/env bash
# Start only the backend server
# Run this from the project root

set -euo pipefail

echo "Starting FastAPI Backend..."
echo "============================"
echo ""

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Save the project root path before changing directories
PROJECT_ROOT="$PWD"

# Upgrade pip
pip install --upgrade pip -q

# Install dependencies
echo "Installing/updating Python dependencies..."
pip install -q -r backend/requirements.txt

echo ""
echo "Starting backend server..."
echo ""
echo "📍 Access points:"
echo "   Backend API: http://localhost:5051"
echo "   API Docs:    http://localhost:5051/docs"
echo "   ReDoc:       http://localhost:5051/redoc"
echo ""
echo "⚠️  Press Ctrl+C to stop"
echo ""

# Run the backend from inside the backend directory
cd backend

# Use the venv's Python explicitly
exec "$PROJECT_ROOT/venv/bin/python" -m uvicorn app:app --reload --port 5051

