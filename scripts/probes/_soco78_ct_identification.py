"""SOCO-78 phase 0 (ZERO LP): WHY do SOCO's cheapest CTs rarely start? Identification census.

Rule 32 ``[R-SHARD]`` (a): never solves. Reads the soco-76 keeper legs (gitignored, fetched at
the RESULT-soco-76 §6 SHAs) and SOCO's own EIA-860 / EIA-923 / CAMPD, and puts every soco-77
§2 candidate for the CT ranking inversion beside the per-plant model/EIA-923 ratio:

- ``attrs``   — per CT_PEAKER plant: EIA-860 owner / sector / EWG status / BA / pipelines,
  dual-fuel capability (860 multifuel), EIA-923 oil share of fuel, EIA-923 Page-5 gas
  receipts coverage and price, model offer (leg ``mc`` p50 when dispatched, econ tranches),
  implied model fuel $/MMBtu (mc / the CEMS heat rate), CEMS heat rate, CEMS hours on vs
  model hours on.
- ``timing``  — per dispatching entity (EIA-860 operator/sector): model vs CEMS TWh, top-decile-load share.
- ``rank``    — Spearman correlation of log(model/923) against each candidate, pooled and per year.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco78_ct_identification.py attrs|rank|timing
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
CT = "CT_PEAKER"
T = 8760
RAW = _ROOT / "data/raw"
OUT = _ROOT / "docs/records/soco/r-soco"
SPLIT = OUT / "soco77_ct_plant_split.csv"


def model_side(y: int) -> pd.DataFrame:
    """Per CT plant: model TWh, hours on, offer p50 when on, capacity (leg unit hourlies)."""
    leg = _ROOT / f"results/calibration/soco76_{y}"
    u = pd.read_parquet(
        leg / f"hourly/unit_hourly_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"],
    )
    u = u[u.plant_group.astype(str) == CT]
    u["econ"] = ~u.unit_id.astype(str).str.contains("_committed")
    on = u[u.mw > 1.0]
    g = u.groupby("plant_code")
    out = pd.DataFrame(
        {
            "model_twh": g.mw.sum() / 1e6,
            "cap_mw_max": u.groupby(["plant_code", "hour"])
            .cap_mw.sum()
            .groupby("plant_code")
            .max(),
            "model_on_h": on.groupby("plant_code").hour.nunique(),
            "offer_p50_econ": u[u.econ].groupby("plant_code").mc.median(),
            "offer_min_econ": u[u.econ].groupby("plant_code").mc.min(),
        }
    )
    out.index.name = "plant"
    return out.reset_index().assign(year=y)


def cems_side(y: int, plants: list[int], states: dict[int, str]) -> pd.DataFrame:
    """Per plant: CEMS hours any unit on, heat rate (sum HI / sum gross load)."""
    rows = []
    by_state: dict[str, list[int]] = {}
    for p in plants:
        by_state.setdefault(states.get(p, ""), []).append(p)
    for st, ps in by_state.items():
        f = RAW / f"campd-unit-level/{st}_{y}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(
            f,
            columns=["facilityId", "date", "hour", "grossLoad", "heatInput", "opTime"],
        )
        d["facilityId"] = pd.to_numeric(d.facilityId, errors="coerce")
        d = d[d.facilityId.isin(ps)]
        d["on"] = d.opTime.fillna(0) > 0
        for p, dp in d.groupby("facilityId"):
            h = dp[dp.on]
            rows.append(
                {
                    "plant": int(p),
                    "year": y,
                    "cems_on_h": h.groupby(["date", "hour"]).ngroups,
                    "cems_hr": h.heatInput.sum() / max(h.grossLoad.sum(), 1e-9),
                }
            )
    return pd.DataFrame(rows, columns=["plant", "year", "cems_on_h", "cems_hr"])


def attrs() -> pd.DataFrame:
    """Full per plant-year census table."""
    split = pd.read_csv(SPLIT)[
        ["year", "plant", "eia923_twh", "starts_per_unit", "run_med"]
    ]
    pl = pd.read_parquet(RAW / "eia-860/eia860_plant.parquet")
    pl = pl.rename(columns={"Plant Code": "plant"})
    keep = [
        "plant",
        "Plant Name",
        "State",
        "Utility Name",
        "Sector",
        "Sector Name",
        "FERC Exempt Wholesale Generator Status",
        "Balancing Authority Code",
        "Natural Gas Pipeline Name 1",
        "Natural Gas LDC Name",
        "Natural Gas Storage",
    ]
    pl = pl[keep].drop_duplicates("plant")
    states = dict(zip(pl.plant, pl.State))
    mf = pd.read_parquet(RAW / "eia-860/eia860_multifuel_operable.parquet")
    mf = mf[mf["Technology"].astype(str).str.contains("Combustion Turbine", na=False)]
    dual = (
        mf.groupby("Plant Code")
        .apply(
            lambda d: (d["Switch Between Oil and Natural Gas?"] == "Y").mean(),
            include_groups=False,
        )
        .rename("dual_fuel_share")
    )
    g923 = pd.read_csv(
        RAW / "eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
    )
    g923 = g923[g923.prime_mover.isin(["GT", "IC", "CT"])]
    oil_codes = {"DFO", "RFO", "KER", "JF", "WO"}
    g923["oil"] = g923.fuel_type.isin(oil_codes) * g923.total_fuel_mmbtu
    fuel = g923.groupby(["year", "plant_id"]).agg(
        tot=("total_fuel_mmbtu", "sum"), oil=("oil", "sum")
    )
    fuel["oil_share"] = fuel.oil / fuel.tot.where(fuel.tot > 0)
    fuel = fuel.reset_index().rename(columns={"plant_id": "plant"})[
        ["year", "plant", "oil_share"]
    ]
    rc = pd.read_parquet(RAW / "_processed-legacy/eia923_monthly_fuel_costs.parquet")
    rc = rc[rc.fuel_group.astype(str).str.lower().str.contains("gas")]
    rc["pq"] = rc.price_per_mmbtu * rc.quantity
    rcy = rc.groupby(["year", "plant_id"]).agg(
        pq=("pq", "sum"), q=("quantity", "sum"), n_m=("month", "nunique")
    )
    rcy["receipt_px"] = rcy.pq / rcy.q
    rcy = rcy.reset_index().rename(columns={"plant_id": "plant"})[
        ["year", "plant", "receipt_px", "n_m"]
    ]

    frames = []
    for y in YEARS:
        m = model_side(y)
        c = cems_side(y, m.plant.tolist(), states)
        frames.append(m.merge(c, on=["plant", "year"], how="left"))
    t = pd.concat(frames)
    t = t.merge(split, on=["year", "plant"], how="left").merge(
        pl, on="plant", how="left"
    )
    t = t.merge(dual, left_on="plant", right_index=True, how="left")
    t = t.merge(fuel, on=["year", "plant"], how="left").merge(
        rcy, on=["year", "plant"], how="left"
    )
    t["ratio"] = t.model_twh / t.eia923_twh.where(t.eia923_twh > 0)
    t["implied_fuel"] = t.offer_p50_econ / t.cems_hr
    t["ipp"] = t.Sector.isin([2, 3]).astype(int)
    t.to_csv(OUT / "soco78_ct_census.csv", index=False)
    return t


def rank(t: pd.DataFrame) -> None:
    """Spearman of log ratio vs candidates, plant-years with >= 0.02 TWh actual."""
    t = t[(t.eia923_twh >= 0.02) & (t.model_twh > 0)].copy()
    t["lr"] = np.log(t.model_twh / t.eia923_twh)
    cands = [
        "ipp",
        "offer_p50_econ",
        "cems_hr",
        "implied_fuel",
        "receipt_px",
        "oil_share",
        "dual_fuel_share",
        "starts_per_unit",
        "cems_on_h",
    ]
    res = {c: t[["lr", c]].dropna().corr(method="spearman").iloc[0, 1] for c in cands}
    print("pooled n=", len(t), {k: round(v, 3) for k, v in res.items()})
    cols = [
        "year",
        "plant",
        "Plant Name",
        "Utility Name",
        "Sector",
        "model_twh",
        "eia923_twh",
        "ratio",
        "offer_p50_econ",
        "cems_hr",
        "implied_fuel",
        "receipt_px",
        "n_m",
        "oil_share",
        "dual_fuel_share",
        "starts_per_unit",
        "model_on_h",
        "cems_on_h",
        "Natural Gas Pipeline Name 1",
    ]
    with pd.option_context("display.width", 300, "display.max_columns", 40):
        print(
            t[t.year.isin([2019, 2023])]
            .sort_values(["year", "ratio"], ascending=[True, False])[cols]
            .round(3)
            .to_string(index=False)
        )


def _entity(r: pd.Series) -> str:
    """Dispatching entity from EIA-860 plant operator + sector (published per-plant fields)."""
    u = str(r["Utility Name"])
    if "Oglethorpe" in u:
        return "OPC"
    if any(k in u for k in ("Georgia Power", "Alabama Power", "Mississippi Power")):
        return "SO-utility"
    if "Southern Power" in u:
        return "SouthernPower"
    if r["Sector"] in (2, 3):
        return "IPP"
    return "muni/coop"


def timing(t: pd.DataFrame) -> pd.DataFrame:
    """Per entity x year: model vs CEMS TWh, share of energy in the top-10 % SOCO-demand hours,
    hours on, hourly r. CEMS for the SO-utility and muni/coop groups includes the non-CT units
    of mixed plants (Greene County, McIntosh) and is NOT comparable; IPP / OPC / SouthernPower
    plants are CT-only."""
    t = t.copy()
    t["entity"] = t.apply(_entity, axis=1)
    ent = dict(zip(t.plant, t.entity))
    st = {p: s for p, s in zip(t.plant, t.State) if isinstance(s, str)}
    rows = []
    for y in YEARS:
        leg = _ROOT / f"results/calibration/soco76_{y}"
        d = (
            pd.read_parquet(leg / f"hourly/system_{y}.parquet")
            .groupby("hour")
            .demand.sum()
            .values
        )
        top = d >= np.quantile(d, 0.90)
        u = pd.read_parquet(
            leg / f"hourly/unit_hourly_{y}.parquet",
            columns=["plant_code", "plant_group", "hour", "mw"],
        )
        u = u[u.plant_group.astype(str) == CT]
        u["e"] = u.plant_code.map(ent)
        m = u.groupby(["e", "hour"]).mw.sum().unstack(0).reindex(range(T)).fillna(0)
        fr = []
        for s in set(st.values()):
            f = pd.read_parquet(
                RAW / f"campd-unit-level/{s}_{y}.parquet",
                columns=["facilityId", "date", "hour", "grossLoad"],
            )
            f["facilityId"] = pd.to_numeric(f.facilityId, errors="coerce")
            fr.append(f[f.facilityId.isin(list(ent))])
        c = pd.concat(fr)
        c["h"] = ((c.date - pd.Timestamp(f"{y}-01-01")).dt.days * 24 + c.hour).astype(
            int
        )
        c = c[c.h < T]
        c["e"] = c.facilityId.map(ent)
        a = c.groupby(["e", "h"]).grossLoad.sum().unstack(0).reindex(range(T)).fillna(0)
        z = np.zeros(T)
        for e in sorted(set(m.columns) | set(a.columns)):
            mm = m[e].values if e in m else z
            aa = a[e].values if e in a else z
            rows.append(
                {
                    "year": y,
                    "entity": e,
                    "model_twh": mm.sum() / 1e6,
                    "eia923_twh": t[(t.year == y) & (t.entity == e)].eia923_twh.sum(),
                    "cems_twh": aa.sum() / 1e6,
                    "model_top10": mm[top].sum() / max(mm.sum(), 1),
                    "cems_top10": aa[top].sum() / max(aa.sum(), 1),
                    "model_on_h": int((mm > 1).sum()),
                    "cems_on_h": int((aa > 1).sum()),
                    "r_hourly": float(np.corrcoef(mm, aa)[0, 1])
                    if mm.std() > 0 and aa.std() > 0
                    else np.nan,
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "soco78_ct_entity_timing.csv", index=False)
    print(out.round(3).to_string(index=False))
    return out


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["attrs", "rank", "timing"])
    a = ap.parse_args()
    f = OUT / "soco78_ct_census.csv"
    t = attrs() if a.what == "attrs" or not f.exists() else pd.read_csv(f)
    if a.what == "timing":
        timing(t)
    else:
        rank(t)


if __name__ == "__main__":
    main()
