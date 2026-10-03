"""closeout-SOCO-3 zero-LP probe: does contracted coal look sunk where SOCO's model under-runs coal at night?

Census for the owner's take-or-pay hypothesis (R-45), readings fixed ex ante in
docs/records/soco/closeout-soco-3/PRECOMMIT-phase0-closeout-soco-3-2026-10-03.md:

- C-A: per SOCO coal plant-month, contract (C/NC/T) vs spot (S) share of tons and MMBtu from EIA-923 Page 5,
  tonnage-weighted months to contract expiration, contract vs spot delivered $/MMBtu, and burn
  (receipts - delta month-end stock, EIA-923 Page 2).
- C-B: per plant-month, keeper P1 coal MW (unit_marginal) vs CAMPD gross x plant EIA-923 net/gross in the lowest two
  system-load deciles of each year ("night").
- C-C: month-end stock as a fraction of the plant's maximum month-end stock 2018-2024 (headroom).

Keeper: results/calibration/closeout_soco_2_span. No LP, no ScenarioConfig field touched.
Outputs: docs/records/soco/closeout-soco-3/{census_plant_month,census_plant_year}.csv and printed summaries.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

KEEPER = REPO / "results/calibration/closeout_soco_2_span/hourly"
OUT = REPO / "docs/records/soco/closeout-soco-3"
YEARS = range(2019, 2026)
CONTRACT = ("C", "NC", "T")  # scripts/data/derive_coal_takeorpay.py _CONTRACT_CODES
COAL_FUELS = ("BIT", "SUB", "LIG", "RC", "WC")
MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
STOCK_COLS = [f"Quantity {m.capitalize()}" for m in MONTHS]
STATES = ("GA", "AL", "MS", "FL")


def read_receipts(plants: set[int]) -> pd.DataFrame:
    """Return Page-5 receipts for ``plants`` with MMBtu, $ and months-to-expiration columns."""
    r = pd.concat(
        pd.read_csv(p, low_memory=False)
        for p in sorted(
            glob.glob(str(RAW_DATA_DIR / "coal-receipts" / "coal_receipts_*.csv"))
        )
    )
    r = r[r["Plant Id"].isin(plants)].copy()
    r["mm"] = r.QUANTITY * r["Average Heat Content"]
    r["usd"] = pd.to_numeric(r.FUEL_COST, errors="coerce") * r.mm / 100.0  # cents/MMBtu
    r["pt"] = r["Purchase Type"].astype(str).str.strip()
    exp = pd.to_numeric(r["Contract Expiration Date"], errors="coerce")
    exp_m, exp_y = exp // 100, 2000 + exp % 100
    r["months_to_exp"] = (exp_y - r.YEAR) * 12 + (exp_m - r.MONTH)
    return r


def read_stocks(plants: set[int]) -> pd.DataFrame:
    """Return long-form month-end coal stock (tons) per plant-month from EIA-923 Page 2."""
    s = pd.concat(
        pd.read_csv(p, low_memory=False)
        for p in sorted(
            glob.glob(str(RAW_DATA_DIR / "coal-stocks" / "coal_stocks_*.csv"))
        )
    )
    s = s[s["Plant Id"].isin(plants)]
    long = s.melt(
        id_vars=["Plant Id", "YEAR"],
        value_vars=STOCK_COLS,
        var_name="m",
        value_name="stock",
    )
    long["stock"] = pd.to_numeric(long.stock, errors="coerce")
    long["MONTH"] = long.m.map({c: i + 1 for i, c in enumerate(STOCK_COLS)})
    return (
        long.groupby(["Plant Id", "YEAR", "MONTH"])
        .stock.sum(min_count=1)
        .rename("stock")
        .reset_index()
    )


def contract_month(r: pd.DataFrame, st: pd.DataFrame) -> pd.DataFrame:
    """Return the C-A / C-C plant-month table: shares, horizon, prices, burn and headroom."""
    isc = r.pt.isin(CONTRACT)
    r = r.assign(
        c_t=np.where(isc, r.QUANTITY, 0.0),
        c_mm=np.where(isc, r.mm, 0.0),
        c_usd=np.where(isc, r.usd, 0.0),
        s_mm=np.where(r.pt == "S", r.mm, 0.0),
        s_usd=np.where(r.pt == "S", r.usd, 0.0),
        hz=np.where(isc, r.months_to_exp * r.QUANTITY, 0.0),
    )
    g = (
        r.groupby(["Plant Id", "YEAR", "MONTH"])
        .agg(
            tons=("QUANTITY", "sum"),
            mm=("mm", "sum"),
            c_t=("c_t", "sum"),
            c_mm=("c_mm", "sum"),
            c_usd=("c_usd", "sum"),
            s_mm=("s_mm", "sum"),
            s_usd=("s_usd", "sum"),
            hz=("hz", "sum"),
        )
        .reset_index()
    )
    g["contract_share_mm"] = g.c_mm / g.mm
    g["contract_usd_mmbtu"] = g.c_usd / g.c_mm.replace(0, np.nan)
    g["spot_usd_mmbtu"] = g.s_usd / g.s_mm.replace(0, np.nan)
    g["months_to_exp"] = g.hz / g.c_t.replace(0, np.nan)
    st = st.sort_values(["Plant Id", "YEAR", "MONTH"]).copy()
    st["stock_prev"] = st.groupby("Plant Id").stock.shift(1)
    st["stock_max"] = st.groupby("Plant Id").stock.transform("max")
    st["headroom_used"] = st.stock / st.stock_max
    m = st.merge(g, on=["Plant Id", "YEAR", "MONTH"], how="outer")
    for c in ("tons", "c_t", "mm", "c_mm"):
        m[c] = m[c].fillna(0.0)
    m["burn_t"] = m.tons - (m.stock - m.stock_prev)
    m["contract_over_burn"] = m.c_t / m.burn_t.where(m.burn_t > 0)
    return m.rename(columns={"Plant Id": "plant", "YEAR": "year", "MONTH": "month"})


def night_dispatch(y: int, gen: pd.DataFrame) -> pd.DataFrame:
    """Return per coal plant-month model vs CAMPD-net MWh in the lowest two system-load deciles of year ``y``."""
    u = pd.read_parquet(
        KEEPER / f"unit_marginal_{y}.parquet",
        columns=["pass", "plant_code", "plant_group", "hour", "mw"],
    )
    u = u[(u["pass"] == "P1") & u.plant_group.str.startswith("COAL")]
    s = pd.read_parquet(KEEPER / f"system_{y}.parquet")
    dem = s[s["pass"] == "P1"].groupby("hour").demand.sum().reindex(range(8760))
    night = (pd.qcut(dem, 10, labels=False) <= 1).to_numpy()
    month = pd.date_range(f"{y}-01-01", periods=8760, freq="h").month.to_numpy()
    plants = sorted(u.plant_code.unique())
    model = (
        u.groupby(["plant_code", "hour"])
        .mw.sum()
        .unstack(fill_value=0.0)
        .reindex(columns=range(8760), fill_value=0.0)
    )
    frames = [
        pd.read_parquet(
            f, columns=["facilityId", "date", "hour", "grossLoad", "primaryFuelInfo"]
        )
        for st in STATES
        for f in glob.glob(str(RAW_DATA_DIR / f"campd-unit-level/{st}_{y}.parquet"))
    ]
    c = pd.concat(frames)
    c["facilityId"] = c.facilityId.astype(int)
    c = c[c.facilityId.isin(plants) & c.primaryFuelInfo.str.contains("Coal", na=False)]
    c["h"] = (
        (pd.to_datetime(c.date) - pd.Timestamp(f"{y}-01-01")).dt.days * 24 + c.hour
    ).astype(int)
    c = c[c.h < 8760]
    e = gen[
        (gen.year == y)
        & gen.plant_id.isin(plants)
        & (gen.prime_mover == "ST")
        & gen.fuel_type.isin(COAL_FUELS)
    ]
    k = (
        e.groupby("plant_id").netgen_annual_mwh.sum()
        / c.groupby("facilityId").grossLoad.sum()
    ).clip(0, 2)
    c["net"] = c.grossLoad * c.facilityId.map(k).fillna(0.0)
    act = (
        c.groupby(["facilityId", "h"])
        .net.sum()
        .unstack(fill_value=0.0)
        .reindex(index=plants, columns=range(8760), fill_value=0.0)
    )
    rows = []
    for p in plants:
        mv, av = model.loc[p].to_numpy(), act.loc[p].to_numpy()
        for mo in range(1, 13):
            sel = month == mo
            rows.append(
                dict(
                    plant=p,
                    year=y,
                    month=mo,
                    model_mwh=mv[sel].sum(),
                    actual_mwh=av[sel].sum(),
                    model_night_mwh=mv[sel & night].sum(),
                    actual_night_mwh=av[sel & night].sum(),
                )
            )
    return pd.DataFrame(rows)


def main() -> None:
    """Build the census tables, write them and print the ex-ante readings."""
    gen = pd.read_parquet(
        RAW_DATA_DIR / "_processed-legacy/eia923_monthly_generation.parquet"
    )
    nd = pd.concat(night_dispatch(y, gen) for y in YEARS)
    plants = set(int(p) for p in nd.plant.unique())
    cm = contract_month(read_receipts(plants), read_stocks(plants))
    pm = nd.merge(cm, on=["plant", "year", "month"], how="left")
    pm["night_short_mwh"] = pm.actual_night_mwh - pm.model_night_mwh
    pm.to_csv(OUT / "census_plant_month.csv", index=False)

    py = (
        pm.groupby(["plant", "year"])
        .agg(
            model_twh=("model_mwh", "sum"),
            actual_twh=("actual_mwh", "sum"),
            model_night=("model_night_mwh", "sum"),
            actual_night=("actual_night_mwh", "sum"),
            c_mm=("c_mm", "sum"),
            mm=("mm", "sum"),
            c_t=("c_t", "sum"),
            burn_t=("burn_t", "sum"),
            c_usd=("c_usd", "sum"),
            s_usd=("s_usd", "sum"),
            s_mm=("s_mm", "sum"),
        )
        .reset_index()
    )
    py[["model_twh", "actual_twh"]] /= 1e6
    py["night_short_gwh"] = (py.actual_night - py.model_night) / 1e3
    py["night_short_frac"] = (py.actual_night - py.model_night) / py.actual_night.where(
        py.actual_night > 0
    )
    py["contract_share_mm"] = py.c_mm / py.mm.where(py.mm > 0)
    py["contract_over_burn"] = py.c_t / py.burn_t.where(py.burn_t > 0)
    py["contract_usd"] = py.c_usd / py.c_mm.where(py.c_mm > 0)
    py["spot_usd"] = py.s_usd / py.s_mm.where(py.s_mm > 0)
    py.to_csv(OUT / "census_plant_year.csv", index=False)
    pd.set_option("display.width", 250)
    cols = [
        "plant",
        "year",
        "model_twh",
        "actual_twh",
        "model_night",
        "actual_night",
        "night_short_gwh",
        "night_short_frac",
        "contract_share_mm",
        "contract_over_burn",
        "contract_usd",
        "spot_usd",
    ]
    print(
        py[cols]
        .assign(model_night=py.model_night / 1e3, actual_night=py.actual_night / 1e3)
        .round(3)
        .to_string(index=False)
    )
    print("\nfleet by year (GWh night model/actual):")
    print(
        py.groupby("year")[["model_night", "actual_night"]]
        .sum()
        .div(1e3)
        .round(0)
        .to_string()
    )

    # S1
    q = py[(py.actual_night >= 100e3) & py.contract_share_mm.notna()]
    rho = spearmanr(q.night_short_frac, q.contract_share_mm)
    pos = py[py.night_short_gwh > 0]
    hi = (
        pos[pos.contract_share_mm >= 0.9].night_short_gwh.sum()
        / pos.night_short_gwh.sum()
    )
    print(
        f"\nS1: spearman rho(night_short_frac, contract_share) = {rho.statistic:.3f} (p={rho.pvalue:.3f}, n={len(q)}); "
        f"share of positive night shortfall at contract>=0.9 plants = {hi:.3f}"
    )
    # S2
    cors = []
    for p, g in pm.dropna(subset=["burn_t"]).groupby("plant"):
        g = g[g.year <= 2024]
        if g.c_t.std() > 0 and g.burn_t.std() > 0 and len(g) >= 24:
            cors.append((p, np.corrcoef(g.c_t, g.burn_t)[0, 1]))
    print(
        "S2: within-plant monthly corr(contract tons, burn tons):",
        [(p, round(c, 2)) for p, c in cors],
        f"median {np.median([c for _, c in cors]):.3f}",
    )
    sp = py[py.night_short_gwh > 0]
    print(
        "S2b: shortfall plant-years contract/burn:",
        sp[["plant", "year", "contract_over_burn"]].round(2).values.tolist(),
    )
    # S3
    sm = pm[(pm.night_short_mwh > 0) & pm.headroom_used.notna()]
    w = sm.night_short_mwh
    print(
        f"S3: headroom_used in shortfall plant-months: median {sm.headroom_used.median():.3f}, "
        f"shortfall-weighted mean {np.average(sm.headroom_used, weights=w):.3f}, n={len(sm)}; "
        f"share of shortfall MWh in months with headroom_used>=0.85: {w[sm.headroom_used >= 0.85].sum() / w.sum():.3f}"
    )
    # horizon
    h = pm[pm.c_t > 0]
    print(
        "contract horizon (months to expiration, tonnage-weighted) by year:",
        h.groupby("year")
        .apply(lambda g: np.average(g.months_to_exp.fillna(0), weights=g.c_t))
        .round(1)
        .to_dict(),
    )


if __name__ == "__main__":
    main()
