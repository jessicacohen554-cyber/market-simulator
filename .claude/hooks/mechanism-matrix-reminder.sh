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
SHARD_DIR="docs/codebase-site/data/mechanism-matrix"
[ -f "$MATRIX" ] || exit 0

# Freshest `updated:` stamp across the base + the per-ISO shards (each lane
# bumps only its own shard's stamp since the 2026-08-11 sharding).
updated=$(grep -h -m1 -o 'updated: "[0-9-]*"' "$MATRIX" "$SHARD_DIR"/*.js 2>/dev/null \
  | cut -d'"' -f2 | sort | tail -1)

cat <<EOF
[R-MECH-MATRIX] Cross-ISO mechanism matrix (last updated: ${updated:-unknown}).
SHARDED PER ISO: mechanism-level rows live in $MATRIX;
each ISO's cell verdicts, fc postures, evidence and keeper/gates stamps live in
$SHARD_DIR/<ISO>.js — a lane edits ONLY its own ISO's shard.
If this session proposes, tests, or adds a calibration/forecast mechanism:
- BEFORE proposing a lever: check the target ISO's lever queue
  (docs/mechanism-testing-matrix.md section 5) and the cell verdicts in
  $SHARD_DIR/<ISO>.js (rendered: docs/codebase-site/mechanism-matrix.html).
  Never re-test a cell marked R/I/G without new evidence.
- AFTER testing a mechanism (probe, candidate, or keeper - rejections too):
  update that cell + evidence citation in $SHARD_DIR/<ISO>.js in THIS session.
- NEW ScenarioConfig mechanism: add its row in $MATRIX plus a cell
  line in EVERY shard, in the same PR
  (CI enforces this half: scripts/check_mechanism_matrix.py).
[CLOSE-OUT PLAN] docs/backcast-closeout-plan-2026-10.md is the backcast close-out
program (2026-10-02): section 3.<ISO> is the ranked lever sequence a calibration
lane takes its next step from (also at the head of each ISO's lever queue in
docs/mechanism-testing-matrix.md section 5); section 5 is the owner decision
queue; section 2.1 is the EIA-860 settlement (W0). Go off-plan only with a
stated reason in the PRECOMMIT. Evidence: docs/records/governance/closeout-2026-10/.
EOF
exit 0
