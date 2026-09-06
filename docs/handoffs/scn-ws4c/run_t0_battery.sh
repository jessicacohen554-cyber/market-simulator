#!/usr/bin/env bash
# SCN-WS4c — the full T0 battery (PRECOMMIT §1, 15 arms), rule-12 scheduled.
#
# Rule 12 [R-PARALLEL] as applied here:
#   * years are sequential inside every invocation (one year at T0 anyway);
#   * <= 2 concurrent invocations, and exactly 1 whenever a per-plant
#     multi-zone ISO (CAISO / PJM / MISO, ~8.6 GB each) is running, because
#     two of those cannot co-run on this 15 GB box.
# Phase A pairs the small ISOs; phase B runs the heavy ones strictly alone.
set -uo pipefail
L="docs/handoffs/scn-ws4c/launch_arm.sh"
R="results/scn-ws4-probe"
say () { echo "[$(date -u +%H:%M:%S)] === $* ==="; }

say "PHASE A — small ISOs, two invocations at a time"
bash $L ERCOT REF 2026 2026 $R & bash $L NEISO REF 2026 2026 $R & wait
bash $L ERCOT LOAD-HI 2026 2026 $R & bash $L NEISO LOAD-HI 2026 2026 $R & wait
bash $L ERCOT LOAD-HI-ORGANIC 2026 2026 $R & bash $L NYISO REF 2026 2026 $R & wait
bash $L NYISO LOAD-HI 2026 2026 $R & bash $L NYISO LOAD-HI-ORGANIC 2026 2026 $R & wait

say "PHASE B — per-plant multi-zone ISOs, ONE invocation at a time"
for arm in "CAISO REF" "CAISO LOAD-HI" "PJM REF" "PJM LOAD-HI" \
           "MISO REF" "MISO LOAD-HI" "MISO LOAD-HI-ORGANIC"; do
  set -- $arm
  bash $L "$1" "$2" 2026 2026 $R
done
say "T0 BATTERY COMPLETE"
