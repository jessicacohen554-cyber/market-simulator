#!/bin/bash
# PostToolUse hook on Edit|Write — keeper-change auditor trigger.
#
# "A new keeper is set" == an edit to an ISO's keeper shard
# frontend/data/backcast/keepers/<ISO>.json (a keeper id swapped/added/removed;
# index.json edits don't count — that is only the display-order registry).
# When a shard is written, this hook injects context telling the session to run
# the calibration-keeper-auditor subagent, which checks (and repairs) that the
# dashboard's keeper text — the Calibration Status page and each keeper's
# run-report header — still matches the keeper's actual run results, then
# refreshes that ISO's status part (status/<ISO>.js). The legacy monolith path
# (keepers.json) is still matched so a historical checkout stays guarded.
#
# It only nudges; it never blocks the edit and never mutates files itself (the
# subagent does the audit/fix so the work is reviewable). Stdlib tools only.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" 2>/dev/null || exit 0

# Edited path arrives as JSON on stdin (Edit/Write -> tool_input.file_path).
f=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)

case "$f" in
  */frontend/data/backcast/keepers/index.json|frontend/data/backcast/keepers/index.json) exit 0 ;;
  */frontend/data/backcast/keepers/README.md|frontend/data/backcast/keepers/README.md) exit 0 ;;
  */frontend/data/backcast/keepers/*.json|frontend/data/backcast/keepers/*.json) ;;
  */frontend/data/backcast/keepers.json|frontend/data/backcast/keepers.json) ;;
  *) exit 0 ;;
esac

iso=$(basename "$f" .json)

msg="A keeper change was just written to $f. \
Before finishing, launch the calibration-keeper-auditor subagent (Agent tool, \
subagent_type: calibration-keeper-auditor) to verify and repair the dashboard's \
keeper text against the current run results: it runs \
scripts/audit_keepers.py --iso $iso, rewrites any placeholder/stale sidecar \
definition, and refreshes that ISO's status part via \
scripts/build_status.py --iso $iso. Commit the resulting registry sidecar(s) + \
frontend/data/backcast/keepers/$iso.json + frontend/data/backcast/status/$iso.js \
(and status/shared.js only if the rubric changed) per the calibration-report \
skill — never the other ISOs' lanes."

# additionalContext surfaces the instruction to the model without blocking.
jq -cn --arg ctx "$msg" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $ctx}}' \
  2>/dev/null || printf '%s\n' "$msg"

exit 0
