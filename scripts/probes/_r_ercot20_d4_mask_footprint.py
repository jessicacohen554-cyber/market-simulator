"""R-ERCOT-20 D-4 design (zero LP): would a 1-5 day shutdown mask flip the residual rider rows?

Reads a keeper leg's floors npz (min_gen + mechanism) and unit_hourly (mw), the
st_netload_drag binding hours per plant (mw at a >0 drag floor), and CAMPD's
plant-total measured MW. Reports the rider's statistic (median measured MW over
binding hours) as-is, then with binding hours inside measured all-off stretches
of >= 24 h removed (the day-grain extension of the ercot-256 >= 5-day lay-up
mask), and the drag energy that removal takes out. Solves nothing.
Usage: python _r_ercot20_d4_mask_footprint.py <year> <floors.npz> <unit_hourly.parquet> [plant ...]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts/probes")
from _r_ercot20_d4_gap_census import file_cover, plant_hours  # noqa: E402

MECH = None  # resolved from the floors module id


def main(year: int, npz: str, uh: str, plants: list[int]) -> None:
    """Print the per-plant before/after rider statistic."""
    from market_sim.data.fleet.floors import MECH_ST_NETLOAD_DRAG
    z = np.load(npz, allow_pickle=True)
    ids = z["unit_ids"]
    u = pd.read_parquet(uh, columns=["unit_id", "hour", "mw"])
    u = u[u.unit_id.astype(str).isin(set(ids[np.isin(z["plant_code"], plants)]))]
    for p in plants:
        rows = np.flatnonzero((z["plant_code"] == p) & (z["plant_group"] == "ST_GAS"))
        mw = np.zeros((len(rows), 8760))
        for k, r in enumerate(rows):
            s = u[u.unit_id.astype(str) == ids[r]].sort_values("hour")
            mw[k, s.hour.to_numpy()] = s.mw.to_numpy()
        mg = z["min_gen"][rows].astype(float)
        drag = (z["mechanism"][rows] == MECH_ST_NETLOAD_DRAG) & (mg > 0.5) & (mw <= mg + 1e-3)
        bind = drag.any(axis=0)
        meas, _ = plant_hours(p, year)
        off = meas <= 0
        lens = np.zeros(8760)
        i = 0
        while i < 8760:
            if off[i]:
                j = i
                while j < 8760 and off[j]:
                    j += 1
                lens[i:j] = j - i
                i = j
            else:
                i += 1
        keep = bind & ~(off & (lens >= 24))
        e_all = float((mw * drag).sum()) / 1e6
        e_rm = float((mw * drag)[:, ~keep].sum()) / 1e6
        fk = bind & ~file_cover(p, year, ("campd-unit-outages-layup.csv", "campd-unit-outages.csv",
                                           "campd-unit-outages-layup-shortgas.csv", "campd-unit-outages-shortgas.csv"))
        print(f"   file-based short lay-up mask: binding {fk.sum()} h, median {np.median(meas[fk]):.1f} MW, "
              f"zero {off[fk].mean():.2f}, removed TWh {float((mw * drag)[:, ~fk].sum()) / 1e6:.3f}")
        print(f"{p} {year}: binding {bind.sum()} h, median {np.median(meas[bind]):.1f} MW, zero {off[bind].mean():.2f} | "
              f"mask>=24h: binding {keep.sum()} h, median {np.median(meas[keep]):.1f} MW, zero {off[keep].mean():.2f}, "
              f"floored TWh {e_all:.3f} -> removed {e_rm:.3f}; residual zero-hours in <24h stretches {int((keep & off).sum())}")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2], sys.argv[3], [int(a) for a in sys.argv[4:]] or [3491, 3452, 3628])
