#!/usr/bin/env bash
# capx D81 — PHASE 3, the full 2021-2025 window, run only after the screen
# cleared (PRECOMMIT Addendum A.1). Both legs, PJM solo, sequential, each under
# a HEAD guard. Everything phase 3 reports is REPORTED, NOT GATED (Addendum
# A.3): nothing here is a criterion and nothing here can promote the arm.
#
#   bash docs/handoffs/d81/run_full.sh control   # base code (acbb5350)
#   bash docs/handoffs/d81/run_full.sh arm       # post-fix code
#
# Throwaway diagnostic probes (rule 29(c)): never registered, never a keeper,
# DELETED from results/ before the PR merges.
set -euo pipefail

name="$1"; shift
H0=$(git rev-parse HEAD)
out="results/hindcast/pjm-2021-2025-realized-t1h-d81-${name}"
PY=${PY:-uv run python}
echo "=== [$(date -u +%H:%M:%S)] FULL LEG ${name} -> ${out}  HEAD GUARD ${H0}"
$PY scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2025 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics "$@" --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during ${name}"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] ${name} done, HEAD guard OK (${H0})"
