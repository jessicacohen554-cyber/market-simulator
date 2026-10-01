#!/usr/bin/env python3
"""miso-295 (ZERO LP): how did the real MISO coal fleet express fuel conservation, 2019-2025?

Owner ruling 2026-10-01 ("Do a coal study on all years not just 2021"). The study
extends miso-288's 2022 method to every year the keeper carries, and settles first
whether the flat annual coal offset against EIA-930 is a real overburn or a
boundary/reporting artifact. Every block uses the MODEL FLEET's coal plants
(the bench's per-plant set, ``frontend/data/backcast/bench/MISO/<y>.json.gz``,
groups ``COAL_*``) as the footprint, so model and actual are on one boundary.

Blocks (all measured; nothing here feeds a solve, rule 13):

A. Boundary. Monthly coal TWh: keeper P1 (``class_hourly``), EIA-923 net
   generation of the model-fleet coal plants (bench ``e_mon``), and EIA-930 MISO
   adjusted net generation. Prints model - EIA-923 and EIA-930 - EIA-923.
B. Gas mirror. Same as A for the gas classes (CC_*, CT_*, ST_GAS, ST_CHP), model
   vs EIA-923 plant-matched.
C. Pile accounting (EIA-923 Sch. 2 stocks + Page 5 receipts, 2019-2024; 2025 has
   no plant-level stocks file). Per year: opening stock (Dec Y-1), the keeper
   budget's prior-years receipts rate (mean Y-2..Y-1), actual receipts, implied
   burn, minimum month-end days on hand, and summer / fall burn minus receipts.
D. CAMPD hourly, coal units at those plants: monthly mean online capacity
   (sum of unit p99 over units with opTime > 0) and loading-when-on, so a
   conservation that decommits units is told apart from one that runs them low.
E. Keeper P1 vs zone-resolved actual night (h0-5) and all-hours monthly mean
   price, system load-weighted (the miso-294 basis).

Output: ``results/calibration/_miso295_coal_study.json``.

Usage::

    uv run python scripts/probes/_miso295_coal_study.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data/raw"
HOURLY = REPO / "results/calibration/miso280_span/hourly"
BENCH = REPO / "frontend/data/backcast/bench/MISO"
OUT = REPO / "results/calibration/_miso295_coal_study.json"
YEARS = tuple(range(2019, 2026))
STOCK_YEARS = tuple(range(2019, 2025))
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
GAS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP")
NIGHT = range(0, 6)
MISO_STATES = (
    "AR",
    "IA",
    "IL",
    "IN",
    "KY",
    "LA",
    "MI",
    "MN",
    "MO",
    "MS",
    "MT",
    "ND",
    "SD",
    "TX",
    "WI",
)


def bench(year: int) -> dict:
    """The committed bench payload for one year."""
    return json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]


def coal_plants(year: int) -> set[int]:
    """Model-fleet coal plant ids for ``year`` (bench groups COAL_*)."""
    return {
        int(k.split(":")[0])
        for k, p in bench(year)["plants"].items()
        if p["group"].startswith("COAL")
    }


def plant_monthly(year: int, groups) -> np.ndarray:
    """EIA-923 monthly net generation (TWh) summed over bench plants in ``groups``."""
    rows = [
        np.array(p["e_mon"], float)
        for p in bench(year)["plants"].values()
        if p["group"] in groups or p["group"].startswith(groups)
    ]
    return np.nansum(rows, axis=0) / 1e3


def model_monthly(year: int, groups) -> np.ndarray:
    """Keeper P1 monthly TWh for classes starting with any of ``groups``."""
    c = pd.read_parquet(HOURLY / f"class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & c["klass"].astype(str).str.startswith(groups)]
    m = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(c["hour"], unit="h")).dt.month
    return c.groupby(m)["mw"].sum().reindex(range(1, 13)).fillna(0).to_numpy() / 1e6


def e930_monthly(year: int) -> np.ndarray:
    """EIA-930 MISO adjusted coal net generation, monthly TWh."""
    b = pd.concat(
        pd.read_parquet(RAW / f"eia-930/EIA930_BALANCE_{year}_{h}.parquet")
        for h in ("Jan_Jun", "Jul_Dec")
    )
    b = b[b["Balancing Authority"] == "MISO"]
    mon = pd.to_datetime(b["Data Date"].astype(str)).dt.month
    col = "Net Generation (MW) from Coal (Adjusted)"
    v = pd.to_numeric(b[col], errors="coerce").groupby(mon).sum()
    return v.reindex(range(1, 13)).to_numpy() / 1e6


def block_ab() -> dict:
    """Blocks A and B: boundary and gas mirror, every year."""
    out = {}
    for y in YEARS:
        cm, ce = model_monthly(y, ("COAL",)), plant_monthly(y, ("COAL",))
        c930 = e930_monthly(y)
        gm, ge = model_monthly(y, GAS), plant_monthly(y, GAS)
        out[y] = {
            "coal_model": cm.round(3).tolist(),
            "coal_e923": ce.round(3).tolist(),
            "coal_e930": c930.round(3).tolist(),
            "gas_model": gm.round(3).tolist(),
            "gas_e923": ge.round(3).tolist(),
        }
    return out


def _pid(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce ``Plant Id`` to int (some vintages ship it as text)."""
    df["Plant Id"] = pd.to_numeric(df["Plant Id"], errors="coerce")
    return df.dropna(subset=["Plant Id"]).astype({"Plant Id": int})


def _stocks(year: int, ids: set[int]) -> np.ndarray:
    """Month-end coal stock (Mt) at ``ids`` for ``year``."""
    s = _pid(pd.read_csv(RAW / f"coal-stocks/coal_stocks_{year}.csv", thousands=","))
    s = s[s["Plant Id"].isin(ids) & (s["AER Fuel Type Code"] == "COL")]
    q = [f"Quantity {m}" for m in MONTHS]
    v = s[q].apply(
        lambda c: pd.to_numeric(c.astype(str).str.replace(",", ""), errors="coerce")
    )
    return v.fillna(0.0).sum().to_numpy() / 1e6


def _receipts(year: int, ids: set[int]) -> np.ndarray:
    """Monthly coal receipts (Mt) at ``ids`` for ``year``."""
    r = _pid(
        pd.read_csv(
            RAW / f"coal-receipts/coal_receipts_{year}.csv",
            low_memory=False,
            usecols=["MONTH", "Plant Id", "FUEL_GROUP", "QUANTITY"],
        )
    )
    r = r[r["Plant Id"].isin(ids) & (r["FUEL_GROUP"] == "Coal")]
    q = pd.to_numeric(r["QUANTITY"], errors="coerce").groupby(r["MONTH"]).sum()
    return q.reindex(range(1, 13)).fillna(0).to_numpy() / 1e6


def block_c() -> dict:
    """Block C: pile accounting on the model-fleet coal plants, 2019-2024."""
    out = {}
    for y in STOCK_YEARS:
        ids = coal_plants(y)
        st = _stocks(y, ids)
        s_dec = _stocks(y - 1, ids)[11]
        rec = _receipts(y, ids)
        r_prior = np.mean([_receipts(y - k, ids).sum() for k in (1, 2)])
        burn = np.empty(12)
        prev = s_dec
        for m in range(12):
            burn[m] = prev + rec[m] - st[m]
            prev = st[m]
        rate = burn.sum() / 365.0
        days = st / rate
        out[y] = {
            "plants": len(ids),
            "opening_stock_mt": round(float(s_dec), 2),
            "opening_days": round(float(s_dec / rate), 1),
            "receipts_prior_rate_mt": round(float(r_prior), 2),
            "receipts_actual_mt": round(float(rec.sum()), 2),
            "receipts_surprise_mt": round(float(rec.sum() - r_prior), 2),
            "burn_mt": round(float(burn.sum()), 2),
            "keeper_budget_mt": round(float(s_dec + r_prior), 2),
            "budget_over_burn": round(float((s_dec + r_prior) / burn.sum()), 3),
            "ending_stock_mt": round(float(st[11]), 2),
            "min_days": round(float(days.min()), 1),
            "min_days_month": int(days.argmin()) + 1,
            "days_on_hand": days.round(1).tolist(),
            "burn_mt_month": burn.round(2).tolist(),
            "receipts_mt_month": rec.round(2).tolist(),
            "jja_burn_minus_receipts": round(float((burn - rec)[5:8].sum()), 2),
            "son_burn_minus_receipts": round(float((burn - rec)[8:11].sum()), 2),
        }
    return out


def block_d() -> dict:
    """Block D: CAMPD coal units at model-fleet plants, online GW and loading."""
    out = {}
    for y in YEARS:
        ids = coal_plants(y)
        frames = []
        for stt in MISO_STATES:
            p = RAW / f"campd-unit-level/{stt}_{y}.parquet"
            if not p.exists():
                continue
            d = pd.read_parquet(
                p,
                columns=[
                    "facilityId",
                    "unitId",
                    "date",
                    "hour",
                    "opTime",
                    "grossLoad",
                    "primaryFuelInfo",
                ],
            )
            d = d[
                pd.to_numeric(d["facilityId"], errors="coerce").isin(ids)
                & d["primaryFuelInfo"].fillna("").str.contains("Coal")
            ]
            frames.append(d)
        d = pd.concat(frames)
        d["gl"] = d["grossLoad"].fillna(0.0)
        d["uid"] = d["facilityId"].astype(str) + "_" + d["unitId"].astype(str)
        cap = d.groupby("uid")["gl"].quantile(0.99)
        cap = cap[cap > 50]
        d = d[d["uid"].isin(cap.index)]
        d["cap"] = d["uid"].map(cap)
        d["on"] = d["opTime"].fillna(0) > 0
        d["month"] = d["date"].dt.month
        d["oncap"] = d["cap"] * d["on"]
        h = (
            d.groupby(["month", "date", "hour"])[["oncap", "gl", "cap"]].sum() / 1e3
        ).rename(columns={"oncap": "online_gw", "gl": "gen_gw", "cap": "fleet_gw"})
        h = h.reset_index()
        rec = {}
        for m, g in h.groupby("month"):
            rec[int(m)] = {
                "fleet_gw": round(float(g["fleet_gw"].mean()), 2),
                "online_gw": round(float(g["online_gw"].mean()), 2),
                "gen_gw": round(float(g["gen_gw"].mean()), 2),
                "loading_when_on": round(
                    float(g["gen_gw"].sum() / g["online_gw"].sum()), 3
                ),
            }
        out[y] = rec
    return out


def block_e() -> dict:
    """Block E: keeper P1 vs zone-resolved actual, monthly night and all-hours means."""
    sys.path.insert(0, str(REPO / "scripts/probes"))
    from _miso294_c3b2021_phase0 import zone_prices

    out = {}
    for y in YEARS:
        pm, dm, az = zone_prices(y)
        ok = az.notna().all(axis=1)
        w = dm.sum(axis=1)
        m = ((pm * dm).sum(axis=1) / w)[ok]
        a = ((az * dm).sum(axis=1) / w)[ok]
        ts = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(m.index, unit="h")
        f = pd.DataFrame({"m": m.values, "a": a.values, "mon": ts.month, "h": ts.hour})
        rec = {}
        for mon, g in f.groupby("mon"):
            n = g[g["h"].isin(NIGHT)]
            rec[int(mon)] = {
                "mean_model": round(float(g["m"].mean()), 2),
                "mean_actual": round(float(g["a"].mean()), 2),
                "night_model": round(float(n["m"].mean()), 2),
                "night_actual": round(float(n["a"].mean()), 2),
            }
        out[y] = rec
    return out


def main() -> int:
    """Run blocks A-E, print the headline tables and write the JSON record."""
    ab = block_ab()
    c = block_c()
    d = block_d()
    e = block_e()
    for y in YEARS:
        r = ab[y]
        cm, ce, c9 = (np.array(r[k]) for k in ("coal_model", "coal_e923", "coal_e930"))
        gm, ge = np.array(r["gas_model"]), np.array(r["gas_e923"])
        print(
            f"{y} coal model {cm.sum():6.1f} e923 {ce.sum():6.1f} e930 {c9.sum():6.1f}"
            f" | gas model {gm.sum():6.1f} e923 {ge.sum():6.1f}"
        )
        print("   coal m-923 " + " ".join(f"{v:+5.1f}" for v in cm - ce))
        print("   930 - 923  " + " ".join(f"{v:+5.1f}" for v in c9 - ce))
        print("   gas  m-923 " + " ".join(f"{v:+5.1f}" for v in gm - ge))
        print(
            "   price m-a  "
            + " ".join(
                f"{e[y][k]['mean_model'] - e[y][k]['mean_actual']:+5.1f}"
                for k in range(1, 13)
            )
        )
        print(
            "   online GW  "
            + " ".join(f"{d[y][k]['online_gw']:5.1f}" for k in range(1, 13))
        )
        print(
            "   loading    "
            + " ".join(f"{d[y][k]['loading_when_on']:5.2f}" for k in range(1, 13))
        )
        if y in c:
            k = c[y]
            print(
                f"   pile: open {k['opening_stock_mt']} Mt ({k['opening_days']} d), "
                f"prior rate {k['receipts_prior_rate_mt']}, actual {k['receipts_actual_mt']} "
                f"(surprise {k['receipts_surprise_mt']:+}), burn {k['burn_mt']}, "
                f"budget/burn {k['budget_over_burn']}, min {k['min_days']} d "
                f"(m{k['min_days_month']}), JJA burn-rec {k['jja_burn_minus_receipts']:+}, "
                f"SON {k['son_burn_minus_receipts']:+}"
            )
            print("   days       " + " ".join(f"{v:5.0f}" for v in k["days_on_hand"]))
    OUT.write_text(
        json.dumps(
            {"boundary_gas": ab, "pile": c, "campd": d, "price": e},
            indent=1,
            default=float,
        )
    )
    print("wrote", OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
