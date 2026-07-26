#!/bin/bash
# miso-61 solve chain: main then zero-forcing ablation twin, SEQUENTIALLY
# (rule 12: never parallel year/twin solves — a MISO full-structure year
# needs ~15 GB; swap /swapfile-miso must be on).
set -uo pipefail
cd /home/user/market-simulator
PY=.venv/bin/python
LOG=results/calibration/miso61_rpe_pricing_solve.log
LOGA=results/calibration/miso61_rpe_pricing_ablation_solve.log

echo "=== miso-61 MAIN start $(date -u +%FT%TZ) ===" | tee "$LOG"
$PY scripts/probes/_miso61_rpe_pricing.py main >>"$LOG" 2>&1
rc=$?
echo "=== miso-61 MAIN exit $rc $(date -u +%FT%TZ) ===" | tee -a "$LOG"
if [ $rc -ne 0 ]; then
  echo "MAIN FAILED — not starting twin" | tee -a "$LOG"
  exit $rc
fi

echo "=== miso-61 ABLATION start $(date -u +%FT%TZ) ===" | tee "$LOGA"
$PY scripts/probes/_miso61_rpe_pricing.py ablation >>"$LOGA" 2>&1
rc=$?
echo "=== miso-61 ABLATION exit $rc $(date -u +%FT%TZ) ===" | tee -a "$LOGA"
exit $rc
