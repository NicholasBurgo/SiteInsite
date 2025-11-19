#!/usr/bin/env bash
# Start only the frontend server
# Run this from the project root

set -euo pipefail

echo "Starting React Frontend..."
echo "=========================="
echo ""

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "Dependencies already installed ✓"
fi

echo ""
echo "Starting frontend server..."
echo ""
echo "📍 Access point: http://localhost:5173"
echo ""
echo "⚠️  Press Ctrl+C to stop"
echo ""

# Run the frontend
cd frontend
exec npm run dev










