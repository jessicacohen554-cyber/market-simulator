#!/usr/bin/env python3
"""miso-293 Stage 1 (ZERO LP): can ANY reduced network move the scored C3a 2022 object?

C3a for MISO compares the model's zone-demand-weighted P1 price with INDIANA.HUB RT,
time-weighted by measured system demand (``rt_lw``, miso-292). A network adds
congestion and losses to the model's ZONAL prices; the scored model number is their
demand-weighted MEAN across zones. So the most any network can add to the scored
model price is the demand-weighted mean of the zones' congestion + loss components,
not Indiana's.

This probe measures, from MISO's published hub components (rule 13: answer class,
used here only as an upper bound and to localize, never to set a number):

1. ``indiana_wedge``: INDIANA.HUB MCC+MLC, demand-time-weighted (what the comparator
   carries above the system energy price).
2. ``zone_ceiling``: model-zone-demand-weighted hub MCC+MLC (MINN->West, ILLINOIS->
   Illinois, INDIANA->Indiana, MICHIGAN->East, ARKANSAS/LOUISIANA/MS/TEXAS mean ->South,
   MINN/ILLINOIS mean->Plains, the staging's own Plains proxy). This is what a
   perfect zone-level network would add to the scored model price.
3. The C3a 2022 reading if the model gained exactly ``zone_ceiling`` (additive).
4. Rank of the hourly hub-MCC matrix (share of squared norm in the first singular
   vector, and its loadings): if one direction dominates, a small flowgate family on
   zone injections could carry the hub-to-hub spreads, whatever LBA the monitored
   element sits in.

Usage::

    uv run python scripts/probes/_miso293_flowgate_ceiling.py --out results/phase0/miso/_miso293_flowgate_ceiling.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso277_c3a2022_congestion as m277  # noqa: E402

KEEPER = REPO / "results/calibration/miso280_span"
REF = REPO / "data/raw/_validation-source/actual_lmp.json"
YEARS = (2022, 2023, 2024, 2025)
SOUTH_HUBS = ("ARKANSAS.HUB", "LOUISIANA.HUB", "MS.HUB", "TEXAS.HUB")
ZONE_HUBS = {
    "MISO-West": ("MINN.HUB",),
    "MISO-Plains": ("MINN.HUB", "ILLINOIS.HUB"),
    "MISO-Illinois": ("ILLINOIS.HUB",),
    "MISO-Indiana": ("INDIANA.HUB",),
    "MISO-East": ("MICHIGAN.HUB",),
    "MISO-South": SOUTH_HUBS,
}
HUBS = ("MINN.HUB", "ILLINOIS.HUB", "INDIANA.HUB", "MICHIGAN.HUB") + SOUTH_HUBS


def components(year: int) -> dict[str, dict[str, np.ndarray]]:
    """Hub RT MCC/MLC arrays (8760,) for every hub, on the scorer's hour key."""
    saved = dict(m277.HUB_ZONE)
    m277.HUB_ZONE.clear()
    m277.HUB_ZONE.update({h: h for h in HUBS})
    try:
        return m277.hub_components(year)
    finally:
        m277.HUB_ZONE.clear()
        m277.HUB_ZONE.update(saved)


def wmean(x: np.ndarray, w: np.ndarray) -> float:
    """NaN-safe weighted mean."""
    ok = np.isfinite(x) & np.isfinite(w)
    return float((x[ok] * w[ok]).sum() / w[ok].sum())


def run(year: int, ref: dict) -> dict:
    """All measures for one year."""
    comp = components(year)
    sysdf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    sysdf = sysdf[(sysdf["pass"] == "P1") & sysdf["zone"].isin(ZONE_HUBS)]
    dem = sysdf.pivot(index="hour", columns="zone", values="demand").reindex(
        range(8760)
    )
    prc = sysdf.pivot(index="hour", columns="zone", values="price").reindex(range(8760))
    cm = comp["MCC"]
    cl = comp["MLC"]
    hub_cl = {h: cm[h] + cl[h] for h in HUBS}
    zone_cl = {
        z: np.nanmean(np.vstack([hub_cl[h] for h in hs]), axis=0)
        for z, hs in ZONE_HUBS.items()
    }
    zone_mcc = {
        z: np.nanmean(np.vstack([cm[h] for h in hs]), axis=0)
        for z, hs in ZONE_HUBS.items()
    }
    D = dem[list(ZONE_HUBS)].to_numpy(float)
    tot = D.sum(axis=1)
    mask = np.isfinite(cm["INDIANA.HUB"])
    if year == 2022:
        mask &= np.arange(8760) < m277.JAN_OCT_HOURS
    zc_h = (np.column_stack([zone_cl[z] for z in ZONE_HUBS]) * D).sum(axis=1) / tot
    zm_h = (np.column_stack([zone_mcc[z] for z in ZONE_HUBS]) * D).sum(axis=1) / tot
    model_h = (prc[list(ZONE_HUBS)].to_numpy(float) * D).sum(axis=1) / tot
    w = np.where(mask, tot, np.nan)
    out = {
        "hours": int(mask.sum()),
        "indiana_wedge_mcc_mlc": round(wmean(hub_cl["INDIANA.HUB"], w), 2),
        "indiana_mcc": round(wmean(cm["INDIANA.HUB"], w), 2),
        "zone_ceiling_mcc_mlc": round(wmean(zc_h, w), 2),
        "zone_ceiling_mcc": round(wmean(zm_h, w), 2),
        "hub_mcc_mlc_lw": {h: round(wmean(hub_cl[h], w), 2) for h in HUBS},
        "model_scored_price_lw": round(wmean(model_h, w), 2),
    }
    # Scored actual: Jan-Oct hour-weighted mean of rt_lw_mon for 2022, else rt_lw.
    r = ref["MISO"][str(year)]
    out["actual_rt_lw"] = r.get("rt_lw")
    # Rank of the hourly hub-MCC matrix (masked hours, hubs as columns).
    M = np.column_stack([cm[h] for h in HUBS])[mask]
    M = M[np.isfinite(M).all(axis=1)]
    _, s, vt = np.linalg.svd(M, full_matrices=False)
    share = s**2 / (s**2).sum()
    v1 = vt[0] * np.sign(vt[0][HUBS.index("INDIANA.HUB")] or 1)
    out["mcc_rank1_share"] = round(float(share[0]), 3)
    out["mcc_rank2_cum"] = round(float(share[:2].sum()), 3)
    out["mcc_v1_loadings"] = {h: round(float(x), 3) for h, x in zip(HUBS, v1)}
    # Hub-to-hub spreads the model's zone set could express (MCC only).
    out["spread_indiana_minus_minn_mcc"] = round(
        wmean(cm["INDIANA.HUB"] - cm["MINN.HUB"], w), 2
    )
    out["spread_indiana_minus_illinois_mcc"] = round(
        wmean(cm["INDIANA.HUB"] - cm["ILLINOIS.HUB"], w), 2
    )
    return out


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    ref = json.loads(REF.read_text())
    res = {str(y): run(y, ref) for y in YEARS}
    a.out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
