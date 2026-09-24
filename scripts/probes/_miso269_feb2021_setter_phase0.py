#!/usr/bin/env python3
"""miso-269 phase 0: what sets the keeper's price on Feb-2021 NON-STORM days?

ZERO LP. Rebuilds the keeper's 2021 fleet_only state (the offers the LP was
handed) and, per internal zone-hour, matches the keeper's P1 dual to the live
rows whose ``mc`` lies within ``TOL`` of it (zone-local, else pooled) — the
miso-264 census. Reports, for Feb 1-12 + Feb 20-28 2021 against the same hours
of Jan and Mar 2021 (the adjacent calm months): the MWh-weighted share of each
(class, fuel) price setter, the mean dual, the reserve price, slack/dump, and the
share of zone-hours with no match (a dual set off-stack: seam, reserve coupling,
or a binding energy/budget row).

Usage::

    uv run python scripts/probes/_miso269_feb2021_setter_phase0.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes._miso269_transport_static_phase0 import (  # noqa: E402
    INTERNAL, KEEPER, TOL, rebuild,
)

OUT = REPO / "results/calibration/_miso269_feb2021_setter_phase0.json"
YEAR = 2021


def main() -> int:
    """Run the census."""
    sysd = pd.read_parquet(KEEPER / f"hourly/system_{YEAR}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    piv = {c: sysd.pivot(index="hour", columns="zone", values=c)[list(INTERNAL)].to_numpy(float).T
           for c in ("price", "demand", "reserve_price", "slack", "dump")}
    st = rebuild(YEAR, False)
    fa, fleet = st["fleet_arrays"], st["fleet"]
    mc = np.asarray(st["mc_base"], float)
    fp = np.asarray(st["fuel_prices"], float)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    zone = np.array([str(getattr(g, "zone", "") or "") for g in fleet])
    klass = np.array([str(getattr(g, "plant_group", "") or getattr(g, "fuel_type", "")) for g in fleet])
    fuel = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])
    uid = np.asarray(fa.unit_ids, dtype=object)
    band = np.array([u.rsplit("_", 1)[-1] if "_" in u else "" for u in uid])
    fam = np.array([f"{k}|{f}|{b}" for k, f, b in zip(klass, fuel, band)])

    day = np.arange(8760) // 24
    windows = {
        "jan": (day >= 0) & (day < 31),
        "feb_nonstorm": ((day >= 31) & (day < 31 + 12)) | ((day >= 31 + 19) & (day < 59)),
        "feb_storm_13_19": (day >= 31 + 12) & (day < 31 + 19),
        "mar": (day >= 59) & (day < 90),
    }
    out = {}
    for name, hmask in windows.items():
        w: Counter = Counter()
        heat: Counter = Counter()
        fuelp: Counter = Counter()
        tot = matched = 0.0
        for zi, zz in enumerate(INTERNAL):
            p = piv["price"][zi]
            d = np.where(hmask, piv["demand"][zi], 0.0)
            tot += d.sum()
            done = np.zeros(8760, bool)
            for scope in ("local", "pooled"):
                gi = np.where(zone == zz)[0] if scope == "local" else np.arange(zone.size)
                hit = (cap[gi] > 1e-6) & (np.abs(mc[gi] - p[None, :]) <= TOL)
                hit &= ~done[None, :]
                n = hit.sum(0)
                has = (n > 0) & hmask
                share = np.where(hit, 1.0, 0.0) / np.maximum(n, 1)[None, :]
                mwh = (share * np.where(has, d, 0.0)[None, :])
                per = mwh.sum(1)
                for j in np.nonzero(per > 0)[0]:
                    g = gi[j]
                    w[fam[g]] += per[j]
                    fuelp[fam[g]] += float((mwh[j] * fp[g]).sum())
                    heat[fam[g]] += float((mwh[j] * mc[g]).sum())
                matched += float(d[has].sum())
                done |= n > 0
        top = [
            {"family": k, "share": round(v / max(matched, 1), 4),
             "mean_mc": round(heat[k] / v, 2), "mean_fuel_price": round(fuelp[k] / v, 3)}
            for k, v in w.most_common(12)
        ]
        dm = np.where(hmask[None, :], piv["demand"], 0.0)
        out[name] = {
            "lw_price": round(float((piv["price"] * dm).sum() / dm.sum()), 2),
            "lw_reserve_price": round(float((piv["reserve_price"] * dm).sum() / dm.sum()), 2),
            "slack_mwh": round(float(np.where(hmask[None, :], piv["slack"], 0).sum()), 1),
            "matched_share": round(matched / tot, 4),
            "setters": top,
        }
        print(name, {k: v for k, v in out[name].items() if k != "setters"})
        for t in top:
            print("   ", t)
    OUT.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
