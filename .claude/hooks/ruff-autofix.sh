#!/bin/bash
# PostToolUse hook on Edit|Write — ruff autofix gate.
#
# Why PostToolUse (not Stop): a session commits+pushes *within* a turn, and the
# Stop hook only fires *after* the turn ends — too late to keep an unclean push
# from landing. Fixing each Python file the instant it is written guarantees the
# bytes are already ruff-clean by the time the agent stages and pushes them.
#
# SCOPED TO THE EDITED FILE ONLY (HOUSE-1 repair 2026-08-08; incident: sitting
# Addendum T.1, docs/handoffs/ffr-owner-sitting-2026-08-02.md). This hook
# originally ran `ruff check --fix .` / `ruff format .` over the WHOLE TREE on
# any .py Write/Edit, "matching CI's scope". That was a hazard, not a
# guarantee: whenever main itself carries bytes failing `ruff format --check`
# (2026-08-05: constants.py, a 3,960 → 9,508-line reflow; 2026-08-08 again:
# tests/unit/data/test_outages.py), the hook rewrote files the session never
# touched — a rule-27 [R-PUSH] full-file rewrite every session had to trap
# manually before staging. Formatting only the file actually written keeps the
# real guarantee (the bytes THIS session produces are ruff-clean) while files
# it did not edit stay byte-identical, whatever state main is in. The tree-wide
# CI lint job still covers the tree; this hook covers the session's own writes.
#
# SAFETY: applies ONLY the fixes the pinned baseline already uses. `ruff check
# --fix` applies ruff's *safe* fixes by default (no --unsafe-fixes), and both
# commands read [tool.ruff.lint] from pyproject.toml — this hook never changes
# the rule selection/ignores and never enables unsafe fixes.
#
# --force-exclude makes ruff honor pyproject's exclusions (extend-exclude:
# constants.py, scripts/archive, scripts/probes, results) even for a path
# passed explicitly on the command line — without it ruff processes ANY named
# path, exclusions notwithstanding, so an Edit to constants.py itself would
# re-arm the exact T.1 reflow this hook exists to prevent.
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

# The edited file ONLY — never the tree: safe autofixes, then format.
uv run ruff check --fix --force-exclude -- "$f" >/dev/null 2>&1 || true
uv run ruff format --force-exclude -- "$f" >/dev/null 2>&1 || true

# Re-stage the just-edited file ONLY if it was already staged, so the committed
# bytes are the fixed ones. Scoped to "$f" on purpose: never auto-stage other
# files ruff may have touched (e.g. work owned by a parallel session).
if git diff --cached --name-only -- "$f" 2>/dev/null | grep -q .; then
  git add -- "$f" 2>/dev/null || true
fi

exit 0
