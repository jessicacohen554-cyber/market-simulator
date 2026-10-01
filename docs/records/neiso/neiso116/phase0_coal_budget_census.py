"""neiso-116 phase 0 (zero LP): would a NEISO coal fuel-inventory budget bind on the keeper?

For each NEISO coal yard and year, compares the fuel the KEEPER's own P1
dispatch burns (per-unit MW x the unit's LP heat rate, from the G-DRIFT
``fleet_only`` dump of the keeper recipe) against the budget the existing
``coal_fuel_inventory`` / ``coal_fuel_inventory_plant_grain`` construction
would size from EIA-923 (Page 2 stocks, Page 5 receipts):

    budget_Y = (Dec(Y-1) ending stock + mean receipts over Y-2, Y-1) x heat content

Every sizing quantity predates the solved year (rule 13 [R-MEASURED]); year
Y's own receipts and stock path are never read. Also reports the pooled
MONTHLY limb (annual / 12 per month over the pooled footprint), because
``coal_fuel_inventory_plant_grain`` cannot be armed without it.

Read-only. Inputs: the keeper bundle's ``dispatch/<Y>_P1.parquet`` (recomposed
from the neiso-115 legs, gitignored), the G-DRIFT dumps ``<dump>/<tag>_<Y>.npz``
written by ``docs/handoffs/neiso114/gdrift_fleet_probe.py``, and the raw
``data/raw/coal-{stocks,receipts}`` CSVs.

Usage::

    uv run python docs/handoffs/neiso116/phase0_coal_budget_census.py \\
        --bundle results/calibration/neiso114b_span --dump <dir> --tag basis
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "raw"
YEARS = list(range(2019, 2026))
N_RATE_YEARS = 2  # the coal_fuel_inventory default (owner ruling 2026-09-16, MISO)


def _stocks(year: int) -> pd.DataFrame:
    """Return EIA-923 Page 2 coal stocks for ``year`` (empty if not published)."""
    p = RAW / "coal-stocks" / f"coal_stocks_{year}.csv"
    return pd.read_csv(p, low_memory=False) if p.exists() else pd.DataFrame()


def _receipts(year: int) -> pd.DataFrame:
    """Return EIA-923 Page 5 coal receipts for ``year`` (empty if not published)."""
    p = RAW / "coal-receipts" / f"coal_receipts_{year}.csv"
    return pd.read_csv(p, low_memory=False) if p.exists() else pd.DataFrame()


def fleet_heat_content(plants: list[int], year: int) -> float:
    """Return the covered fleet's quantity-weighted prior-window heat content.

    The fallback ``build_coal_plant_budget`` applies to a yard that holds stock
    but received nothing in the rate window.
    """
    tons = mmbtu = 0.0
    for y in range(year - N_RATE_YEARS, year):
        rc = _receipts(y)
        if rc.empty:
            continue
        r = rc[rc["Plant Id"].isin(plants)]
        tons += float(r["QUANTITY"].sum())
        mmbtu += float((r["QUANTITY"] * r["Average Heat Content"]).sum())
    return mmbtu / tons if tons > 0 else float("nan")


def yard_budget_mmbtu(
    plant: int, year: int, fleet_hc: float = float("nan")
) -> tuple[float | None, dict]:
    """Return the plant-grain annual budget (MMBtu) and its inputs, or None."""
    st = _stocks(year - 1)
    dec = None
    if not st.empty and plant in set(st["Plant Id"]):
        dec = float(
            pd.to_numeric(
                st.loc[st["Plant Id"] == plant, "Quantity December"], errors="coerce"
            ).sum()
        )
    tons = mmbtu = 0.0
    filed = dec is not None
    for y in range(year - N_RATE_YEARS, year):
        rc = _receipts(y)
        if rc.empty:
            continue
        r = rc[rc["Plant Id"] == plant]
        if not r.empty:
            filed = True
        tons += float(r["QUANTITY"].sum())
        mmbtu += float((r["QUANTITY"] * r["Average Heat Content"]).sum())
    if not filed:
        return None, {}
    rate = tons / N_RATE_YEARS
    hc = mmbtu / tons if tons > 0 else fleet_hc
    info = {"dec_stock_t": dec, "rate_t_yr": rate, "hc_mmbtu_t": hc}
    if not (dec or rate):
        return 0.0, info  # filed, and reported zero: a zero budget
    if not np.isfinite(hc):
        return None, info
    return ((dec or 0.0) + rate) * hc, info


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--tag", default="basis")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()
    bundle = Path(args.bundle)
    out: list[dict] = []
    for year in YEARS:
        z = np.load(Path(args.dump) / f"{args.tag}_{year}.npz", allow_pickle=True)
        hr = dict(zip(z["unit_ids"].tolist(), z["heat_rate"].tolist()))
        d = pd.read_parquet(
            bundle / "dispatch" / f"{year}_P1.parquet",
            columns=["unit_id", "plant_code", "klass", "hour", "mw"],
        )
        d = d[d["klass"].str.startswith("COAL")]
        d = d.assign(mmbtu=d["mw"] * d["unit_id"].map(hr).astype(float))
        month = pd.to_datetime(f"{year}-01-01") + pd.to_timedelta(d["hour"], unit="h")
        d = d.assign(month=month.dt.month)
        pooled_budget = 0.0
        fhc = fleet_heat_content(sorted(int(p) for p in d["plant_code"].unique()), year)
        for plant, g in d.groupby("plant_code"):
            budget, info = yard_budget_mmbtu(int(plant), year, fhc)
            twh = g["mw"].sum() / 1e6
            burn = g["mmbtu"].sum()
            wavg_hr = burn / g["mw"].sum() if g["mw"].sum() > 0 else float("nan")
            if budget is not None:
                pooled_budget += budget
            out.append(
                {
                    "year": year,
                    "plant": int(plant),
                    "klass": ",".join(sorted(set(g["klass"]))),
                    "model_twh": round(twh, 3),
                    "model_tbtu": round(burn / 1e6, 3),
                    "hr": round(wavg_hr, 3),
                    "budget_tbtu": None if budget is None else round(budget / 1e6, 3),
                    "budget_twh_at_hr": None
                    if budget is None or not np.isfinite(wavg_hr)
                    else round(budget / wavg_hr / 1e6, 3),
                    "cut_twh_annual": None
                    if budget is None or not np.isfinite(wavg_hr)
                    else round(max(0.0, burn - budget) / wavg_hr / 1e6, 3),
                    **info,
                }
            )
        mburn = d.groupby("month")["mmbtu"].sum()
        mcap = pooled_budget / 12.0
        over = (mburn - mcap).clip(lower=0.0)
        out.append(
            {
                "year": year,
                "plant": "POOLED_MONTHLY",
                "model_tbtu": round(float(mburn.sum()) / 1e6, 3),
                "budget_tbtu": round(pooled_budget / 1e6, 3),
                "monthly_cap_tbtu": round(mcap / 1e6, 3),
                "months_binding": int((over > 0).sum()),
                "excess_tbtu_over_monthly_caps": round(float(over.sum()) / 1e6, 3),
            }
        )
    df = pd.DataFrame(out)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(df.to_string(index=False))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=1, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
