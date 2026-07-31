#!/usr/bin/env bash
# miso-111 per-year replay chain (CLAUDE.md rule 12: years sequential, one
# FRESH year per process — a single-process 3-year MISO per-plant solve peaks
# ~15.9 GB and OOMs a 15 GB box). Each link solves one new year and byte-copies
# the earlier years forward with --reuse-solved; the final link is the bundle.
#
# Usage: _miso111_chain.sh <final-bundle-name> <note> [--set KEY=JSON ...]
set -euo pipefail
cd "$(dirname "$0")/../.."
KEEPER=results/calibration/miso109_hy_level_B
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
