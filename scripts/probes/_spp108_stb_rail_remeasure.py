"""SPP-108 step 3 probe: re-measure SPP-44 on the STB EP 724 PRB unit-train loadings-vs-plan series (zero LP).

Close-out plan §3.4 step 3. SPP-44 (2026-09-16) killed the coal-deliverability lever because EIA-923 tonnage puts
2022 *inside* the other years' range while the MMU coal markup has 2022 at 3.07x every other year, and named the
missing instrument: a delivery-reliability / rail-performance series. STB EP 724 Category 9 (weekly coal unit-train
loadings vs the carrier's own plan, by production region) is that series. This probe asks three questions:

1. **Identification** — is the PRB loadings/plan ratio anomalous in 2022 and *not* in 2021, against a reference that
   is built only from years <= Y-1 (rule 13; the two-year window of ``coal_receipts.prior_years_delivery_rate``)?
2. **Does a zero-parameter mechanism keyed to it bind?** The RR502 opportunity-cost offer is the shadow value of an
   energy limit. Its zero-parameter physical form is a cumulative inventory: opening stock (prior December, EIA-923
   Page 2) + lagged deliveries (prior two years, EIA-923 Page 5) scaled month by month by the STB anomaly, never below
   zero, against the keeper's own monthly PRB burn. A bind is where an adder would be non-zero.
3. **Where** — per year, including 2019 and the train tier 2023-25 (a bind there would move 2025 PRB / C3a).

Reads ``data/raw/stb-ep724/`` (the consolidated EP 724 workbook), ``data/raw/coal-{receipts,stocks}``, the keeper's
committed ``hourly/class_hourly_<Y>.parquet`` and its EIA-923 benchmark frame. Writes
``results/phase0/spp/_spp108_stb_rail_remeasure.json`` and prints the tables.

Run: ``uv run python scripts/probes/_spp108_stb_rail_remeasure.py`` (~1 min).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts/probes"))
import _spp87_benchmark_reconcile as s87  # noqa: E402
from market_sim.data.stb_ep724 import load_coal_loadings  # noqa: E402

BUNDLE = REPO / "results/calibration/spp107EXR_span"
OUT = REPO / "results/phase0/spp/_spp108_stb_rail_remeasure.json"
YEARS = range(2019, 2026)
CARRIERS = ("BNSF", "UP")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December")
REF_YEARS = 2  # coal_receipts.prior_years_delivery_rate default window
MMU_MARKUP = {2021: 6.02, 2022: 21.12, 2023: 6.88, 2024: 4.29, 2025: 5.81}  # SPP-44 §3 (SPP MMU ASOM)


def prb_series() -> pd.DataFrame:
    """Weekly PRB loadings plan and actual, BNSF + UP summed, indexed by week-ending date."""
    d = load_coal_loadings()
    d = d[d.carrier.isin(CARRIERS) & (d.region == "Powder River Basin")]
    return d.pivot_table(index="week", columns="measure", values="value", aggfunc="sum").dropna().sort_index()


def anomaly(w: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Annual loadings/plan ratio and the monthly anomaly vs the mean of the prior ``REF_YEARS`` annual ratios."""
    yr = w.groupby(w.index.year)[["actual", "plan"]].sum()
    yr["ratio"] = yr.actual / yr.plan
    yr["ref"] = yr.ratio.shift(1).rolling(REF_YEARS).mean()
    yr["anomaly"] = yr.ratio / yr.ref
    mo = w.groupby([w.index.year, w.index.month])[["actual", "plan"]].sum()
    mo["ratio"] = mo.actual / mo.plan
    mo["anomaly"] = [r / yr.ref.get(y, np.nan) for (y, _), r in mo.ratio.items()]
    return yr, mo["anomaly"]


def receipts_pm(year: int, ids: set[int]) -> pd.DataFrame:
    """Monthly coal receipts (short tons), plant x month, for ``ids`` in ``year``."""
    r = pd.read_csv(REPO / f"data/raw/coal-receipts/coal_receipts_{year}.csv", low_memory=False)
    r = r[(r.FUEL_GROUP == "Coal") & r["Plant Id"].isin(ids)]
    t = r.pivot_table(index="Plant Id", columns="MONTH", values="QUANTITY", aggfunc="sum")
    return t.reindex(index=sorted(ids), columns=range(1, 13)).fillna(0.0)


def stocks_pm(year: int, ids: set[int]) -> pd.DataFrame:
    """Month-end coal stocks (short tons), plant x month, for ``ids`` in ``year``."""
    s = pd.read_csv(REPO / f"data/raw/coal-stocks/coal_stocks_{year}.csv", low_memory=False)
    s = s[(s["AER Fuel Type Code"] == "COL") & s["Plant Id"].isin(ids)]
    q = s.groupby("Plant Id")[[f"Quantity {m}" for m in MONTHS]].sum().apply(pd.to_numeric, errors="coerce")
    q.columns = range(1, 13)
    return q.reindex(sorted(ids)).fillna(0.0)


def receipts(year: int, ids: set[int]) -> pd.Series:
    """Monthly coal receipts (short tons) to ``ids`` in ``year``, fleet sum."""
    return receipts_pm(year, ids).sum()


def stocks(year: int, ids: set[int]) -> pd.Series:
    """Month-end coal stocks (short tons) at ``ids`` in ``year``, fleet sum."""
    return stocks_pm(year, ids).sum()


def model_plant_monthly_mwh(year: int, ids: set[int]) -> pd.DataFrame:
    """Keeper's monthly coal MWh by plant (plant x month) from the committed unit_marginal sidecar."""
    d = pd.read_parquet(
        BUNDLE / f"hourly/unit_marginal_{year}.parquet", columns=["pass", "plant_code", "fuel", "hour", "mw"]
    )
    d = d[(d["pass"] == "P1") & d.plant_code.isin(ids) & d.fuel.astype(str).str.upper().str.startswith("COAL")]
    d["month"] = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(d.hour, unit="h")).dt.month
    t = d.pivot_table(index="plant_code", columns="month", values="mw", aggfunc="sum")
    return t.reindex(index=sorted(ids), columns=range(1, 13)).fillna(0.0)


def plant_leg(y: int, ids: set[int], frame: pd.DataFrame, an: pd.Series, basis: str) -> dict:
    """Per-plant cumulative inventory (stock >= 0) with STB-scaled lagged deliveries vs the keeper's plant burn."""
    s1, s2 = stocks_pm(y - 1, ids), stocks_pm(y - 2, ids)
    opening = s1[12]
    lag = sum(receipts_pm(y - k, ids) for k in range(1, REF_YEARS + 1)) / REF_YEARS
    burn_prev = receipts_pm(y - 1, ids).sum(axis=1) - (s1[12] - s2[12])
    mwh_prev = frame[(frame.year == y - 1) & frame.plant_id.isin(ids)].groupby("plant_id").annual_mwh.sum()
    if basis == "gross":
        # The model's coal is on the CEMS-gross basis (SPP-87), so convert its MWh at tons per Y-1 gross MWh;
        # a plant with no CEMS series (River Valley 10671) keeps its net denominator.
        g = s87.cems_coal(y - 1, ids).groupby("facilityId").mwh.sum()
        mwh_prev = g.reindex(mwh_prev.index).where(lambda v: v > 0).fillna(mwh_prev)
    tpm = (burn_prev / mwh_prev.reindex(burn_prev.index)).where(lambda v: (v > 0.3) & (v < 1.5))
    mwh = model_plant_monthly_mwh(y, ids)
    out = {}
    for name, scale in (("lagged_only", pd.Series(1.0, index=an.index)), ("stb_scaled", an.clip(upper=1.0))):
        tons = mwh.mul(tpm, axis=0)
        path = opening.to_frame().values + (lag.mul(scale, axis=1) - tons).cumsum(axis=1)
        ok = tpm.notna() & (mwh.sum(axis=1) > 0)
        p = path[ok]
        deficit_t = (-p.min(axis=1)).clip(lower=0.0)
        out[name] = {
            "plants_scored": int(ok.sum()),
            "plants_binding": int((deficit_t > 0).sum()),
            "binding_plants": {int(k): round(float(v) / 1e6, 3) for k, v in deficit_t[deficit_t > 0].items()},
            "deficit_twh": round(float((deficit_t / tpm[ok]).sum()) / 1e6, 3),
            "model_coal_twh_scored": round(float(mwh[ok].sum().sum()) / 1e6, 3),
        }
    return out


def model_monthly_mwh(year: int) -> pd.Series:
    """Keeper's monthly COAL_PRB MWh from the committed class_hourly sidecar."""
    d = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    d = d[(d.klass == "COAL_PRB") & (d["pass"] == "P1")].sort_values("hour")
    ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(d.hour.values, unit="h")
    return pd.Series(d.mw.values, index=ts).groupby(lambda t: t.month).sum()


def main() -> None:
    """Run the three legs and write the JSON record."""
    meta = json.loads((BUNDLE / "meta.json").read_text())
    frame = pd.read_parquet((BUNDLE / meta["shared_inputs"]["eia923"]).resolve())
    w = prb_series()
    yr, mo_anom = anomaly(w)
    rec: dict = {"annual": {}, "identification": {}, "inventory": {}}
    for y, r in yr.iterrows():
        rec["annual"][int(y)] = {k: round(float(v), 4) for k, v in r.items() if pd.notna(v)}

    # Leg 1: identification against the MMU markup (SPP-44's test, same five years).
    a = {y: float(yr.anomaly[y]) for y in MMU_MARKUP}
    others = [v for y, v in a.items() if y != 2022]
    from scipy.stats import spearmanr

    rho = spearmanr([a[y] for y in MMU_MARKUP], [MMU_MARKUP[y] for y in MMU_MARKUP]).statistic
    rec["identification"] = {
        "anomaly_by_year": {y: round(v, 4) for y, v in a.items()},
        "anomaly_2022": round(a[2022], 4),
        "others_range": [round(min(others), 4), round(max(others), 4)],
        "outside": bool(a[2022] < min(others)),
        "spearman_vs_mmu": round(float(rho), 3),
    }

    # Leg 2/3: cumulative inventory with STB-scaled lagged deliveries vs the keeper's PRB burn.
    for y in YEARS:
        ids = set(frame[(frame.year == y) & (frame.klass == "COAL_PRB")].plant_id.astype(int))
        s_prev = stocks(y - 1, ids) if (REPO / f"data/raw/coal-stocks/coal_stocks_{y - 1}.csv").exists() else None
        if s_prev is None:
            rec["inventory"][y] = {"skipped": "no prior-December stock on disk"}
            continue
        opening = float(s_prev[12])
        lag = pd.concat([receipts(y - k, ids) for k in range(1, REF_YEARS + 1)], axis=1).mean(axis=1)
        # Tons per net MWh of the same plants in Y-1: burn = receipts - change in stock.
        s_pp = stocks(y - 2, ids)[12] if (REPO / f"data/raw/coal-stocks/coal_stocks_{y - 2}.csv").exists() else np.nan
        burn_prev = receipts(y - 1, ids).sum() - (s_prev[12] - s_pp)
        mwh_prev = frame[(frame.year == y - 1) & frame.plant_id.isin(ids)].annual_mwh.sum()
        tpm = float(burn_prev / mwh_prev) if np.isfinite(burn_prev) else np.nan
        m_mwh = model_monthly_mwh(y)
        m_tons = m_mwh * tpm
        an = pd.Series([mo_anom.get((y, m), np.nan) for m in range(1, 13)], index=range(1, 13)).fillna(1.0)
        legs = {}
        for name, scale in (("lagged_only", pd.Series(1.0, index=an.index)), ("stb_scaled", an.clip(upper=1.0))):
            deliv = lag * scale
            path = opening + (deliv - m_tons).cumsum()
            deficit = float(-path.min()) if path.min() < 0 else 0.0
            legs[name] = {
                "deliveries_mt": round(float(deliv.sum()) / 1e6, 3),
                "min_stock_mt": round(float(path.min()) / 1e6, 3),
                "min_stock_days": round(float(path.min() / (m_tons.sum() / 365)), 1),
                "bind_months": int((path < 0).sum()),
                "first_bind_month": int(path[path < 0].index.min()) if (path < 0).any() else None,
                "deficit_mt": round(deficit / 1e6, 3),
                "deficit_twh": round(deficit / tpm / 1e6, 3),
            }
        has = (REPO / f"data/raw/coal-stocks/coal_stocks_{y - 2}.csv").exists()
        per_plant = {b: plant_leg(y, ids, frame, an, b) for b in ("net", "gross")} if has else None
        actual = stocks(y, ids) if (REPO / f"data/raw/coal-stocks/coal_stocks_{y}.csv").exists() else None
        rec["inventory"][y] = {
            "plants": len(ids),
            "opening_mt": round(opening / 1e6, 3),
            "lagged_deliveries_mt": round(float(lag.sum()) / 1e6, 3),
            "tons_per_mwh_prev": round(tpm, 4),
            "model_prb_twh": round(float(m_mwh.sum()) / 1e6, 3),
            "model_burn_mt": round(float(m_tons.sum()) / 1e6, 3),
            "annual_anomaly": round(float(yr.anomaly.get(y, np.nan)), 4),
            "min_month_anomaly": round(float(an.min()), 4),
            **legs,
            "per_plant": per_plant,
            # Forbidden comparator (rule 13): the year's own measured stock path, reported, never an input.
            "forbidden_actual_min_stock_mt": None if actual is None else round(float(actual.min()) / 1e6, 3),
            "forbidden_actual_dec_stock_mt": None if actual is None else round(float(actual[12]) / 1e6, 3),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1, default=float))
    print(json.dumps(rec, indent=1, default=float))


if __name__ == "__main__":
    main()
