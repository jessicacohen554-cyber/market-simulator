"""R-ERCOT-12 zero-LP check: Frontera (55098) fleet availability under ISO_PLANT_ENTRIES.

Rebuilds the keeper recipe's LP fleet (``run_year(fleet_only=True)``, the
sanctioned ``replay_keeper.run_year_kwargs`` reconstruction) per year and
reports the 55098 rows' available MWh (pmax x availability) and first
available LP row. Usage: ``python3 scripts/probes/_r_ercot12_frontera_fleet_mask.py 2021 2023 2024``.
"""

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(p))

import probes._r_ercot3_coal_census as c3  # noqa: E402

c3.BUNDLE = REPO / "results/calibration/r_ercot11_parish_split_span"

for y in [int(a) for a in sys.argv[1:]]:
    st, lines = c3.build(y)
    fa = st["fleet_arrays"]
    pc = np.asarray(fa.plant_code, int)
    k = pc == 55098
    av = np.asarray(fa.availability, float)[k]
    pmax = np.asarray(fa.pmax, float)[k]
    mwh = float((av * pmax[:, None]).sum())
    on = np.where(av.max(axis=0) > 0)[0]
    first = int(on[0]) if on.size else -1
    print(f"{y}: 55098 rows={int(k.sum())} pmax={pmax.sum():.1f} MW avail {mwh/1e6:.3f} TWh-cap first_row={first}")
    print("   ", [ln for ln in lines if "plant entry" in ln][:2])
