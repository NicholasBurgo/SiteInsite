#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
VENV_DIR="${ROOT_DIR}/.venv"

PYTHON_BIN="${PYTHON:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Error: python3 is required but not installed." >&2
    exit 1
  fi
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is required but not installed. Install Node.js 18+ first." >&2
  exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
  echo "Creating Python virtual environment in ${VENV_DIR}..."
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

echo "Building SiteInsite..."

echo "Installing backend dependencies..."
python -m pip install --upgrade pip wheel >/dev/null
python -m pip install -r "${BACKEND_DIR}/requirements.txt"

echo "Building React frontend..."
(
  cd "${FRONTEND_DIR}"
  npm install
  npm run build
)

echo "Build complete!"
echo "To start production:"
echo "  Backend (venv active): python -m uvicorn backend.app:app --port 5051"
echo "  Frontend: cd frontend && npm run preview"