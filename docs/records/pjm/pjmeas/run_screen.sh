#!/usr/bin/env bash
# PJM RUBRIC-RESIDUAL — THE SCREEN (rule 29 [R-SCREEN] step 1).
#
# ONE solved year (2021), which is the minimum that exercises the mechanism at
# its measured footprint: the whole zero-E&AS decided cohort is the 2022
# decision (103 units / 8,693.3 MW), and 2022 is a BRIDGED year decided off the
# 2021 solve. Screen year named in PRECOMMIT-pjm-eas-operand-2026-09-07.md §5
# BEFORE this ran, on the mechanism's footprint and never on a residual.
#
# Same invocation as docs/handoffs/d75rarm/run_steps34.sh (the control) with the
# year span truncated and the declared arm added. THE SCREEN BUNDLE IS A
# THROWAWAY DIAGNOSTIC PROBE: never registered, never a keeper, never quoted as
# a keeper number, and DELETED BEFORE MERGE (rule 29(c)) — every number the lane
# cites lives in the FINDING.
#
# HEAD GUARD (charter, mandatory): no commit is made while this runs.
set -euo pipefail
out="results/capacity-hindcast/pjm-screen-eas-2021-2022-arm"
declared="cf9b7dc1ca285c35"
H0=$(git rev-parse HEAD)
PY=${PY:-python3}
echo "=== [$(date -u +%H:%M:%S)] PJM E&AS screen -> ${out}"
echo "=== HEAD GUARD ${H0}   DECLARED KEY ${declared}"
$PY scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2022 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics \
    --energy-reserve-coopt --pjm-reserve-pergen --pjm-reserve-supply-cap \
    --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during the solve"; exit 90; }
realized=$($PY -c "import json;print(json.load(open('${out}/meta.json'))['cache_key'])")
echo "=== REALIZED KEY ${realized}   DECLARED ${declared}"
[ "$realized" = "$declared" ] || {
    echo "STOP: realized key != the key declared in the PRECOMMIT before the solve."
    echo "The arm is not the arm that was declared; nothing downstream may be read."
    exit 91
}
echo "=== realized == declared; grade with grade_screen.py"
