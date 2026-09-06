#!/usr/bin/env bash
# capx D78-R3 — the control-P leg, EARNED as a derivation base (PRECOMMIT §5.1).
#
# No committed artifact carries the control's per-DY per-class offer stack: the
# D78-R2 control-P was deleted before merge (rule 29(c)) and the D78-R2 arm was
# never registered. A deleted derivation base is rule 29(b)'s LIVE-hunk analogue
# — the capx ledger's own doctrine (ii), r#51 §0av.5: "a successor that needs
# the control's structure must budget the re-solve".
#
# WHY THIS SCRIPT AND NOT d78r2/run_full.sh: at HEAD, owner ruling Q55 (capx
# D75-R-ARM) arms pjm_vre_accreditation_vintage for PJM through
# iso_configs._pjm_config, so the BARE recipe now keys b518f5fe7d02f961 and is
# NOT the control D78-R2 graded. --no-pjm-vre-accreditation-vintage reaches the
# pre-arm posture and keeps a9c66d8ea25acb9d — the graded control's key,
# verified through the harness path before this leg ran. Full audit and the
# measured keys: ADDENDUM-2-rebase-reaudit.md §2.
#
# This lane does NOT evaluate Q55. The flag is here because the derivation base
# must be the control that produced the graded comparison, nothing more.
#
# The bundle is DELETED BEFORE MERGE (rule 29(c)); every number it yields is
# carried in zero_eas_set.json and the FINDING.
set -euo pipefail

out="results/hindcast/pjm-2021-2025-realized-t1h-d78r3-control-P"
H0=$(git rev-parse HEAD)
PY=${PY:-uv run python}
echo "=== [$(date -u +%H:%M:%S)] D78-R3 control-P -> ${out}  HEAD GUARD ${H0}"
$PY scripts/run_capacity_hindcast.py \
    --iso PJM --start-year 2021 --end-year 2025 --vintage 2020 \
    --fuel-variant realized --entry-screen-diagnostics \
    --no-pjm-vre-accreditation-vintage \
    --out-dir "$out"
[ "$(git rev-parse HEAD)" = "$H0" ] || { echo "HEAD MOVED during control-P"; exit 90; }
echo "=== [$(date -u +%H:%M:%S)] control-P done, HEAD guard OK (${H0})"
