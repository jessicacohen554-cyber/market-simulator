#!/bin/bash
# SessionStart hook (Claude Code on the web).
#
# Guarantees the lint toolchain is present in the ephemeral web container so the
# ruff-autofix PostToolUse hook (and any manual `uv run ruff ...`) can actually
# run during the session. `ruff` ships in the project's `dev` dependency group,
# which `uv sync` installs by default, so a single `uv sync` installs the exact
# pinned ruff from uv.lock — the same toolchain the .github/workflows/ci.yml
# `lint` job uses in CI (the former standalone lint.yml was folded into ci.yml
# when CI was restored).
#
# Synchronous + idempotent: re-running is a near no-op once the container is
# warm, and finishing before the agent starts means ruff is ready on the very
# first edit (no race with the PostToolUse hook).
set -euo pipefail

# Web-only. Local sessions already have whatever env the developer set up; don't
# mutate it. ($CLAUDE_CODE_REMOTE == "true" only inside Claude Code on the web.)
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Install runtime + dev deps (ruff, pytest, ...) from the locked environment.
uv sync
