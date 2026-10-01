#!/usr/bin/env bash
# capx D81 — the rule-29 SCREEN legs on D78's own span (2021-2023: solve years
# {2021, 2023}, 2022 bridged and never scored). SCREEN YEAR = 2022, the delivery
# year in which phase 0 measures the pending owner-filed dated block largest
# (29 units / 7,855.0 MW nameplate / 7,246.3 MW accredited —
# docs/handoffs/d81/phase0_dated_block.json). PJM solo, sequential, each under a
# HEAD guard.
#
#   bash docs/handoffs/d81/run_screen.sh control   # pre-fix code
#   bash docs/handoffs/d81/run_screen.sh arm       # post-fix code
#
# The two legs differ by CODE ONLY — the fix is the seam's correct semantics, so
# no flag selects it and both legs pass the identical recipe (PRECOMMIT §3).
# cachemod.CACHE_ROOT is repointed at --out-dir by the harness, so neither leg
# can read the other's cache.
#
# Every bundle is a THROWAWAY diagnostic probe (rule 29(c)): never registered,
# never a keeper, DELETED from results/ before the PR merges. Every number the
# session cites lives in PRECOMMIT/FINDING-capx-d81-2026-09-06.md and
# docs/handoffs/d81/screen_compare.json.
set -euo pipefail

name="$1"; shift
H0=$(git rev-parse HEAD)
out="results/hindcast/pjm-2021-2023-realized-t1h-d81-${name}"
PY=${PY:-uv run python}
echo "=== [$(date -u +%H:%M:%S)] SCREEN LEG ${name} -> ${out}  HEAD GUARD ${H0}  cwd $(pwd)"
$PY scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2023 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics "$@" --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during ${name}"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] ${name} done, HEAD guard OK (${H0})"
