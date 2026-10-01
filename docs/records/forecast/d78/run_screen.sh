#!/usr/bin/env bash
# capx D78 — the rule-29 SCREEN legs on D58's own span (2021-2023: solve years
# {2021, 2023}, 2022 bridged), PJM solo, sequential, each under a HEAD guard.
#
#   bash docs/handoffs/d78/run_screen.sh control-P            # gate off
#   bash docs/handoffs/d78/run_screen.sh d58-arm --retirement-sector-gate   # seam as built (pre-fix code)
#   bash docs/handoffs/d78/run_screen.sh arm --retirement-sector-gate       # seam repaired (post-fix code)
#
# Every bundle is a THROWAWAY diagnostic probe (rule 29(c)): never registered,
# never a keeper, deleted from results/ before the PR merges. Every number the
# session cites lives in PRECOMMIT/FINDING-capx-d78-2026-09-06.md and
# docs/handoffs/d78/screen_compare.json.
set -euo pipefail

name="$1"; shift
H0=$(git rev-parse HEAD)
out="results/hindcast/pjm-2021-2023-realized-t1h-d78-${name}"
# PY overrides the interpreter so legs 1-2 can run from a worktree pinned at
# the phase-0 commit with the main tree's venv (PYTHONPATH=<worktree>/src),
# while the fix is built on the branch — see PRECOMMIT §3.
PY=${PY:-uv run python}
echo "=== [$(date -u +%H:%M:%S)] SCREEN LEG ${name} -> ${out}  HEAD GUARD ${H0}  cwd $(pwd)"
$PY scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2023 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics "$@" --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during ${name}"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] ${name} done, HEAD guard OK (${H0})"
