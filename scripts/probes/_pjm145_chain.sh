#!/usr/bin/env bash
# pjm-145 per-year replay chain (CLAUDE.md rule 12: years sequential, one
# FRESH year per process — a PJM per-plant solve with ramp rows peaks
# ~15.6 GB on a 15 GB box; swap must be active, pjm-143 keeper note 14).
# Each link solves one new year and byte-copies the earlier years forward
# with --reuse-solved; the final link is the bundle. Copied from
# _pjm143_chain.sh with the KEEPER repointed at the current keeper
# (pjm143_hy_level_B) and an optional trailing EXTRA-args passthrough so the
# SAME script drives both pjm-145 arms:
#
#   control: _pjm145_chain.sh pjm145_control_A "<note>"
#   arm:     _pjm145_chain.sh pjm145_damavail_B "<note>" --set pjm_dam_availability=true
#
# PREREG-pjm145-dam-availability-2026-08-02.md §2. Confirm "reusing years"
# appears on link 2+ (an untracked-file dirty tree makes --reuse-solved
# refuse and every link silently re-solves its whole span — the miso-113
# lesson; commit this script before launching).
set -euo pipefail
cd "$(dirname "$0")/../.."
KEEPER=results/calibration/pjm143_hy_level_B
OUT="results/calibration/$1"
NOTE="$2"
shift 2
Y1="${OUT}_y23"; Y2="${OUT}_y24"

run() { uv run python scripts/replay_keeper.py "$KEEPER" --note "$NOTE" "$@"; }

run --out-dir "$Y1" --years 2023 "$@"
run --out-dir "$Y2" --years 2023 2024 --reuse-solved "$Y1" "$@"
run --out-dir "$OUT" --years 2023 2024 2025 --reuse-solved "$Y2" "$@"

rm -rf "$Y1" "$Y2"
echo "CHAIN DONE: $OUT"
ls "$OUT/hourly"
