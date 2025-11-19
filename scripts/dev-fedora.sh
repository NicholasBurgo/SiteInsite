#!/usr/bin/env bash
# Development helper for Fedora Linux
# Starts both backend and frontend with Fedora-specific setup

set -euo pipefail

echo "Starting SiteInsite (Fedora Linux)..."

# Ensure we are on Fedora
if [ ! -f /etc/fedora-release ]; then
    echo "Warning: This script is tailored for Fedora Linux"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Verify system dependencies -------------------------------------------------

if ! command -v python3 &>/dev/null; then
    echo "Python 3 not found. Installing via dnf..."
    sudo dnf install -y python3 python3-pip
fi

if ! command -v node &>/dev/null; then
    echo "Node.js not found. Installing via dnf..."
    sudo dnf install -y nodejs npm
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"

# Virtual environment --------------------------------------------------------

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

source venv/bin/activate
PROJECT_ROOT="$(pwd)"

# Python deps ----------------------------------------------------------------

echo "Upgrading pip..."
pip install --upgrade pip -q

echo "Installing Python dependencies..."
pip install -q -r backend/requirements.txt

# Optional Playwright install if JS rendering enabled ------------------------

if grep -q "RENDER_ENABLED=true" .env 2>/dev/null || [ "${RENDER_ENABLED:-false}" = "true" ]; then
    echo "RENDER_ENABLED=true detected. Ensuring Playwright is installed..."
    if ! pip show playwright &>/dev/null; then
        pip install playwright -q
        playwright install chromium
    fi
fi

# Node deps ------------------------------------------------------------------

echo "Installing Node.js dependencies..."
(cd frontend && npm install --silent)

# Launch services ------------------------------------------------------------

echo
echo "========================================="
echo "Starting services..."
echo "========================================="
echo

# Backend (background)
echo "Starting FastAPI backend..."
(cd backend && "$PROJECT_ROOT/venv/bin/python" -m uvicorn app:app --reload --port 5051) &
BACKEND_PID=$!

sleep 2

# Frontend (background)
echo "Starting React frontend..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

sleep 3

echo
echo "========================================="
echo "Services are running!"
echo "========================================="
echo

cat <<MSG
📍 Access the application:
   Frontend UI:  http://localhost:5173
   Backend API:  http://localhost:5051
   API Docs:     http://localhost:5051/docs

⚠️  Press Ctrl+C in this window to stop all services
MSG

trap "echo; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait