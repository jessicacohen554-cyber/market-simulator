#!/usr/bin/env bash
# caiso-172 A/B driver — the MEASURED Path-15 split of PG&E TAC load.
#
# Both arms replay the SAME keeper recipe (caiso166_measured_loss_zones) through
# the sanctioned scripts/replay_keeper.py channel, at the SAME commit, with the
# SAME years (2023 2024 2025 in one invocation, rule 16 [R-ALLYEARS]). The ONLY
# difference between them is CAISO_TAC_ZONE_WEIGHTS['PGE-TAC'] (and the paired
# static load_share fallback in iso_configs.py, which must move with it):
#
#   Arm A (control)   NP15 0.86     / ZP26 0.14      -- the incumbent estimate
#   Arm B (candidate) NP15 0.883951 / ZP26 0.116049  -- the caiso-172 measurement
#
# Run SEQUENTIALLY, not concurrently: a single CAISO plant-level multi-zone LP
# already uses several GB, and this container has 15 GB / 4 cores (rule 12's
# OOM caution). The control is solved fresh on this head rather than reusing the
# keeper's committed bundle, so no incidental code drift contaminates the delta.
#
# Usage: bash scripts/probes/_caiso172_ab_driver.sh
set -uo pipefail
cd "$(dirname "$0")/../.."
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH=.:src

KEEPER=results/calibration/caiso166_measured_loss_zones
CTRL=results/calibration/caiso172_control_pge_estimate
ARM=results/calibration/caiso172_measured_path15_split
STASH=/tmp/claude-0/-home-user-market-simulator/a88381f9-25b1-514f-b060-524b8e265951/scratchpad/caiso172_files
C=src/market_sim/config/constants.py
I=src/market_sim/config/iso_configs.py

mkdir -p "$STASH"
# keep the MEASURED (arm B) versions safe, so the control edit is always undone
cp "$C" "$STASH/constants.measured.py"
cp "$I" "$STASH/iso_configs.measured.py"
restore_measured() { cp "$STASH/constants.measured.py" "$C"; cp "$STASH/iso_configs.measured.py" "$I"; }
trap restore_measured EXIT

echo "=== ARM A (control): reverting to the 0.86/0.14 estimate ==="
python - <<'PY'
import pathlib
c = pathlib.Path("src/market_sim/config/constants.py")
t = c.read_text()
new = '    "PGE-TAC": {"NP15": 0.883951, "ZP26": 0.116049},'
old = '    "PGE-TAC": {"NP15": 0.86, "ZP26": 0.14},'
assert new in t, "measured PGE-TAC line not found"
c.write_text(t.replace(new, old))
i = pathlib.Path("src/market_sim/config/iso_configs.py")
t = i.read_text()
for a, b in (('load_share=0.4079', 'load_share=0.3969'), ('load_share=0.0536', 'load_share=0.0646')):
    assert a in t, f"{a} not found"
    t = t.replace(a, b)
i.write_text(t)
print("control weights pinned: NP15 0.86 / ZP26 0.14")
PY
python -c "
from market_sim.config.constants import CAISO_TAC_ZONE_WEIGHTS as W
assert W['PGE-TAC'] == {'NP15': 0.86, 'ZP26': 0.14}, W['PGE-TAC']
print('verified control constant:', W['PGE-TAC'])"

python scripts/replay_keeper.py "$KEEPER" --out-dir "$CTRL" \
  --note "caiso-172 Arm A CONTROL: same-head fresh solve of the caiso-166 keeper recipe with the INCUMBENT residual-identified CAISO_TAC_ZONE_WEIGHTS['PGE-TAC'] = {NP15 0.86, ZP26 0.14}. Zero-delta against the keeper except the solve being fresh on this head; it is the baseline the measured Path-15 split (Arm B) is differenced against." \
  2>&1 | tail -30
echo "ARM A exit=$?"

echo "=== restoring the MEASURED weights for ARM B ==="
restore_measured
python -c "
from market_sim.config.constants import CAISO_TAC_ZONE_WEIGHTS as W
assert W['PGE-TAC'] == {'NP15': 0.883951, 'ZP26': 0.116049}, W['PGE-TAC']
print('verified arm constant:', W['PGE-TAC'])"

echo "=== ARM B (candidate): the measured Path-15 split ==="
python scripts/replay_keeper.py "$KEEPER" --out-dir "$ARM" \
  --note "caiso-172 Arm B CANDIDATE: the MEASURED Path-15 split of PG&E TAC load, CAISO_TAC_ZONE_WEIGHTS['PGE-TAC'] = {NP15 0.883951, ZP26 0.116049}, derived by scripts/data/derive_caiso_path15_load_split.py from OASIS ATL_LDF x ATL_PNODE_MAP (rule 14 [R-ACCURATE] measured-over-estimate; rule 23 frozen derive). Zero free parameters, zero ScenarioConfig fields changed; the only delta from Arm A is the weight pair and its paired static load_share fallback." \
  2>&1 | tail -30
echo "ARM B exit=$?"
echo "=== A/B COMPLETE ==="
