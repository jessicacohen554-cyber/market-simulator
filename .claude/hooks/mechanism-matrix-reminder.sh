#!/bin/bash
# SessionStart hook: rule 28 [R-MECH-MATRIX] reminder.
#
# Runs in EVERY session (local and web, unlike the web-only session-start.sh)
# so calibration/forecast lane sessions see the mechanism-matrix duties even
# when the handoff prompt forgot to cite them. Prints a short pointer block;
# SessionStart stdout is injected into the session context. Never fails the
# session: every step is guarded and the script always exits 0.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" || exit 0

MATRIX="docs/codebase-site/data/mechanism-matrix.js"
[ -f "$MATRIX" ] || exit 0

updated=$(grep -m1 -o 'updated: "[0-9-]*"' "$MATRIX" 2>/dev/null | cut -d'"' -f2)

cat <<EOF
[R-MECH-MATRIX] Cross-ISO mechanism matrix (last updated: ${updated:-unknown}).
If this session proposes, tests, or adds a calibration/forecast mechanism:
- BEFORE proposing a lever: check the target ISO's lever queue
  (docs/mechanism-testing-matrix.md section 5) and the cell verdicts in
  $MATRIX (rendered: docs/codebase-site/mechanism-matrix.html).
  Never re-test a cell marked R/I/G without new evidence.
- AFTER testing a mechanism (probe, candidate, or keeper - rejections too):
  update that cell + evidence citation in $MATRIX in THIS session.
- NEW ScenarioConfig mechanism: add its matrix row in the same PR
  (CI enforces this half: scripts/check_mechanism_matrix.py).
EOF
exit 0
