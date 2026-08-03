#!/usr/bin/env bash
# miso-121 Phase 1 — the two pre-registered arms (PREREG §8.2).
#
# ONE invocation per arm covering --years 2023 2024 2025, years sequential
# INSIDE the invocation (rules 12 / 16) — the miso-119 form.
#
# WHY NOT a per-year invocation chain: replay_keeper sets
#   kwargs["years"] = args.years
# so a `--years <one>` invocation writes meta.json with ONLY that year. The
# hourly sidecars accumulate across a chain, but the bundle's own provenance
# does not: after a 2023/2024/2025 chain the bundle claims years [2025]. That
# breaks the K5 year-span gate (which reads meta["years"]) and rule 16's
# one-bundle span, and the only way to "fix" it afterwards is to hand-edit a
# provenance artifact — which is not a thing to do. One invocation records the
# true span by construction.
#
# Arms SEQUENTIAL. Rule 22: 2023-2025 only.
set -u

cd /home/user/market-simulator

KEEPER=results/calibration/miso117_ctheatrate_B
A=results/calibration/miso121_control_A
B=results/calibration/miso121_dualfuel_B
LOG=/tmp/miso121_arms

echo "=== $(date -u +%H:%M:%S) ARM A (control) 2023 2024 2025 ==="
uv run python scripts/replay_keeper.py "$KEEPER" \
  --out-dir "$A" --years 2023 2024 2025 \
  --note "miso-121 arm A CONTROL — zero-delta same-HEAD replay of the miso-117b keeper (PREREG-miso121 §8.2)" \
  >> "${LOG}_control_A.log" 2>&1 || { echo "ARM A FAILED"; exit 1; }
echo "=== $(date -u +%H:%M:%S) ARM A COMPLETE ==="

echo "=== $(date -u +%H:%M:%S) ARM B (treatment) 2023 2024 2025 ==="
uv run python scripts/replay_keeper.py "$KEEPER" \
  --out-dir "$B" --years 2023 2024 2025 \
  --set dual_fuel_switching=true \
  --note "miso-121 arm B TREATMENT — dual_fuel_switching=true, single delta vs arm A (PREREG-miso121 §8.2)" \
  >> "${LOG}_dualfuel_B.log" 2>&1 || { echo "ARM B FAILED"; exit 1; }
echo "=== $(date -u +%H:%M:%S) ARM B COMPLETE ==="
