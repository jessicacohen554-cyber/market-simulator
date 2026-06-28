#!/bin/bash
# PostToolUse hook on Edit|Write — keeper-change auditor trigger.
#
# "A new keeper is set" == an edit to frontend/data/backcast/keepers.json (a
# keeper id swapped/added/removed). When that file is written, this hook injects
# context telling the session to run the calibration-keeper-auditor subagent,
# which checks (and repairs) that the dashboard's keeper text — the Calibration
# Status page and each keeper's run-report header — still matches the keeper's
# actual run results, then refreshes status.js.
#
# It only nudges; it never blocks the edit and never mutates files itself (the
# subagent does the audit/fix so the work is reviewable). Stdlib tools only.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" 2>/dev/null || exit 0

# Edited path arrives as JSON on stdin (Edit/Write -> tool_input.file_path).
f=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)

case "$f" in
  */frontend/data/backcast/keepers.json|frontend/data/backcast/keepers.json) ;;
  *) exit 0 ;;
esac

msg="A keeper change was just written to frontend/data/backcast/keepers.json. \
Before finishing, launch the calibration-keeper-auditor subagent (Agent tool, \
subagent_type: calibration-keeper-auditor) to verify and repair the dashboard's \
keeper text against the current run results: it runs scripts/audit_keepers.py, \
rewrites any placeholder/stale sidecar definition, and refreshes status.js. \
Commit the resulting registry sidecar(s) + status.js + keepers.json per the \
calibration-report skill."

# additionalContext surfaces the instruction to the model without blocking.
jq -cn --arg ctx "$msg" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $ctx}}' \
  2>/dev/null || printf '%s\n' "$msg"

exit 0
