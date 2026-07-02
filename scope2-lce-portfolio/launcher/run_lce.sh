#!/usr/bin/env bash
# Desktop launcher entry point (ADR 0016): resolve a usable Python, then start
# the local launch-page server (`python -m lce_portfolio.launcher`). Twin of
# run_lce.bat — keep the two in lockstep on any behavior change.
#
# Usage:
#   ./run_lce.sh                # open the launch page in the default browser
#   ./run_lce.sh --no-open      # start the server without opening a browser
#   ./run_lce.sh --port 8765    # bind a fixed port instead of an ephemeral one
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"           # scope2-lce-portfolio/
VENV_PYTHON="$TOOL_ROOT/../.venv/bin/python"        # repo-relative venv (ADR 0016 §4)

MIN_PYTHON_MINOR=11   # pyproject.toml requires-python = ">=3.11"
REQUIRED_MODULES=(highspy numpy pandas)

# Checks version >= 3.$MIN_PYTHON_MINOR and that REQUIRED_MODULES import
# cleanly; prints nothing, exit status is the pass/fail signal.
check_python() {
  local candidate="$1"
  [ -x "$candidate" ] || return 1
  "$candidate" - "$MIN_PYTHON_MINOR" "${REQUIRED_MODULES[@]}" <<'PYEOF'
import importlib
import sys

min_minor = int(sys.argv[1])
modules = sys.argv[2:]
if sys.version_info < (3, min_minor):
    sys.exit(1)
for mod in modules:
    try:
        importlib.import_module(mod)
    except ImportError:
        sys.exit(1)
PYEOF
}

PYTHON=""
if check_python "$VENV_PYTHON"; then
  PYTHON="$VENV_PYTHON"
else
  for name in python3 python; do
    candidate="$(command -v "$name" || true)"
    if [ -n "$candidate" ] && check_python "$candidate"; then
      PYTHON="$candidate"
      break
    fi
  done
fi

if [ -z "$PYTHON" ]; then
  echo "error: no usable Python found for the LCE portfolio launcher." >&2
  echo "  Tried: $VENV_PYTHON, then python3/python on PATH." >&2
  echo "  Need Python >= 3.$MIN_PYTHON_MINOR with highspy, numpy, and pandas importable." >&2
  echo "  Fix: create the venv and install dependencies, e.g.:" >&2
  echo "    python3 -m venv .venv" >&2
  echo "    .venv/bin/pip install -r scope2-lce-portfolio/requirements.txt" >&2
  exit 1
fi

cd "$TOOL_ROOT"
# Run straight from a clone without requiring `pip install -e .` (mirrors
# run_portfolio.py's sys.path.insert trick, done here via PYTHONPATH since
# this is a `-m` invocation, not a script that can insert its own path).
export PYTHONPATH="$TOOL_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m lce_portfolio.launcher "$@"
