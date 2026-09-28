#!/usr/bin/env python3
"""miso-282 phase 0 (ZERO LP): per-unit ST_GAS offers, fuel and model price for the in-merit 2x2.

A copy of ``_miso281_south_steam_2019.py`` that also saves each ST_GAS unit's
hourly delivered fuel price (so a measured heat rate can be priced on the
model's own gas path) and a per-(group, zone) offer summary for the relative
merit order. Original docstring follows.

miso-281 phase 0 (ZERO LP): why do MISO-South gas-steam plants dispatch below actual in 2019?

Fleet-only rebuild of the designated keeper's recipe (``results/calibration/
miso280_span``, 2019) joined, per LP unit, to the keeper's own committed
2019 hourly zone prices (``hourly/system_2019.parquet``). Per ST_GAS unit it
records plant, zone, pmax, available MWh, floor MWh and the assembled P0 offer
(``mc_base``: fuel + VOM + every pricing overlay) and computes the
price-taker envelope

    E_attain = sum_t max(floor[t], pmax*avail[t] * 1[price_z[t] >= mc[t]])

i.e. what a unit would produce if it ran whenever the model's own clearing
price covered its P0 offer. The per-hour offer and floor arrays are saved so
a later join can place the gap by hour and band.

Rule 13: nothing here is fed back into a solve; it localizes a residual.
Rule 23: artifacts are read, never re-derived.

Usage::

    uv run python scripts/probes/_miso281_south_steam_2019.py --out-dir X
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

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402

KEEPER = REPO / "results/calibration/miso280_span"
YEAR = 2019
GROUPS = ("ST_GAS", "CC_REGULAR", "CT_PEAKER", "ST_CHP", "CC_CHP")


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--year", type=int, default=YEAR)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    y = args.year
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    hh = _henry_hub_actual(_load_reference(), y)
    st = run_year(y, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(y, {}))
    fa, isoc = st["fleet_arrays"], st["iso_config"]
    n = len(fa.pmax)
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], 8760, axis=1)
    cap = pmax[:, None] * avail
    mg = (
        np.clip(np.asarray(fa.min_gen, dtype=float), 0.0, None)
        if fa.min_gen is not None
        else np.zeros((n, 8760))
    )
    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    if mc.shape[1] == 1:
        mc = np.repeat(mc, 8760, axis=1)
    zone_names = list(isoc.zone_names)
    zidx = np.asarray(fa.zone_idx).astype(int)
    zone = np.array([zone_names[i] for i in zidx])
    groups = np.asarray(list(fa.plant_group))

    sysd = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    price = sysd.pivot(index="hour", columns="zone", values="price").sort_index()
    pz = np.vstack([price[z].to_numpy() for z in zone])  # (n, 8760)

    run = pz >= mc
    e_attain = np.maximum(mg, cap * run).sum(axis=1)
    sel = np.isin(groups, GROUPS)
    fp = st.get("fuel_prices")
    fp_mean = np.full(n, np.nan)
    if fp is not None:
        fpa = np.asarray(fp, dtype=float)
        if fpa.ndim == 2 and fpa.shape[0] == n:
            fp_mean = fpa.mean(axis=1)
        elif fpa.ndim == 1 and fpa.shape[0] == n:
            fp_mean = fpa
    df = pd.DataFrame(
        {
            "unit_id": list(fa.unit_ids),
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "group": groups,
            "zone": zone,
            "pmax": pmax,
            "heat_rate": np.asarray(fa.heat_rate, dtype=float),
            "fuel_price_mean": fp_mean,
            "avail_twh": cap.sum(axis=1) / 1e6,
            "floor_twh": mg.sum(axis=1) / 1e6,
            "mc_mean": mc.mean(axis=1),
            "mc_p10": np.percentile(mc, 10, axis=1),
            "zone_price_mean": pz.mean(axis=1),
            "hours_in_money": run.sum(axis=1),
            "attain_twh": e_attain / 1e6,
        }
    )[sel]
    df.to_parquet(out / f"units_{y}.parquet", index=False)
    idx = np.where(sel & (groups == "ST_GAS"))[0]
    np.savez_compressed(
        out / f"stgas_hourly_{y}.npz",
        unit_ids=np.asarray(list(fa.unit_ids))[idx],
        mc=mc[idx].astype(np.float32),
        cap=cap[idx].astype(np.float32),
        floor=mg[idx].astype(np.float32),
        price=pz[idx].astype(np.float32),
        fuel=np.asarray(fp, dtype=float)[idx].astype(np.float32),
        heat_rate=np.asarray(fa.heat_rate, dtype=float)[idx],
    )
    # Relative merit: capacity-weighted mean P0 offer per (group, zone, month).
    mon = pd.to_datetime(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), unit="h")
    mcm = pd.DataFrame(mc.T).groupby(mon.month).mean().T.to_numpy()  # (n, 12)
    rows = []
    for g in np.unique(groups):
        for z in zone_names:
            m = (groups == g) & (zone == z) & (pmax > 0)
            if not m.any():
                continue
            w = pmax[m]
            for mo in range(12):
                rows.append(
                    {
                        "group": g,
                        "zone": z,
                        "month": mo + 1,
                        "mw": float(w.sum()),
                        "offer_mean": float((mcm[m, mo] * w).sum() / w.sum()),
                    }
                )
    pd.DataFrame(rows).to_parquet(out / f"group_offers_{y}.parquet", index=False)
    g = (
        df[df.group == "ST_GAS"]
        .groupby("zone")[["avail_twh", "floor_twh", "attain_twh"]]
        .sum()
    )
    print(
        json.dumps(
            {"year": y, "fuel_prices_shape": getattr(fp, "shape", None)}, default=str
        )
    )
    print(g.round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
