#!/usr/bin/env bash
# SCN-WS1b leg 1 — the six paired 2026 T0 solves (PRECOMMIT §3.1).
#
# One ISO per invocation of this script. Concurrency is rule 12 [R-PARALLEL]:
# the two arms of a SMALL ISO (ERCOT / NEISO / NYISO) run concurrently; the
# two arms of a per-plant multi-zone ISO (PJM / MISO / CAISO) run STRICTLY
# SEQUENTIALLY, because each is ~8.6 GB on a 15 GB box.
#
# Usage:  bash docs/handoffs/scn-ws1b/launch_t0.sh <ISO> <par|seq>
set -uo pipefail
ISO="$1"; MODE="${2:-seq}"
LOW="$(echo "$ISO" | tr 'A-Z' 'a-z')"
OUT="results/scn-ws1-probe/${LOW}"
PY=".venv/bin/python"
mkdir -p "$OUT"

run_arm () {
  local arm="$1"; shift
  echo "[$(date -u +%H:%M:%S)] start $ISO $arm"
  PYTHONPATH=. "$PY" scripts/run_full_horizon.py \
    --iso "$ISO" --start-year 2026 --end-year 2026 \
    --out-dir "$OUT/$arm" "$@" > "$OUT/${arm}.log" 2>&1
  echo "[$(date -u +%H:%M:%S)] done  $ISO $arm rc=$?"
}

if [ "$MODE" = "par" ]; then
  run_arm REF &
  run_arm CARB --set carbon_price_delta=25 &
  wait
else
  run_arm REF
  run_arm CARB --set carbon_price_delta=25
fi
echo "[$(date -u +%H:%M:%S)] $ISO pair complete"
