"""closeout-SOCO-3 zero-LP reach of the EXISTING take-or-pay family on SOCO: the per-yard monthly pile with same-year
measured receipts (coal_fuel_inventory -> _plant_grain -> _take_floor -> _monthly_pile -> _measured_receipts).

Reproduces the field's identity (mechanism-matrix row coal_monthly_pile_measured_receipts; data/coal_fuel_inventory.py
build_coal_monthly_pile / build_coal_measured_receipts) per SOCO coal plant, month-end m of year Y:
    floor(m)   = max(0, (S_dec - S_max) x hc + cumC_Y(m))      cumC = same-year contract (C/NC/T) lots, MMBtu
    ceiling(m) = S_dec x hc + cumR_Y(m)                         cumR = all same-year lots, MMBtu
with S_dec = Dec(Y-1) stock, S_max = max month-end stock through Y-1 (2018 onward on disk), hc = Y-1 Page-5 heat
content. MMBtu -> MWh at the plant's measured HR (CAMPD heat input / EIA-923 coal net, same year: conversion only).
Against the keeper's cumulative coal energy: minimum added energy to meet the floor = max_m (floor - model)+,
minimum cut to meet the ceiling = max_m (model - ceiling)+. The floor is SOFT in the field (shortfall priced at the
yard's coal fuel price); this probe treats it as hard (upper bound). Outputs pile_reach_plant_year.csv, and C1
re-scored with the scorer's own score_fuelmix (net coal change displaces/refills CC_REGULAR one-for-one).
"""

from __future__ import annotations

import base64
import glob
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import calibration_verdict as cv  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

OUT = REPO / "docs/records/soco/closeout-soco-3"
KEEPER = REPO / "results/calibration/closeout_soco_2_span/hourly"
CONTRACT = ("C", "NC", "T")
PRB = {6002, 6073, 6124, 6257}
STATES = ("GA", "AL", "MS", "FL")
COAL_FUELS = ("BIT", "SUB", "LIG", "RC", "WC")


SMAX = sys.argv[1] if len(sys.argv) > 1 else "prior"
TAG = "" if SMAX == "prior" else f"_smax_{SMAX}"


def main() -> None:
    """Compute floor/ceiling reach per plant-year, write it, and re-score C1."""
    pm = pd.read_csv(OUT / "census_plant_month.csv")
    plants = sorted(int(p) for p in pm.plant.unique())
    r = pd.concat(
        pd.read_csv(p, low_memory=False)
        for p in sorted(
            glob.glob(str(RAW_DATA_DIR / "coal-receipts" / "coal_receipts_*.csv"))
        )
    )
    r = r[r["Plant Id"].isin(plants)].copy()
    r["mm"] = r.QUANTITY * r["Average Heat Content"]
    r["c_mm"] = np.where(
        r["Purchase Type"].astype(str).str.strip().isin(CONTRACT), r.mm, 0.0
    )
    rec = r.groupby(["Plant Id", "YEAR", "MONTH"])[["mm", "c_mm", "QUANTITY"]].sum()
    hc_y = (
        r.groupby(["Plant Id", "YEAR"]).mm.sum()
        / r.groupby(["Plant Id", "YEAR"]).QUANTITY.sum()
    )
    sys.path.insert(0, str(REPO / "scripts/probes"))
    from _closeout_soco3_takeorpay_census import read_stocks  # noqa: E402

    st = (
        read_stocks(set(plants))
        .rename(columns={"Plant Id": "plant", "YEAR": "year", "MONTH": "month"})
        .dropna()
    )
    gen = pd.read_parquet(
        RAW_DATA_DIR / "_processed-legacy/eia923_monthly_generation.parquet"
    )
    rows = []
    for y in range(2019, 2026):
        hi = []
        for s in STATES:
            for f in glob.glob(str(RAW_DATA_DIR / f"campd-unit-level/{s}_{y}.parquet")):
                c = pd.read_parquet(
                    f, columns=["facilityId", "heatInput", "primaryFuelInfo"]
                )
                c["facilityId"] = c.facilityId.astype(int)
                hi.append(c[c.primaryFuelInfo.str.contains("Coal", na=False)])
        hi = pd.concat(hi).groupby("facilityId").heatInput.sum()
        e = (
            gen[
                (gen.year == y)
                & (gen.prime_mover == "ST")
                & gen.fuel_type.isin(COAL_FUELS)
            ]
            .groupby("plant_id")
            .netgen_annual_mwh.sum()
        )
        for p in plants:
            g = pm[(pm.plant == p) & (pm.year == y)].sort_values("month")
            if g.empty or g.model_mwh.sum() + g.actual_mwh.sum() < 1e3:
                continue
            prev = st[(st.plant == p) & (st.year == y - 1) & (st.month == 12)].stock
            # field construction: max month-end stock through Y-1; sensitivity SMAX=all: max over the whole corpus
            smax = st[
                (st.plant == p) & ((st.year <= y - 1) | (SMAX == "all"))
            ].stock.max()
            hc = hc_y.get((p, y - 1), hc_y.get((p, y), np.nan))
            hr = (
                hi.get(p, np.nan) / e.get(p, np.nan) if e.get(p, 0) > 0 else np.nan
            )  # MMBtu/MWh
            if prev.empty or not np.isfinite(hc) or not np.isfinite(hr):
                rows.append(dict(plant=p, year=y, note="no stock/hc/hr"))
                continue
            sdec = float(prev.iloc[0])
            m = rec.reindex(
                pd.MultiIndex.from_product([[p], [y], range(1, 13)]), fill_value=0.0
            )
            cumC, cumR = m.c_mm.cumsum().to_numpy(), m.mm.cumsum().to_numpy()
            floor = np.maximum(0.0, (sdec - smax) * hc + cumC) / hr
            ceil = (sdec * hc + cumR) / hr
            mod = (
                g.set_index("month")
                .model_mwh.reindex(range(1, 13), fill_value=0.0)
                .cumsum()
                .to_numpy()
            )
            act = (
                g.set_index("month")
                .actual_mwh.reindex(range(1, 13), fill_value=0.0)
                .cumsum()
                .to_numpy()
            )
            rows.append(
                dict(
                    plant=p,
                    year=y,
                    hr=hr,
                    headroom_frac=1 - sdec / smax,
                    floor_dec_gwh=floor[-1] / 1e3,
                    ceil_dec_gwh=ceil[-1] / 1e3,
                    model_gwh=mod[-1] / 1e3,
                    actual_gwh=act[-1] / 1e3,
                    add_gwh=max(0.0, (floor - mod).max()) / 1e3,
                    cut_gwh=max(0.0, (mod - ceil).max()) / 1e3,
                    floor_over_actual_gwh=max(0.0, (floor - act).max()) / 1e3,
                    ceil_under_actual_gwh=max(0.0, (act - ceil).max()) / 1e3,
                )
            )
    d = pd.DataFrame(rows)
    d.to_csv(OUT / f"pile_reach_plant_year{TAG}.csv", index=False)
    pd.set_option("display.width", 250)
    print(d.round(2).to_string(index=False))
    d["net_gwh"] = d.add_gwh.fillna(0) - d.cut_gwh.fillna(0)
    print(
        d.groupby("year")[
            [
                "add_gwh",
                "cut_gwh",
                "net_gwh",
                "floor_over_actual_gwh",
                "ceil_under_actual_gwh",
            ]
        ]
        .sum()
        .round(0)
        .to_string()
    )

    t = (
        REPO / "frontend/data/backcast/runs/2026-10-03-closeout-soco-2-nuclear.js"
    ).read_text()
    P = json.loads(
        gzip.decompress(
            base64.b64decode(re.search(r'="([A-Za-z0-9+/=]+)"', t).group(1))
        )
    )
    out = []
    for y in range(2019, 2026):
        yb = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/SOCO/{y}.json.gz")
        )["bench"]
        dy = d[d.year == y]
        prb = dy[dy.plant.isin(PRB)].net_gwh.sum() / 1e3
        bit = dy[~dy.plant.isin(PRB)].net_gwh.sum() / 1e3
        for form in ("keeper", "pile"):
            yp = json.loads(json.dumps(P["years"][str(y)]))
            if form == "pile":
                gm = yp["gmModel"]
                gm["COAL_PRB"] = gm.get("COAL_PRB", 0) + prb
                gm["COAL_BIT"] = gm.get("COAL_BIT", 0) + bit
                gm["CC_REGULAR"] = gm["CC_REGULAR"] - (prb + bit)
            for row in cv.score_fuelmix(y, yp, yb, iso="SOCO"):
                if row["key"] in ("CC_REGULAR", "COAL_BIT", "COAL_PRB"):
                    out.append(
                        dict(
                            year=y,
                            form=form,
                            cls=row["key"],
                            status=row["status"],
                            share_pp=row.get("share_pp"),
                            model=row.get("model"),
                            actual=row.get("actual"),
                        )
                    )
    o = pd.DataFrame(out)
    o.to_csv(OUT / f"pile_c1_reach{TAG}.csv", index=False)
    o["v"] = (
        o.share_pp.round(2).astype(str)
        + " "
        + o.status.str[0]
        + " ("
        + o.model.round(1).astype(str)
        + ")"
    )
    print(
        o.pivot_table(
            index=["year", "cls"], columns="form", values="v", aggfunc="first"
        ).to_string()
    )


if __name__ == "__main__":
    main()
