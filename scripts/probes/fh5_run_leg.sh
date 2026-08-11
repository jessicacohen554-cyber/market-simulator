#!/usr/bin/env bash
# FH-5 Phase B — run one ISO's leg: solve -> score -> register, per arm.
#
# Phase B differs from Phase A (docs/handoffs/fh-4-*-leg-*.md) in exactly two
# coordinates: base year 2021 (not 2023) and window 2021-2025 (not 2023-2025).
# Per-ISO arming is Phase A's, verbatim: ERCOT armed the two capacity-screen
# flags by invocation; the other five run shipped defaults.
#
# Rule 12: years are sequential within each invocation (the runner's year loop),
# and the two arms run sequentially here. Never launch two of these at once for
# PJM and MISO.
#
# Every arm registers REGARDLESS of verdict or reads (rule 15 / the FH-4
# registration commitment). A scoring or registration failure does not abort the
# other arm — it is reported and the leg continues, so a solved arm is never
# lost to a downstream error.
#
# Usage: scripts/probes/fh5_run_leg.sh ERCOT
set -uo pipefail

ISO="${1:?usage: fh5_run_leg.sh <ISO>}"
LO="$(echo "$ISO" | tr '[:upper:]' '[:lower:]')"
LOGDIR="results/hindcast/_fh5_logs"
mkdir -p "$LOGDIR"

# ERCOT-only arming, replicated from FH-4-ERCOT §1.1 (the manager's AG.2
# determination). Empty for every other ISO — no arming beyond the two arms.
EXTRA=()
if [[ "$ISO" == "ERCOT" ]]; then
  EXTRA=(--capacity-screen-unified-lookahead --capacity-screen-scarcity-restoration)
fi

for ARM in realized asknown; do
  # CAISO Arm K is BLOCKED: the FH-2 as-of demand-growth resolver refuses CAISO
  # at vintage 2021 (the as-of-2021 CAISO IEPR cell was never intaken — charter
  # §4 row 6, "Phase B only"). Fail-closed working as designed; no value is
  # substituted (rules 5/13/25). Skipped, not worked around.
  if [[ "$ISO" == "CAISO" && "$ARM" == "asknown" ]]; then
    echo "[fh5] SKIP ${ISO} arm K — blocked on the un-intaken as-of-2021 CAISO cell"
    continue
  fi

  SHORT="armr"; [[ "$ARM" == "asknown" ]] && SHORT="armk"
  ID="${LO}-2021-2025-t1ff-${SHORT}-fh5"
  OUT="results/hindcast/${ID}"
  LOG="${LOGDIR}/${ID}.log"

  echo "[fh5] === ${ISO} ${ARM} -> ${ID} ==="
  uv run python scripts/run_capacity_hindcast.py --iso "$ISO" \
    --forward-from-base --arm "$ARM" --vintage 2020 \
    --start-year 2021 --end-year 2025 \
    "${EXTRA[@]}" \
    --out-dir "$OUT" >"$LOG" 2>&1
  RC=$?
  # The runtime key is the recorded one (the D-13 hazard: never infer the
  # ledger path from the config key).
  grep -o "cache_key=[0-9a-f]*" "$LOG" | tail -1 || true
  if [[ $RC -ne 0 ]]; then
    echo "[fh5] SOLVE FAILED rc=${RC} for ${ID} — see ${LOG}"
    tail -25 "$LOG"
    continue
  fi

  uv run python scripts/score_crossover.py --bundle "$OUT" \
    >>"$LOG" 2>&1 || echo "[fh5] SCORE FAILED for ${ID} — see ${LOG}"
  uv run python scripts/register_hindcast.py --bundle "$OUT" \
    >>"$LOG" 2>&1 || echo "[fh5] REGISTER FAILED for ${ID} — see ${LOG}"
  echo "[fh5] done ${ID}"
done

echo "[fh5] LEG COMPLETE ${ISO}"
