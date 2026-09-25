"""soco-68 basis census (ZERO LP): is SOCO's CC/CT pmax already the net-summer rating?

The miso-141 measurement, on SOCO's own fleet and CEMS. For each solve year:

1. **Capacity basis.** Per CC_REGULAR / CT_PEAKER plant, the keeper fleet's
   summed pmax against the solve-year EIA-860 vintage's summed net-summer and
   nameplate over the plant's matching prime movers (CC: CT/CA/CS; CT: GT).
   Reports the capacity share carried on the net-summer basis (|pmax/summer-1|
   <= 0.5 %), the share the always-on CC guard clipped, and the class's
   nameplate->net-summer gap -- the loss the flat ``SUMMER_CLASS_DERATE``
   (CC 10 %, CT 12.5 %) re-applies.
2. **Measured summer capability.** For single-class plants (every fleet unit of
   the plant is the class), the Jun-Sep hours in which CEMS net (gross x 0.97)
   EXCEEDS the control's pre-outage summer ceiling ``pmax x (1 - flat)`` --
   hours the model forbids output the plant measurably produced.

Reads ``fleet_<y>_ctl.npz`` from ``_soco68_cc_capability.py``.

    .venv/bin/python scripts/probes/_soco68_basis_census.py --cap-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "scripts/probes")]
from _soco68_cc_capability import T  # noqa: E402

FLAT = {"CC_REGULAR": 0.10, "CT_PEAKER": 0.125}  # fuel_trajectories.SUMMER_CLASS_DERATE
PM = {"CC_REGULAR": ("CT", "CA", "CS"), "CT_PEAKER": ("GT",)}
UTYPE = {"CC_REGULAR": "combined cycle", "CT_PEAKER": "combustion turbine"}
STATES = ("AL", "GA", "MS", "FL")


def cems_plant(year: int, plants: set[int], utype: str) -> dict[int, np.ndarray]:
    """Hourly net MW per facility over units whose unitType contains ``utype``."""
    out: dict[int, np.ndarray] = {}
    for st in STATES:
        p = REPO / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(
            p, columns=["facilityId", "date", "hour", "grossLoad", "unitType"]
        )
        f = pd.to_numeric(d.facilityId, errors="coerce")
        d = d[f.isin(plants) & d.unitType.astype(str).str.lower().str.contains(utype)]
        if d.empty:
            continue
        dt = pd.to_datetime(d["date"])
        keep = ~((dt.dt.month == 2) & (dt.dt.day == 29))
        d, dt = d[keep], dt[keep]
        doy = (dt - pd.Timestamp(year=year, month=1, day=1)).dt.days
        if year % 4 == 0:
            doy = doy - (dt.dt.month > 2).astype(int)
        h = (doy * 24 + d["hour"].astype(int)).to_numpy()
        fac = pd.to_numeric(d.facilityId).to_numpy().astype(int)
        g = np.nan_to_num(d["grossLoad"].to_numpy(dtype=float)) * 0.97
        for code in np.unique(fac):
            m = (fac == code) & (h >= 0) & (h < T)
            arr = out.setdefault(int(code), np.zeros(T))
            np.add.at(arr, h[m], g[m])
    return out


def main() -> None:
    """Print the per-year basis census for CC_REGULAR and CT_PEAKER."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cap-dir", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    a = ap.parse_args()
    summer = np.zeros(T, bool)
    summer[151 * 24 : 273 * 24] = True  # Jun 1 .. Sep 30 (non-leap day index)
    for y in a.years:
        f = np.load(a.cap_dir / f"fleet_{y}_ctl.npz")
        cls, plant, pmax = f["cls"], f["plant"], f["pmax"]
        vdir = REPO / f"data/raw/eia-860/vintage_{y}/eia860_generator_operable.parquet"
        if not vdir.exists():
            vdir = REPO / "data/raw/eia-860/eia860_generator_operable.parquet"
        g = pd.read_parquet(vdir)
        g["code"] = pd.to_numeric(g["Plant Code"], errors="coerce")
        for c in ("Nameplate Capacity (MW)", "Summer Capacity (MW)"):
            g[c] = pd.to_numeric(g[c], errors="coerce")
        for k in ("CC_REGULAR", "CT_PEAKER"):
            ii = np.where(cls == k)[0]
            pm = pd.Series(pmax[ii]).groupby(plant[ii]).sum()
            e = (
                g[g["Prime Mover"].isin(PM[k]) & g.code.isin(pm.index)]
                .groupby("code")[["Nameplate Capacity (MW)", "Summer Capacity (MW)"]]
                .sum()
            )
            e = e.reindex(pm.index)
            summ_basis = (pm / e["Summer Capacity (MW)"] - 1).abs() <= 0.005
            np_basis = (
                (pm / e["Nameplate Capacity (MW)"] - 1).abs() <= 0.005
            ) & ~summ_basis
            gap = (
                1 - e["Summer Capacity (MW)"].sum() / e["Nameplate Capacity (MW)"].sum()
            )
            single = [p for p in pm.index if (cls[plant == p] == k).all()]
            cem = cems_plant(y, set(single), UTYPE[k])
            hrs, mwh, n = 0, 0.0, 0
            for p in single:
                cap = pm[p] * (1 - FLAT[k])
                c = cem.get(p)
                if c is None:
                    continue
                n += 1
                over = summer & (c > cap)
                hrs += int(over.sum())
                mwh += float((c[over] - cap).sum())
            print(
                f"{y} {k:10s} pmax {pm.sum():8.0f} MW | on net-summer basis {pm[summ_basis].sum() / pm.sum():6.1%}"
                f" | on nameplate basis {pm[np_basis].sum() / pm.sum():6.1%} | 860 nameplate->summer gap {gap:6.2%}"
                f" | flat {FLAT[k]:.1%} | single-class plants w/ CEMS {n}: summer plant-hours above pmax*(1-flat) {hrs},"
                f" {mwh / 1e6:.3f} TWh"
            )


if __name__ == "__main__":
    main()
