"""NWPP-NEXT-3 phase 0 (ZERO LP): the plant-basis demand anchor, per year and family.

Prints, for 2019-2025, each EIA-930 fuel family's footprint energy (``NG`` net
of GRID's Southwest legs, ``OTH`` = OTH + OIL), its EIA-923 plant-basis total
(``data/raw/reference/nwpp_plant_basis_energy.csv``) and the gap the anchor
adds, then the keeper's served demand against the armed demand. The keeper
recipe carries ``nwpp_grid_carried_wind_served``. DATA PROFILE: nwpp.

Run: ``python3 scripts/probes/_nwppnext3_plant_basis_phase0.py``
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.data.eia930.demand import load_demand
from market_sim.data.eia930.envelopes import (
    _NWPP_PLANT_BASIS_EIA930_NATIVE,
    _NWPP_PLANT_BASIS_FAMILY_COLUMNS,
    _nwpp_grid_external_legs,
    _nwpp_grid_pool_carried_wind,
    _nwpp_plant_basis_energy,
)
from market_sim.data.eia930.frames import _eia_hourly_frame_filled

YEARS = range(2019, 2026)


def main() -> None:
    """Print the per-family table and the demand totals."""
    for year in YEARS:
        frame = _eia_hourly_frame_filled("NWPP", year)
        sw = _nwpp_grid_external_legs(
            year, pd.DatetimeIndex(frame["UTC time"])
        ) - _nwpp_grid_pool_carried_wind(year)
        energy = _nwpp_plant_basis_energy(year)
        print(f"\n== {year}   family   EIA-930   plant basis      gap (TWh)")
        for fam, cols in _NWPP_PLANT_BASIS_FAMILY_COLUMNS.items():
            s = sum(frame[c].fillna(0.0).to_numpy(float) for c in cols)
            if fam == "NG":
                s = s - sw
            e = energy.get(fam, 0.0)
            tag = (
                " (EIA-930-native, untouched)"
                if fam in _NWPP_PLANT_BASIS_EIA930_NATIVE
                else ""
            )
            print(
                f"   {fam:>4} {s.sum() / 1e6:10.3f} {e / 1e6:12.3f} {(e - s.sum()) / 1e6:+12.3f}{tag}"
            )
        base = load_demand("NWPP", year, nwpp_grid_carried_wind_served=True).sum(0)
        arm = load_demand(
            "NWPP",
            year,
            nwpp_grid_carried_wind_served=True,
            nwpp_demand_plant_basis=True,
        ).sum(0)
        d = arm - base
        print(
            f"   demand keeper {base.sum() / 1e6:.3f}  arm {arm.sum() / 1e6:.3f}  "
            f"delta {d.sum() / 1e6:+.3f} TWh; hourly delta min/p50/max "
            f"{d.min():.0f}/{np.median(d):.0f}/{d.max():.0f} MW; peak {base.max():.0f} -> {arm.max():.0f}"
        )


if __name__ == "__main__":
    main()
