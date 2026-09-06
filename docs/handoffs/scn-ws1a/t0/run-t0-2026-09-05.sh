#!/bin/bash
# SCN-WS1a CAISO T0 pair (precommit FINDING §0.4): base then carbon_plus25, 2026 only, sequential.
set -u
cd /home/user/market-simulator
export MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
OUT=/tmp/claude-0/-home-user-market-simulator/b4b6b0f8-d301-514a-ab7b-706ed88e44d3/scratchpad/t0
for arm in base carbon_plus25; do
  echo "=== ARM $arm START $(date -u +%FT%TZ)"
  PYTHONPATH=. .venv/bin/python scripts/run_driver_battery.py --iso CAISO --start-year 2026 --end-year 2026 \
      --paired-arm $arm --out $OUT/$arm > $OUT/$arm.log 2>&1
  echo "=== ARM $arm EXIT $? $(date -u +%FT%TZ)"
done
echo "T0 PAIR DONE"
