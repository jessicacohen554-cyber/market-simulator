#!/bin/bash
# miso-72 winter fuel-security probe solve chain (per-year + --reuse-solved).
#
# RAM <=16 GB: solves ONE fresh LP per process (the one-process all-three-years
# path OOMs on the year-3 MISO co-opt peak at HEAD). Mirrors the _miso71 pattern.
#   base = winter OFF (same-box drift control)
#   main = winter ON  (miso_winter_citygate_daily via prb_overrides)
# Sequential, never concurrent (rule 12). Rule 22: 2023/2024/2025 only.
#
# IDEMPOTENT: skips a variant whose <acc>/<v>_final/system.parquet already exists
# (so a re-run after a reaped process resumes at the missing variant). REUSE
# REQUIRES a clean tree under src/scripts/data and NO src/scripts/data commit
# between the per-year solves — do not commit while this runs.
#
# Usage:  bash scripts/probes/_miso72_chain.sh
set -e
cd "$(dirname "$0")/../.."
export MALLOC_ARENA_MAX=1 OMP_NUM_THREADS=1 MARKET_SIM_HIGHS_THREADS=1
PY=.venv/bin/python
ACC=results/calibration/miso72_probe_acc
PROBE=scripts/run_miso72_winter_probe.py
mkdir -p "$ACC"
ts() { date +%H:%M:%S; }

run_chain() {  # $1 = variant (base|main); $2 = extra flag ("" | --winter)
  local v="$1" flag="$2"
  if [ -f "$ACC/${v}_final/system.parquet" ]; then
    echo ">>> $v already complete ($ACC/${v}_final) — skip  $(ts)"
    return 0
  fi
  echo "===== $v CHAIN (${flag:-base}) start $(ts) ====="
  rm -rf "$ACC/${v}_2023" "$ACC/${v}_2324" "$ACC/${v}_final"
  $PY $PROBE $flag --out-dir "$ACC/${v}_2023" --years 2023
  $PY $PROBE $flag --out-dir "$ACC/${v}_2324" --years 2023 2024 --reuse-solved "$ACC/${v}_2023"
  $PY $PROBE $flag --out-dir "$ACC/${v}_final" --years 2023 2024 2025 --reuse-solved "$ACC/${v}_2324"
  rm -rf "$ACC/${v}_2023" "$ACC/${v}_2324"
  echo ">>> $v FINAL bundle = $ACC/${v}_final  $(ts)"
}

run_chain base ""
run_chain main "--winter"
echo "ALLDONE $(ts)"
