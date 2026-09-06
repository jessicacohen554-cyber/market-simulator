#!/usr/bin/env bash
# SCN-WS4c — one arm of the LOAD-HI battery (PRECOMMIT §1).
#
# Rule 12 [R-PARALLEL]: years are ALWAYS sequential inside an invocation (the
# runner's own year loop); concurrency is between invocations only, and the
# caller is responsible for the <=2 / <=1 cap. Each arm gets its OWN out-dir so
# its full_horizon_summary.json survives for registration; the per-case caches
# are merged into one tree afterwards for report_scenario_deltas.py.
#
# Usage: bash docs/handoffs/scn-ws4c/launch_arm.sh <ISO> <CASE> <START> <END> <CAMPAIGN_DIR>
set -uo pipefail
ISO="$1"; CASE="$2"; START="$3"; END="$4"; ROOT="${5:-results/scn-ws4-probe}"
LOW="$(echo "$ISO" | tr 'A-Z' 'a-z')"
OUT="${ROOT}/${LOW}/${CASE}"
mkdir -p "$OUT"

# The case -> --set mapping IS configs/scenario_campaign_matrix.yaml (SCN-WS4b's
# landed keys, consumed not edited). REF overrides nothing (plan section 3.0).
declare -a SETS=()
case "$CASE" in
  REF)             SETS=() ;;
  LOAD-HI)         SETS=(--set demand_growth_path=high --set datacenter_load_path=high) ;;
  LOAD-HI-ORGANIC) SETS=(--set demand_growth_path=high --set datacenter_load_path=mid) ;;
  *) echo "unknown case $CASE" >&2; exit 2 ;;
esac

echo "[$(date -u +%H:%M:%S)] START $ISO $CASE $START-$END"
/usr/bin/time -v env PYTHONPATH=. .venv/bin/python scripts/run_full_horizon.py \
  --iso "$ISO" --start-year "$START" --end-year "$END" \
  --out-dir "$OUT" "${SETS[@]}" > "$OUT/../${CASE}.log" 2>&1
RC=$?
echo "[$(date -u +%H:%M:%S)] DONE  $ISO $CASE rc=$RC"
exit $RC
