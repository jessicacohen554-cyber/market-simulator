#!/bin/bash
# PostToolUse hook on Edit|Write — ruff autofix gate.
#
# Why PostToolUse (not Stop): a session commits+pushes *within* a turn, and the
# Stop hook only fires *after* the turn ends — too late to keep an unclean push
# from landing. Fixing each Python file the instant it is written guarantees the
# bytes are already ruff-clean by the time the agent stages and pushes them, so
# the tree physically cannot fail the .github/workflows/ci.yml `lint` job
# (`ruff check .` / `ruff format --check .`; the former standalone lint.yml was
# folded into ci.yml when CI was restored).
#
# SAFETY: applies ONLY the fixes the pinned baseline already uses. `ruff check
# --fix` applies ruff's *safe* fixes by default (no --unsafe-fixes), and both
# commands read [tool.ruff.lint] from pyproject.toml — this hook never changes
# the rule selection/ignores and never enables unsafe fixes. It mirrors exactly
# the two commands CI runs, just in write mode.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" 2>/dev/null || exit 0

# The edited path arrives as JSON on stdin (Edit/Write -> tool_input.file_path).
f=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)

# Only Python files can violate the ruff gate; skip everything else cheaply.
case "$f" in
  *.py) ;;
  *) exit 0 ;;
esac

command -v uv >/dev/null 2>&1 || exit 0

# Whole-tree, matching CI's scope exactly: safe autofixes, then format.
uv run ruff check --fix . >/dev/null 2>&1 || true
uv run ruff format . >/dev/null 2>&1 || true

# Re-stage the just-edited file ONLY if it was already staged, so the committed
# bytes are the fixed ones. Scoped to "$f" on purpose: never auto-stage other
# files ruff may have touched (e.g. work owned by a parallel session).
if git diff --cached --name-only -- "$f" 2>/dev/null | grep -q .; then
  git add -- "$f" 2>/dev/null || true
fi

exit 0
