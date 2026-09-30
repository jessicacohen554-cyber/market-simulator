#!/usr/bin/env python3
"""miso-288 (ZERO LP): how did the real 2022 MISO coal fleet express its fuel shortage?

The keeper's ``coal_fuel_inventory`` rows bind all year in 2022 and the LP
prices the shortage as a uniform coal dual, so coal leaves summer NIGHTS and
gas sets the night price (miso-287 §3). This probe measures what the REAL
fleet did, from measured sources only, and sets it beside the keeper:

A. EIA-923 Sch. 2 (stocks) + Sch. 5 (receipts), plants with Balancing
   Authority Code MISO: monthly ending stock, receipts, implied burn
   (``stock[m-1] + receipts[m] - stock[m]``), days of burn on hand.
B. CAMPD hourly gross load, coal-primary units at those plants: monthly TWh,
   night (h0-5) vs day (h10-17) mean GW, dark units, and the unit-level
   ceiling (monthly max hourly output / the unit's 2019-2024 p99).
C. Keeper P1 coal classes (``class_hourly``): the same night/day grain.
D. ILLINOIS.HUB DA LMP night vs day medians by month; keeper P1 price in the
   hub zone.

The question each block answers: did the real fleet ration by pulling coal
off NIGHTS (the LP's uniform-dual signature), or by something else (derates,
dark units, deferred burn)? Output: ``results/calibration/_miso288_coal_scarcity.json``.
Rule 13: nothing here feeds a solve.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data/raw"
KEEPER = REPO / "results/calibration/miso280_span"
OUT = REPO / "results/calibration/_miso288_coal_scarcity.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
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
NIGHT = range(0, 6)
DAY = range(10, 18)
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


def _pid(df):
    """Coerce ``Plant Id`` to int (some vintages ship it as text)."""
    df["Plant Id"] = pd.to_numeric(df["Plant Id"], errors="coerce")
    return df.dropna(subset=["Plant Id"]).astype({"Plant Id": int})


def stocks_and_receipts():
    """Block A: MISO-BA coal stock / receipts / implied burn by month (k tons)."""
    rows = []
    plants = {}
    # 2019's stocks sheet carries no BA column: the MISO plant set is the union
    # of every other year's stocks + every year's receipts BA == MISO.
    miso_ids = set()
    for y in YEARS:
        s = _pid(pd.read_csv(RAW / f"coal-stocks/coal_stocks_{y}.csv", thousands=","))
        if "Balancing Authority Code" in s:
            miso_ids |= set(s.loc[s["Balancing Authority Code"] == "MISO", "Plant Id"])
        r = _pid(
            pd.read_csv(
                RAW / f"coal-receipts/coal_receipts_{y}.csv",
                low_memory=False,
                usecols=["Plant Id", "Balancing Authority Code"],
            )
        )
        miso_ids |= set(r.loc[r["Balancing Authority Code"] == "MISO", "Plant Id"])
    for y in YEARS:
        s = _pid(pd.read_csv(RAW / f"coal-stocks/coal_stocks_{y}.csv", thousands=","))
        s = s[s["Plant Id"].isin(miso_ids) & (s["AER Fuel Type Code"] == "COL")].copy()
        q = [f"Quantity {m}" for m in MONTHS]
        s[q] = (
            s[q]
            .apply(
                lambda c: pd.to_numeric(
                    c.astype(str).str.replace(",", ""), errors="coerce"
                )
            )
            .fillna(0.0)
        )
        plants[y] = set(
            s.loc[s[[f"Quantity {m}" for m in MONTHS]].sum(axis=1) > 0, "Plant Id"]
        )
        st = (
            s[[f"Quantity {m}" for m in MONTHS]]
            .apply(pd.to_numeric, errors="coerce")
            .sum()
        )
        r = _pid(
            pd.read_csv(RAW / f"coal-receipts/coal_receipts_{y}.csv", low_memory=False)
        )
        r = r[r["Plant Id"].isin(miso_ids) & (r["FUEL_GROUP"] == "Coal")]
        rq = pd.to_numeric(r["QUANTITY"], errors="coerce").groupby(r["MONTH"]).sum()
        for i, m in enumerate(MONTHS):
            rows.append(
                {
                    "year": y,
                    "month": i + 1,
                    "stock_kt": st.iloc[i] / 1e3,
                    "receipts_kt": rq.get(i + 1, 0.0) / 1e3,
                }
            )
    df = pd.DataFrame(rows).sort_values(["year", "month"]).reset_index(drop=True)
    df["burn_kt"] = df["stock_kt"].shift(1) + df["receipts_kt"] - df["stock_kt"]
    df.loc[0, "burn_kt"] = np.nan
    ann = df.groupby("year").burn_kt.transform(lambda b: b.mean())
    df["days_on_hand"] = df["stock_kt"] / (ann * 12 / 365)
    return df, plants


def campd(plants):
    """Block B: CAMPD coal-primary units at MISO-BA coal plants."""
    out = {}
    per_unit = []
    for y in YEARS:
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
                pd.to_numeric(d.facilityId, errors="coerce").isin(plants[y])
                & d.primaryFuelInfo.fillna("").str.contains("Coal")
            ]
            frames.append(d)
        d = pd.concat(frames)
        d["gl"] = d.grossLoad.fillna(0.0)
        d["month"] = d.date.dt.month
        d["uid"] = d.facilityId.astype(str) + "_" + d.unitId.astype(str)
        per_unit.append(
            d.groupby(["uid", "month"])
            .gl.agg(["max", "sum"])
            .assign(year=y)
            .reset_index()
        )
        h = d.groupby(["month", "date", "hour"]).gl.sum().reset_index()
        rec = {}
        for m, g in h.groupby("month"):
            rec[int(m)] = {
                "twh": g.gl.sum() / 1e6,
                "night_gw": g[g.hour.isin(NIGHT)].gl.mean() / 1e3,
                "day_gw": g[g.hour.isin(DAY)].gl.mean() / 1e3,
            }
        um = d.groupby(["uid", "month"]).opTime.sum().unstack(fill_value=0)
        for m in rec:
            rec[m]["dark_units"] = int((um[m] == 0).sum())
            rec[m]["units"] = int(len(um))
        out[y] = rec
    pu = pd.concat(per_unit)
    cap = pu.groupby("uid")["max"].quantile(0.99).rename("cap")
    pu = pu.join(cap, on="uid")
    pu = pu[pu.cap > 50]
    for y in YEARS:
        s = pu[(pu.year == y) & (pu["sum"] > 0)]
        for m, g in s.groupby("month"):
            # MW-weighted monthly ceiling ratio over units that ran that month
            out[y][int(m)]["ceiling_ratio"] = float((g["max"]).sum() / g.cap.sum())
    return out


def keeper():
    """Block C+D (model side): keeper P1 coal night/day by month, P1 price."""
    out = {}
    for y in YEARS:
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[(ch["pass"] == "P1") & ch.klass.str.startswith("COAL")]
        mw = ch.groupby("hour").mw.sum().reindex(range(8760)).fillna(0.0).to_numpy()
        ts = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
        f = pd.DataFrame({"mw": mw, "m": ts.month, "h": ts.hour})
        sysd = (
            pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
            if (KEEPER / f"hourly/system_{y}.parquet").exists()
            else None
        )
        rec = {}
        for m, g in f.groupby("m"):
            rec[int(m)] = {
                "twh": g.mw.sum() / 1e6,
                "night_gw": g[g.h.isin(NIGHT)].mw.mean() / 1e3,
                "day_gw": g[g.h.isin(DAY)].mw.mean() / 1e3,
            }
        if sysd is not None:
            sp = (
                sysd[sysd["pass"] == "P1"]
                .groupby("hour")
                .price.median()
                .reindex(range(8760))
                .to_numpy()
            )
            f["p"] = sp
            for m, g in f.groupby("m"):
                rec[int(m)]["p_night"] = float(g[g.h.isin(NIGHT)].p.median())
                rec[int(m)]["p_day"] = float(g[g.h.isin(DAY)].p.median())
        out[y] = rec
    return out


def hub():
    """Block D: ILLINOIS.HUB DA LMP night/day monthly medians."""
    out = {}
    for y in YEARS:
        fr = []
        for p in sorted(
            (RAW / "lmp-data/MISO").glob(f"miso_hub_lmp_{y}_da_p*.csv")
        ) or [RAW / f"lmp-data/MISO/miso_hub_lmp_{y}_da.csv.gz"]:
            d = pd.read_csv(p)
            fr.append(d[(d.node == "ILLINOIS.HUB") & (d.value == "LMP")])
        d = pd.concat(fr)
        d["date"] = pd.to_datetime(d.date)
        long = d.melt(
            id_vars=["date"],
            value_vars=[f"he{i:02d}" for i in range(1, 25)],
            var_name="he",
            value_name="lmp",
        )
        long["h"] = long.he.str[2:].astype(int) - 1
        long["m"] = long.date.dt.month
        out[y] = {
            int(m): {
                "night": float(g[g.h.isin(NIGHT)].lmp.median()),
                "day": float(g[g.h.isin(DAY)].lmp.median()),
            }
            for m, g in long.groupby("m")
        }
    return out


def main():
    """Run blocks A-D and write the JSON record."""
    a, plants = stocks_and_receipts()
    b = campd(plants)
    c = keeper()
    d = hub()
    OUT.write_text(
        json.dumps(
            {
                "stocks": a.to_dict(orient="records"),
                "campd": b,
                "keeper": c,
                "hub": d,
                "plants": {y: len(v) for y, v in plants.items()},
            },
            indent=1,
            default=float,
        )
    )
    print("wrote", OUT)


if __name__ == "__main__":
    sys.exit(main())
