#!/usr/bin/env bash
# capx D78-ARM — the ONE solve: the shipped PJM T1-H posture at HEAD with
# owner ruling Q56 armed (retirement_sector_gate=True through _pjm_config), i.e.
# the BARE recipe, key fb16fda2ddb0a94a (PRECOMMIT-capx-d78arm §2). No flags
# beyond the recipe's own: Q55 stays IN (never --no-pjm-vre-accreditation-
# vintage — that flag reproduced D78-R2's graded control for D78-R3 and has no
# object here). PJM solo, years sequential (rule 12), HEAD-guarded.
#
#   bash docs/handoffs/d78arm/run_arm.sh
#
# The out-dir is the D67-ARM retention class (results/capacity-hindcast/, the
# REGISTERED shipped posture): heavy LP output gitignored, the slim ledgers
# committed, the sidecar registered through register_forecast_run.py.
set -euo pipefail
out="results/capacity-hindcast/pjm-2021-2025-realized-t1h-d78arm"
H0=$(git rev-parse HEAD)
PY=${PY:-uv run python}
echo "=== [$(date -u +%H:%M:%S)] D78-ARM armed pjm-t1h -> ${out}  HEAD GUARD ${H0}"
$PY scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2025 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics \
    --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during the arm"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] arm done, HEAD guard OK (${H0})"
