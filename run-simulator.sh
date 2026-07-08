#!/usr/bin/env bash
# Market Simulator - desktop run launcher (macOS / Linux).
# Mirrors run-simulator.bat: bootstraps a local venv + deps on first run,
# then opens the launcher UI. Run: ./run-simulator.sh
#
# This is a convenience launcher only, not the reference install. The
# canonical install/run path is `uv` + pyproject.toml/uv.lock (see
# README.md "Which install path?"); use this script for a quick local UI
# session when `uv` isn't available.
set -e
cd "$(dirname "$0")"

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Python 3.11+ was not found. Install it and re-run." >&2
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating local Python environment (first run only)..."
  "$PY" -m venv .venv
fi
VENV_PY=".venv/bin/python"

if [ ! -f ".venv/.deps_installed" ]; then
  echo "Installing dependencies (first run only - this can take a few minutes)..."
  "$VENV_PY" -m pip install --upgrade pip
  "$VENV_PY" -m pip install -e .
  touch ".venv/.deps_installed"
fi

echo "Starting the launcher at http://127.0.0.1:8765/ (Ctrl+C to stop)."
exec "$VENV_PY" tools/launcher.py "$@"
