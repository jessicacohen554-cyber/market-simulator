"""R-CAISO-2 phase 0 (ZERO LP): per-plant CC_REGULAR offer census on the keeper.

Rebuilds the keeper bundle's fleet for one year (``reconstruct_bundle_fleet``,
fleet-only, no solve) and reports, per CC_REGULAR plant, its tranche MW,
availability-weighted capacity, heat rate, hourly marginal cost and the share
of hours its cheapest tranche sits below its zone's committed P1 price. Read
alongside the committed payload's per-plant model/actual MWh.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

BUNDLE = REPO / "results/calibration/rcaiso_inputs_span"


def main(year: int, out: Path) -> None:
    """Write the per-plant CC census for ``year`` to ``out`` (JSON)."""
    state, meta = reconstruct_bundle_fleet(
        BUNDLE, year, required_flags=(), required_sequences=()
    )
    fa, fleet = state["fleet_arrays"], state["fleet"]
    mc = np.asarray(state["mc_base"], float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], 8760, axis=1)
    avail = np.asarray(fa.availability, float)
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], 8760, axis=1)
    pmax = np.asarray(fa.pmax, float)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    pcode = np.array([str(getattr(g, "plant_code", getattr(g, "plant_id", "")) or "") for g in fleet])
    zone = np.array([str(z) for z in fa.zone_names[fa.zone_idx]]) if hasattr(fa, "zone_names") else np.array([str(getattr(g, "zone", "")) for g in fleet])
    hr = np.asarray(getattr(fa, "heat_rate", np.full(len(fleet), np.nan)), float)
    sysdf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    pr = sysdf[sysdf["pass"] == "P1"].pivot(index="hour", columns="zone", values="price")
    rows = []
    for p in sorted(set(pcode[klass == "CC_REGULAR"])):
        ix = np.where((pcode == p) & (klass == "CC_REGULAR"))[0]
        z = zone[ix[0]]
        price = pr[z].to_numpy() if z in pr else np.full(8760, np.nan)
        units = []
        for i in ix:
            units.append({
                "unit": str(fa.unit_ids[i]), "pmax": round(float(pmax[i]), 1),
                "avail_mean": round(float(avail[i].mean()), 3),
                "hr": round(float(hr[i]), 3),
                "mc_mean": round(float(mc[i].mean()), 2),
                "in_money_share": round(float((mc[i] < price).mean()), 3),
            })
        rows.append({
            "plant": p, "zone": z, "mw": round(float(pmax[ix].sum()), 1),
            "avail_mwh_twh": round(float((pmax[ix, None] * avail[ix]).sum() / 1e6), 3),
            "zone_price_mean": round(float(np.nanmean(price)), 2), "units": units,
        })
    out.write_text(json.dumps({"year": year, "plants": rows}, indent=1))
    print(f"wrote {out} ({len(rows)} plants)")


if __name__ == "__main__":
    y = int(sys.argv[1])
    main(y, Path(sys.argv[2]))
