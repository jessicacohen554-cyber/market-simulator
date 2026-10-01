#!/usr/bin/env bash
# SCN-WS1b — register one T0 arm on the FORECAST dashboard namespace
# (rule 15 [R-DASHBOARD] / FF plan §7.5: forecast-family runs go to
# frontend/data/forecast, NEVER the backcast registry), through the single
# committed path scripts/register_forecast_run.py.
#
# kind=scenario makes the explorer read campaign / case / reference_case out of
# --extra-meta and group the run with its campaign, exactly as SCN-WS0's
# scn-ws0-smoke pair is grouped.
#
# Usage:  bash docs/handoffs/scn-ws1b/register_t0.sh <ISO> <REF|CARB>
set -euo pipefail
ISO="$1"; ARM="$2"
LOW="$(echo "$ISO" | tr 'A-Z' 'a-z')"
CASE="REF"; [ "$ARM" = "CARB" ] && CASE="CARB-MID"
PYTHONPATH=. .venv/bin/python scripts/register_forecast_run.py \
  --summary "results/scn-ws1-probe/${LOW}/${ARM}/full_horizon_summary.json" \
  --kind scenario \
  --label "scn-ws1-probe-$(echo "$ARM" | tr 'A-Z' 'a-z')" \
  --extra-meta "{\"campaign\": \"scn-ws1-probe\", \"case\": \"${CASE}\", \"reference_case\": \"REF\"}"
