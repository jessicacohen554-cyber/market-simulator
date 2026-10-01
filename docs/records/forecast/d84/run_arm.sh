#!/usr/bin/env bash
# capx D84 — the ARM leg: the PJM thermal ELCC delivery-year vintage axis.
#
# Differs from run_ctl.sh in EXACTLY ONE field
# (ScenarioConfig.pjm_thermal_accreditation_vintage), which is the confinement
# the screen's leg 3 then re-checks on the solve itself.
#
# DECLARED KEY: b9fa47dedb6c3319. The bundle is gitignored (rule 29(c)
# discharged by .gitignore) and is NOT deleted (rule 31 [R-RETAIN]).
set -euo pipefail
out="results/hindcast/pjm-2021-2025-realized-t1h-d84-thermalvintage"
H0=$(git rev-parse HEAD)
echo "=== [$(date -u +%H:%M:%S)] D84 arm -> ${out}  HEAD GUARD ${H0}"
python3 scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2025 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics \
    --pjm-thermal-accreditation-vintage \
    --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during arm"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] arm done, HEAD guard OK (${H0})"
