#!/usr/bin/env bash
# SCN-WS1b-r2 leg 1 — the six paired T0 solves, SCORED AT 2027.
#
# RETARGETED 2026-09-06 (relaunch). The original ran a 2026-only solve of the
# reduced form `--set carbon_price_delta=25`. Both halves changed:
#
#   * the ARM is now the charter's full form `--set carbon_price_path=mid`,
#     released by SCN-WS1c's S2 floor repair (b1996141);
#   * the HORIZON is 2026->2027, because the phase-0 re-census proved
#     CARBON_PRICE_PATHS anchors EVERY registered RFF path at $0 in 2026, so a
#     2026-only solve of this axis is inert in all six ISOs by construction.
#     2027 is the first live year and is still below
#     ccs_retrofit_available_year = 2028, so ruling S5's gas_cc_ccs hold does
#     not reach it (ADDENDUM §(d)/(d.1), pushed before any solve).
#
# The run solves 2026 AND 2027 (capacity evolution is one-pass per year and
# needs its prior); 2027 is the scored year.
#
# Concurrency is rule 12 [R-PARALLEL]: the two arms of a SMALL ISO
# (ERCOT / NEISO / NYISO) may run concurrently; the two arms of a per-plant
# multi-zone ISO (PJM / MISO / CAISO) run STRICTLY SEQUENTIALLY, because each is
# ~8.6 GB on a 15 GB box. Years are ALWAYS sequential within an invocation.
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
    --iso "$ISO" --start-year 2026 --end-year 2027 \
    --out-dir "$OUT/$arm" "$@" > "$OUT/${arm}.log" 2>&1
  echo "[$(date -u +%H:%M:%S)] done  $ISO $arm rc=$?"
}

if [ "$MODE" = "par" ]; then
  run_arm REF &
  run_arm CARB --set carbon_price_path=mid &
  wait
else
  run_arm REF
  run_arm CARB --set carbon_price_path=mid
fi
echo "[$(date -u +%H:%M:%S)] $ISO pair complete"
