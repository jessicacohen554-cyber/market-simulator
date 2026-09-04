#!/usr/bin/env bash
# nyiso-188 Object-1 arm chain (PREREG-nyiso188 §1 Object 1, §5 S2):
#   Arm 1R  = keeper recipe on the re-derived ramp-envelope artifact (remap armed)
#   Arm 1RE = Arm 1R + the re-derived v2 emission-rate artifact
# The re-derived artifacts are installed under their committed NAMES (the loader
# resolves by name), one arm at a time, years sequential within each invocation
# (rule 12); nothing else may solve while a swapped file is on disk. The
# committed (control) blobs are restored from origin/main at the end unless
# KEEP_ARM_ARTIFACTS=1 (promotion path: the candidate's artifacts stay in place
# to be committed with it).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"
export PYTHONPATH="$REPO:$REPO/src"
SCR="${NYISO188_SCRATCH:?set NYISO188_SCRATCH to the scratch dir holding ramp/ramp_post_remap.csv and plant_emission_rates_v2.parquet}"
KEEPER=results/calibration/nyiso187_astoria_routing
P=data/raw/_processed-legacy
LOG="${NYISO188_LOG:-$SCR}"

step() { echo "[$(date -u +%H:%M:%S)] $*"; }

# --- Arm 1R: ramp only -------------------------------------------------------
step "install re-derived ramp envelopes"
cp "$SCR/ramp/ramp_post_remap.csv" "$P/campd_ramp_envelopes_NYISO.csv"
sha256sum "$P/campd_ramp_envelopes_NYISO.csv"
step "solve Arm 1R -> results/calibration/nyiso188_ramp"
python3 scripts/replay_keeper.py "$KEEPER" --out-dir results/calibration/nyiso188_ramp \
  --years 2023 2024 2025 \
  --note "nyiso-188 Arm 1R: the nyiso-187 keeper recipe (ZERO scenario_config changes) on the re-derived campd_ramp_envelopes_NYISO.csv (committed invocation, CAMPD_UNIT_PLANT_REMAP armed: 55375 / 57664 enveloped separately, the (0, CC) class-fraction row moves with its pool). PREREG-nyiso188 §1 Object 1." \
  > "$LOG/arm1r.log" 2>&1
step "Arm 1R done"

# --- Arm 1RE: ramp + v2 emissions --------------------------------------------
step "install re-derived v2 emission rates"
cp "$SCR/plant_emission_rates_v2.parquet" "$P/plant_emission_rates_v2.parquet"
cp "$SCR/plant_emission_rates_v2.csv" "$P/plant_emission_rates_v2.csv"
sha256sum "$P/plant_emission_rates_v2.parquet"
step "solve Arm 1RE -> results/calibration/nyiso188_ramp_emis"
python3 scripts/replay_keeper.py "$KEEPER" --out-dir results/calibration/nyiso188_ramp_emis \
  --years 2023 2024 2025 \
  --note "nyiso-188 Arm 1RE: Arm 1R plus the re-derived plant_emission_rates_v2.parquet (the curate seam applies CAMPD_UNIT_PLANT_REMAP per (facility, unit); 57664 takes its measured CT3 / CT4 rates, 55375 keeps CT1 / CT2; every other plant reproduces to float noise). PREREG-nyiso188 §1 Object 1." \
  > "$LOG/arm1re.log" 2>&1
step "Arm 1RE done"

if [ "${KEEP_ARM_ARTIFACTS:-0}" != "1" ]; then
  step "restore committed artifacts from origin/main"
  git checkout origin/main -- "$P/campd_ramp_envelopes_NYISO.csv" "$P/plant_emission_rates_v2.parquet" "$P/plant_emission_rates_v2.csv"
  git reset -q -- "$P/campd_ramp_envelopes_NYISO.csv" "$P/plant_emission_rates_v2.parquet" "$P/plant_emission_rates_v2.csv"
  sha256sum "$P/campd_ramp_envelopes_NYISO.csv" "$P/plant_emission_rates_v2.parquet"
fi
step "chain complete"
