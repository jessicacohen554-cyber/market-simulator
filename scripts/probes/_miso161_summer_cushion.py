"""miso-161 — RE-RUN of the miso-153 summer-cushion phase-0 instrument on the
NEW keeper ``2026-08-16-miso-160-wefor-shape`` (bundle ``miso160_wefor_B``).

NO SOLVE. NO NEW INSTRUMENT. Executes ``_miso153_summer_cushion.py``
(pre-registered at ``PREREG-miso153-summer-peak-phase0-2026-08-12.md``, pushed
``857a434``) with only the T-1 repoints a keeper change prescribes: the bundle
globals (probe + ``_miso134`` helper) and the output path. The keeper config
rebuilt from ``miso160_wefor_B/run_config.json`` carries
``summer_wefor_share_override = 1.0599``, so D-1's availability and D-3's
within-$20 idle band are measured on the ARMED seasonal outage shape.

The charter's target statistic (miso-161 handoff, charter item a): the
remaining CT_PEAKER ``idle_mw_within_20_above_price_by_class`` at the 2025
top-200 hours — 6.308 GW on the pre-miso-160 keeper
(``_miso153_summer_cushion.json`` D-3), ~2.6 GW expected to remain after the
measured shape removed ~3.7 GW of Jun-Sep capability.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds neither marker.

Usage::

    PYTHONPATH=$PWD:$PWD/src .venv/bin/python \\
        scripts/probes/_miso161_summer_cushion.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso153_summer_cushion as _m153  # noqa: E402

# T-1: repoint BOTH module globals to THIS session's keeper, then assert.
BUNDLE = REPO / "results/calibration/miso160_wefor_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE
_m153.BUNDLE = BUNDLE
assert _m134.BUNDLE == BUNDLE and _m153.BUNDLE == BUNDLE, "T-1: repoint failed"

_m153.OUT = REPO / "results/calibration/_miso161_summer_cushion.json"

if __name__ == "__main__":
    _m153.main()
