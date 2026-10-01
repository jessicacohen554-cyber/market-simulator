#!/usr/bin/env bash
# capx D58 — the rule-29 SCREEN leg: same-HEAD control vs the sector-gate arm,
# screen span 2021-2023 (solve years {2021, 2023}, 2022 bridged).
#
# Both bundles are THROWAWAY diagnostic probes (rule 29(c)): never registered,
# never a keeper, deleted from results/ before the PR merges. Every number the
# session cites from them lives in PREDECL/FINDING-capx-d58-2026-09-06.md.
#
# HEAD GUARD: the charter requires HEAD to be unchanged across every solve.
set -euo pipefail

H0=$(git rev-parse HEAD)
echo "HEAD GUARD armed at $H0"

BASE=(--iso PJM --start-year 2021 --end-year 2023 --vintage 2020
      --fuel-variant realized --entry-screen-diagnostics)

run () {  # $1 = out-dir suffix, rest = extra flags
  local name="$1"; shift
  local out="results/hindcast/pjm-2021-2023-realized-t1h-d58-${name}"
  echo "=== [$(date -u +%H:%M:%S)] SCREEN LEG: ${name} -> ${out}"
  uv run python scripts/run_capacity_hindcast.py "${BASE[@]}" "$@" --out-dir "$out"
  [ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED"; exit 90; }
  echo "=== [$(date -u +%H:%M:%S)] ${name} done, HEAD guard OK"
}

# Sequential, PJM solo (rule 12): a plant-level PJM year is several GB.
run screen-control
run screen-arm --retirement-sector-gate

echo "ALL SCREEN LEGS COMPLETE at $(date -u +%H:%M:%S); HEAD still $H0"
