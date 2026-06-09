#!/bin/bash
# Usage: run_seq.sh <curve.json> <tag> <note>
set -e
cd /home/user/market-simulator
CURVE="$1"; TAG="$2"; NOTE="$3"
for Y in 2023 2024; do
  echo "=== launching $TAG $Y ==="
  python3 scripts/run_calibration_full.py --iso PJM --year $Y \
    --offer-curve-json "$CURVE" \
    --out-dir results/calibration/pjm_${TAG}_${Y} \
    --note "$NOTE" \
    > results/calibration/pjm_logs/${TAG}_${Y}.log 2>&1
  echo "=== $TAG $Y done ==="
done
echo "ALL DONE $TAG"
