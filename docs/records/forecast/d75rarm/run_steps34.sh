#!/usr/bin/env bash
# capx D75-R-ARM steps 3-4 — THE ONE SOLVE: the shipped PJM T1-H posture at
# HEAD, i.e. the BARE recipe, key fb16fda2ddb0a94a (ADDENDUM B §1.1, re-measured
# at abdd30c9 in §7). No flags beyond the recipe's own: NEVER
# --no-pjm-vre-accreditation-vintage (that reaches D78-R2's arm) and NEVER
# --no-retirement-sector-gate (that reaches the Q55 posture) — the row is the
# JOINT Q55+Q56 posture, which is what the recipe carries at HEAD.
#
# This is the SAME invocation docs/handoffs/d78arm/run_arm.sh names, at the same
# key against the same control: there is exactly one bare pjm-t1h recipe at HEAD
# (ADDENDUM B §2). Solving it once discharges both lanes' registration.
#
#   bash docs/handoffs/d75rarm/run_steps34.sh
#
# PJM solo, years 2021-2025 SEQUENTIAL in ONE invocation (rule 12 [R-PARALLEL]).
# Out-dir is the D67-ARM retention class (results/capacity-hindcast/, the
# REGISTERED shipped posture): heavy LP output gitignored, slim ledgers
# committed, sidecar registered through register_forecast_run.py (rule 15).
#
# HEAD GUARD (charter, mandatory): no commit is made while this runs.
set -euo pipefail
out="results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm"
H0=$(git rev-parse HEAD)
PY=${PY:-uv run python}
echo "=== [$(date -u +%H:%M:%S)] D75-R-ARM steps 3-4: bare pjm-t1h -> ${out}"
echo "=== HEAD GUARD ${H0}   DECLARED KEY fb16fda2ddb0a94a"
$PY scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2025 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics \
    --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during the solve"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] solve done, HEAD guard OK (${H0})"
realized=$($PY -c "import json;print(json.load(open('${out}/meta.json'))['cache_key'])")
echo "=== REALIZED KEY ${realized}   DECLARED fb16fda2ddb0a94a"
[ "$realized" = "fb16fda2ddb0a94a" ] || {
    echo "STOP: realized key != declared key. The arm does not reproduce the"
    echo "recipe the A/Bs were measured on; the Q55/Q56 bases need re-reading."
    exit 91
}
echo "=== realized == declared"
