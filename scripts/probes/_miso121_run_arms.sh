#!/usr/bin/env bash
# miso-121 Phase 1 — the two pre-registered arms (PREREG §8.2).
#
# Arms SEQUENTIAL; years sequential inside each arm as a per-year invocation
# chain into ONE bundle (rule 12 RAM discipline + rule 16 one-bundle span).
# Rule 22: 2023-2025 only.
set -u

cd /home/user/market-simulator

KEEPER=results/calibration/miso117_ctheatrate_B
A=results/calibration/miso121_control_A
B=results/calibration/miso121_dualfuel_B
LOG=/tmp/miso121_arms

run_arm() {
  local out="$1" note="$2"; shift 2
  local first=1
  for y in 2023 2024 2025; do
    echo "=== $(date -u +%H:%M:%S) solving $out $y ==="
    if [ $first -eq 1 ]; then
      uv run python scripts/replay_keeper.py "$KEEPER" \
        --out-dir "$out" --years "$y" --note "$note" "$@" \
        >> "${LOG}_$(basename "$out").log" 2>&1 || return 1
      first=0
    else
      uv run python scripts/replay_keeper.py "$KEEPER" \
        --out-dir "$out" --years "$y" --reuse-solved "$out" --note "$note" "$@" \
        >> "${LOG}_$(basename "$out").log" 2>&1 || return 1
    fi
  done
}

run_arm "$A" "miso-121 arm A CONTROL — zero-delta same-HEAD replay of the miso-117b keeper (PREREG-miso121 §8.2)" \
  || { echo "ARM A FAILED"; exit 1; }
echo "=== $(date -u +%H:%M:%S) ARM A COMPLETE ==="

run_arm "$B" "miso-121 arm B TREATMENT — dual_fuel_switching=true, single delta vs arm A (PREREG-miso121 §8.2)" \
  --set dual_fuel_switching=true \
  || { echo "ARM B FAILED"; exit 1; }
echo "=== $(date -u +%H:%M:%S) ARM B COMPLETE ==="
