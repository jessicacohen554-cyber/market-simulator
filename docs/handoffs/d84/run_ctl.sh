#!/usr/bin/env bash
# capx D84 — the CONTROL leg, EARNED by the G-DRIFT audit (PRECOMMIT §6).
#
# Rule 29(b) form 4 is VOID here, and not by a "files changed" heuristic: the
# newest on-disk PJM hindcast bundle (…-d78-sectorgate) carries cache key
# bb6a60239d69508b, which is EXACTLY `HEAD − Q55 − Q58` — it predates owner
# rulings Q55 (pjm_vre_accreditation_vintage) and Q58
# (capacity_screen_peak_measured_hindcast), both LIVE hunks on PJM's forecast
# path. Two LIVE hunks, identified at the line at zero LP cost, earn a control.
#
# DECLARED KEY: f736025631d0d27e (the bare pjm-t1h at HEAD). The bundle is
# gitignored (rule 29(c) discharged by .gitignore) and is NOT deleted (rule 31).
set -euo pipefail
out="results/hindcast/pjm-2021-2025-realized-t1h-d84-control"
H0=$(git rev-parse HEAD)
echo "=== [$(date -u +%H:%M:%S)] D84 control -> ${out}  HEAD GUARD ${H0}"
python3 scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2025 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics \
    --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during control"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] control done, HEAD guard OK (${H0})"
