#!/usr/bin/env bash
# SCN-WS1b leg 2 — one ISO's T1-F carbon ladder, 2026-2030 (PRECOMMIT §3.5).
#
# Four cases (REF + CARB-LO/MID/HI = carbon_price_delta 15/25/50), 5 solve-years
# each, through the committed `market-sim matrix` harness. --workers 2 is the
# rule 12 [R-PARALLEL] cap inside one invocation; ONE ISO AT A TIME, and never
# alongside a PJM/MISO/CAISO leg.
#
# Usage:  bash docs/handoffs/scn-ws1b/launch_ladder.sh <ISO>
set -uo pipefail
ISO="$1"
LOW="$(echo "$ISO" | tr 'A-Z' 'a-z')"
OUT="results/scn-ws1-ladder/${LOW}"
mkdir -p "$OUT"
echo "[$(date -u +%H:%M:%S)] start $ISO ladder 2026-2030"
PYTHONPATH=. .venv/bin/python -m market_sim.runner matrix \
  --config "configs/scenarios/${LOW}_scenario_base_2026_2030.yaml" \
  --matrix docs/handoffs/scn-ws1b/carbon-ladder-cases.yaml \
  --iso "$ISO" --workers 2 --out-dir "$OUT" > "$OUT/ladder.log" 2>&1
echo "[$(date -u +%H:%M:%S)] done $ISO ladder rc=$?"
