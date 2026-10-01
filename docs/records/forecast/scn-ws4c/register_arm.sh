#!/usr/bin/env bash
# SCN-WS4c — register one arm on the FORECAST dashboard namespace.
#
# Rule 15 [R-DASHBOARD] / FF plan section 7.5: forecast-family runs go to
# frontend/data/forecast, NEVER the backcast registry, through the single
# committed path scripts/register_forecast_run.py. kind=scenario makes the
# explorer group the run with its campaign and read case / reference_case out
# of --extra-meta, exactly as SCN-WS0's scn-ws0-smoke pair is grouped.
#
# Usage: bash docs/handoffs/scn-ws4c/register_arm.sh <ISO> <CASE> [<ROOT>] [<TAG>]
set -euo pipefail
ISO="$1"; CASE="$2"; ROOT="${3:-results/scn-ws4-probe}"; TAG="${4:-t0}"
LOW="$(echo "$ISO" | tr 'A-Z' 'a-z')"
SLUG="$(echo "$CASE" | tr 'A-Z' 'a-z')"
PYTHONPATH=. .venv/bin/python scripts/register_forecast_run.py \
  --summary "${ROOT}/${LOW}/${CASE}/full_horizon_summary.json" \
  --kind scenario \
  --label "scn-ws4-probe-${TAG}-${SLUG}" \
  --extra-meta "{\"campaign\": \"scn-ws4-probe\", \"case\": \"${CASE}\", \"reference_case\": \"REF\"}"
