"""R-ERCOT-11 phase 0 (zero LP): per-unit fleet census for the W A Parish split fix.

Rebuilds the keeper recipe's LP fleet (``run_year(fleet_only=True)``, bundle
``r_ercot10_parish_span``) for each year and writes one row per LP unit:
plant code, group, pmax, mean availability, available energy (TWh), must-run
floor energy and mean marginal cost. Run once on the committed bin sheet and
once on the corrected sheet, then diff: only the Parish rows (3470 / 34702)
may move.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python \
        scripts/probes/_r_ercot11_parish_split_census.py --years 2019 2025 --out <csv>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts/probes"):
    sys.path.insert(0, str(p))

import _r_ercot3_coal_census as c3  # noqa: E402

c3.BUNDLE = REPO / "results/calibration/r_ercot10_parish_span"


def census(year: int) -> pd.DataFrame:
    """One row per LP unit for ``year`` on the keeper recipe."""
    st, _ = c3.build(year)
    fa = st["fleet_arrays"]
    n = len(fa.pmax)
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    av = av if av.ndim == 2 else np.repeat(av[:, None], 8760, axis=1)
    mg = c3._arr(fa, "min_gen", n)
    mg = np.zeros(n) if mg is None else np.asarray(mg, float)
    mg_e = (mg.sum(axis=1) if mg.ndim == 2 else mg * 8760) / 1e6
    mc = np.asarray(st["mc_base"], float)
    mc_m = mc.mean(axis=1) if mc.ndim == 2 else mc
    return pd.DataFrame(
        {
            "year": year,
            "i": np.arange(n),
            "plant_code": c3._arr(fa, "plant_code", n),
            "group": [str(g) for g in fa.plant_group],
            "pmax": pmax,
            "avail_mean": av.mean(axis=1),
            "avail_twh": (pmax[:, None] * av).sum(axis=1) / 1e6,
            "mustrun_twh": mg_e,
            "mc_mean": mc_m,
        }
    )


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs=2, default=[2019, 2025])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    frames = [census(y) for y in range(a.years[0], a.years[1] + 1)]
    pd.concat(frames).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
