#!/usr/bin/env python3
"""closeout-MISO-w2 phase 0 (ZERO LP), POST-HOC DIAGNOSTIC: where L4a's price move comes from.

Not a candidate arm. The wave-1 census (``_closeout_miso_l3l4_census.py``) is
loaded from source with two text patches and run on the nuclear-repaired
keeper: arm ``L4a_regonly`` keeps L4a's cycling-slice bid (VOM + incremental HR
x spot share x fuel) on rate-regulated plants only and gives merchant plants'
cycling slice full delivered fuel (the keeper's
``coal_committed_takeorpay_regulated`` conduct scope); ``L4a_regonly_avgHR``
also keeps the regulated slice at average HR (isolates the split construction).
Output ``results/phase0/miso/_closeout_miso_w2_l4a_scope_diag.json``.

Usage::

    .venv/bin/python scripts/probes/_closeout_miso_w2_l4a_scope_diag.py \
        --years 2019 2020 2021 2023 --scratch <dir>
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts"), str(REPO / "scripts/data")):
    if p not in sys.path:
        sys.path.insert(0, p)

SRC = REPO / "scripts/probes/_closeout_miso_l3l4_census.py"
NEW_KEEPER = REPO / "results/calibration/closeout_miso_nuc_span"
OUT = REPO / "results/phase0/miso/_closeout_miso_w2_l4a_scope_diag.json"
PATCHES = (
    (
        "    cyc_b = vom[split_rows, None] + inc_hr[:, None] * fp[split_rows]\n",
        "    cyc_b = vom[split_rows, None] + inc_hr[:, None] * fp[split_rows]\n"
        "    _reg = np.array([int(plant[i]) in reg_plants for i in split_rows])\n"
        "    cyc_reg = np.where(_reg[:, None], cyc_a, cyc_b)\n"
        "    cyc_hr = np.where(_reg[:, None], vom[split_rows, None]"
        " + (hr0[split_rows] * spot)[:, None] * fp[split_rows], cyc_b)\n",
    ),
    (
        '        "L3+L4b": lambda: with_split(l3c, cyc_b),\n    }',
        '        "L3+L4b": lambda: with_split(l3c, cyc_b),\n'
        '        "L4a_regonly": lambda: with_split(None, cyc_reg),\n'
        '        "L4a_regonly_avgHR": lambda: with_split(None, cyc_hr),\n    }',
    ),
    (
        'ARMS = ("KEEPER", "L3", "L3flag", "L3stack", "L4a", "L4b", "L3+L4a", "L3+L4b")',
        'ARMS = ("KEEPER", "L4a", "L4b", "L4a_regonly", "L4a_regonly_avgHR")',
    ),
)


def main() -> int:
    """Load the patched census, re-point it at the new keeper, run it."""
    src = SRC.read_text()
    for old, new in PATCHES:
        if old not in src:
            raise SystemExit(f"patch anchor missing in {SRC.name}: {old[:60]!r}")
        src = src.replace(old, new)
    spec = importlib.util.spec_from_loader("_l4a_scope_diag", loader=None)
    census = importlib.util.module_from_spec(spec)
    census.__file__ = str(SRC)
    exec(compile(src, str(SRC), "exec"), census.__dict__)
    from scripts.probes import _miso271_cc_decomp as dec
    from scripts.probes import _miso296_lowload_stack as m296
    from scripts.probes import _miso297_joint_census as m297

    for mod in (dec, m296, m297):
        mod.KEEPER = NEW_KEEPER
    census.KEEPER = NEW_KEEPER
    census.OUT = OUT
    return census.main()


if __name__ == "__main__":
    raise SystemExit(main())
