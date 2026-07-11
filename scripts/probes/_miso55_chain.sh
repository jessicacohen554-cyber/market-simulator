#!/bin/bash
# miso-55 solve chain: main then zero-forcing ablation twin, SEQUENTIALLY
# (rule 12: never parallel year/twin solves — a MISO full-structure year
# needs ~15 GB; swap /swapfile-miso must be on).
set -uo pipefail
cd /home/user/market-simulator
PY=.venv/bin/python
LOG=results/calibration/miso55_ct_faststart_solve.log
LOGA=results/calibration/miso55_ct_faststart_ablation_solve.log

echo "=== miso-55 MAIN start $(date -u +%FT%TZ) ===" | tee "$LOG"
$PY scripts/probes/_miso55_ct_faststart.py main >>"$LOG" 2>&1
rc=$?
echo "=== miso-55 MAIN exit $rc $(date -u +%FT%TZ) ===" | tee -a "$LOG"
if [ $rc -ne 0 ]; then
  echo "MAIN FAILED — not starting twin" | tee -a "$LOG"
  exit $rc
fi

echo "=== miso-55 ABLATION start $(date -u +%FT%TZ) ===" | tee "$LOGA"
$PY scripts/probes/_miso55_ct_faststart.py ablation >>"$LOGA" 2>&1
rc=$?
echo "=== miso-55 ABLATION exit $rc $(date -u +%FT%TZ) ===" | tee -a "$LOGA"
exit $rc
