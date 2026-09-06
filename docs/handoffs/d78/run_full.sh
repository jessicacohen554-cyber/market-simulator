#!/usr/bin/env bash
# capx D78 — the FULL 2021-2025 window (PRECOMMIT §6), run only after the
# rule-29 screen clears: the repaired arm and a same-HEAD control-P, one
# invocation each, PJM solo, sequential, HEAD-guarded.
#
#   bash docs/handoffs/d78/run_full.sh control-P
#   bash docs/handoffs/d78/run_full.sh arm --retirement-sector-gate
#
# The control bundle is deleted before merge (rule 29(c)); the arm keeps only
# its slim registered files (meta / run_config / forecast_verdict), as every
# registered PJM T1-H run does.
set -euo pipefail

name="$1"; shift
H0=$(git rev-parse HEAD)
case "$name" in
  arm) out="results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate" ;;
  *)   out="results/hindcast/pjm-2021-2025-realized-t1h-d78-${name}" ;;
esac
PY=${PY:-uv run python}
echo "=== [$(date -u +%H:%M:%S)] FULL LEG ${name} -> ${out}  HEAD GUARD ${H0}  cwd $(pwd)"
$PY scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2025 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics "$@" --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during ${name}"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] ${name} done, HEAD guard OK (${H0})"
