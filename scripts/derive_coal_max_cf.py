#!/usr/bin/env python3
"""Derive ERCOT per-plant coal sustained-output ceilings from CAMPD physics.

Re-derivation of ``constants.COAL_MAX_CF_BY_PLANT`` (2026-07 legitimacy scrub,
audit item C-2): the ceiling must reflect each plant's *demonstrated* physical
capability (boiler/turbine/derate limits visible in its own CEMS record), not
a value hand-picked to keep the model from over-running its observed output.

Methodology (mirrors the "ref" ceiling in ``scripts/derive_partial_outages.py``,
so the two mechanisms share one convention for "this plant's normal ceiling"):
for each plant, over every CAMPD hourly gross-output year on record, compute
the daily-max capacity factor (``gross_mw / capacity_mw``, the same nameplate
basis the model's own availability array uses) on days the plant actually ran
(daily-mean CF > :data:`RUN_FLOOR_CF`, filtering off-line days rather than
economic part-load days). The pooled 99th percentile of that daily-max series
across all available years is the plant's demonstrated sustained ceiling — a
near-maximum, robust to a single-hour telemetry spike, but not softened by
economic part-loading (which mostly compresses the mean/median, not the top
tail). A plant whose ceiling reaches or exceeds nameplate (rounded value >=
1.0) gets no entry: CAMPD data show no evidence of a sub-nameplate physical
limit, so the generic age-based availability model governs unconstrained.

Run: ``python scripts/derive_coal_max_cf.py`` (writes nothing; prints the
values to hand-copy into constants.py after review, matching the frozen-derive-
script convention of rule #22 — re-derivation is a reviewed, cited commit, not
an automatic write).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_campd_bins  # noqa: E402

# Coal plants the ceiling applies to (ERCOT CAMPD per-plant binning). Matches
# constants.COAL_MAX_CF_BY_PLANT's plant set.
_PLANTS: dict[int, str] = {
    6180: "Oak Grove",
    298: "Limestone",
    6178: "Coleto Creek",
    6183: "San Miguel",
    6179: "Fayette (Sam Seymour)",
    7097: "J K Spruce",
}

# Daily-mean CF above which a day counts as "running" (matches
# derive_partial_outages._RUN_FLOOR_CF): excludes full-outage/off-line days
# from the ceiling sample without excluding genuine low-CF economic days.
RUN_FLOOR_CF: float = 0.06
# Percentile of the pooled daily-max CF used as the demonstrated ceiling.
CEILING_PERCENTILE: float = 99.0
# Years of CAMPD hourly extract on record for ERCOT (TX).
YEARS: tuple[int, ...] = (2023, 2024, 2025)


def derive() -> dict[int, float]:
    """Return ``{plant_code: ceiling}`` for plants with a sub-1.0 finding."""
    bins = load_campd_bins("data/raw/reference/custom-bin-assignments.csv")
    cap = dict(zip(bins["Plant_Code"].astype(int), bins["capacity_mw"]))
    df = campd.load_campd_hourly(campd.states_for_iso("ERCOT"), list(YEARS))

    out: dict[int, float] = {}
    for code, name in _PLANTS.items():
        pooled: list[np.ndarray] = []
        for year in YEARS:
            grid = campd.plant_hourly_grid(df, code, year)
            if grid.empty:
                continue
            full = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
            cf = (grid["gross_mw"].reindex(full).fillna(0.0) / cap[code]).to_numpy(
                dtype=float
            )
            n_days = cf.shape[0] // 24
            day = cf[: n_days * 24].reshape(n_days, 24)
            dmax, dmean = day.max(1), day.mean(1)
            running = dmean > RUN_FLOOR_CF
            pooled.append(dmax[running])
        if not pooled:
            print(f"{code:>5} {name:<22} no CAMPD data")
            continue
        ceiling = float(np.percentile(np.concatenate(pooled), CEILING_PERCENTILE))
        rounded = round(min(1.0, ceiling), 2)
        note = "no ceiling (>= nameplate)" if rounded >= 1.0 else f"ceiling={rounded}"
        print(f"{code:>5} {name:<22} p{CEILING_PERCENTILE:.0f}={ceiling:.4f}  {note}")
        if rounded < 1.0:
            out[code] = rounded
    return out


if __name__ == "__main__":
    result = derive()
    print("\nCOAL_MAX_CF_BY_PLANT =", result)
