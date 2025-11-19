#!/usr/bin/env bash
# Quick start script for Fedora Linux
# Run this from the project root: ./start-fedora.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/scripts/dev-fedora.sh"










