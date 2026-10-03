#!/usr/bin/env python3
"""closeout-MISO-w2 phase 0 (ZERO LP): re-run the wave-1 L3/L4 census on the new keeper.

The census code (``_closeout_miso_l3l4_census.py``) is unchanged; this wrapper
re-points its keeper constant (and the two modules it imports the constant
from) at ``results/calibration/closeout_miso_nuc_span`` and writes to a new
output so the wave-1 record is untouched. Bars:
``docs/records/miso/closeout-miso-w2/BARS-phase0-l3l4-retest-2026-10-03.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts"), str(REPO / "scripts/data")):
    if p not in sys.path:
        sys.path.insert(0, p)

NEW_KEEPER = REPO / "results/calibration/closeout_miso_nuc_span"
NEW_OUT = REPO / "results/phase0/miso/_closeout_miso_w2_l3l4_retest.json"


def main() -> int:
    """Patch the keeper constant everywhere the census reads it, then run it."""
    from scripts.probes import _miso271_cc_decomp as dec
    from scripts.probes import _miso296_lowload_stack as m296
    from scripts.probes import _miso297_joint_census as m297
    from scripts.probes import _closeout_miso_l3l4_census as census

    for mod in (dec, m296, m297, census):
        mod.KEEPER = NEW_KEEPER
    census.OUT = NEW_OUT
    return census.main()


if __name__ == "__main__":
    raise SystemExit(main())
