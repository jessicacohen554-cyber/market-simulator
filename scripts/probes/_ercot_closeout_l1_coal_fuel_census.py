"""Zero-LP L1 census: ERCOT coal plant-month fuel-feasible energy vs the keeper.

Close-out wave 1, step 0b (``docs/backcast-closeout-plan-2026-10.md`` §3.5).
Owner ruling R-3 (2026-10-02, plan §5.0): EIA-923 monthly coal receipts and
month-end stocks are admissible as a backcast fuel-availability overlay — a
per-plant monthly take CEILING (receipts + stock envelope with a declared
``stock_min``), never the burn.

For every keeper coal plant and month of 2019–2024 (2025 has no plant-level
Page 2 stocks yet, ``data/raw/coal-stocks/README.md``) this computes, with
no LP:

* Form A (charter): ``feasible_m = (R_m + S_{m-1} - stock_min) * hc / HR``,
  where ``S_{m-1}`` is the measured month-end stock of the previous month.
* Form B (the LP construction, ``build_coal_monthly_pile`` with measured
  receipts, ceiling only): ``cum_model_burn(m) <= (S_dec(Y-1) - stock_min) * hc
  + cumR_Y(m)``; reports the largest cumulative excess.

``stock_min`` is declared ex ante: arm 0 = zero tons (the codebase's declared
minimum operating stock, ``data/coal_fuel_inventory.py`` module docstring);
arm P = the plant's own minimum measured month-end stock over Y-3..Y-1
(predates Y; a sensitivity reading, never a fitted value).

Model MWh is the keeper's committed per-unit layer
(``results/calibration/<bundle>/hourly/unit_marginal_<Y>.parquet``, P1).
HR is the plant-year coal heat rate from EIA-923 generation-and-fuel
(``elec_fuel_mmbtu / net_generation_mwh`` over coal fuel codes); hc is the
plant-year quantity-weighted receipt heat content.

Usage::

    uv run python scripts/probes/_ercot_closeout_l1_coal_fuel_census.py \
        --bundle results/calibration/r_ercot24_span --out <dir>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw")
COAL_CODES = ("SUB", "LIG", "BIT", "RC", "WC", "SC", "ANT")
YEARS = tuple(range(2019, 2026))


def load_receipts(year: int) -> pd.DataFrame:
    """Return plant-month coal receipts (tons, MMBtu) for ``year``."""
    r = pd.read_csv(RAW / f"coal-receipts/coal_receipts_{year}.csv", low_memory=False)
    r = r[r["FUEL_GROUP"].astype(str).str.lower() == "coal"]
    r = r.assign(
        tons=pd.to_numeric(r["QUANTITY"], errors="coerce").fillna(0.0),
        hc=pd.to_numeric(r["Average Heat Content"], errors="coerce").fillna(0.0),
    )
    r["mmbtu"] = r["tons"] * r["hc"]
    return r.groupby(["Plant Id", "MONTH"], as_index=False)[["tons", "mmbtu"]].sum()


def load_stocks(year: int) -> pd.DataFrame:
    """Return plant x month ending coal stock (tons), wide (columns 1..12)."""
    s = pd.read_csv(RAW / f"coal-stocks/coal_stocks_{year}.csv", low_memory=False)
    s = s[s["Reported Fuel Type Code"].isin(COAL_CODES)]
    months = [c for c in s.columns if c.startswith("Quantity ")]
    v = s[months].apply(pd.to_numeric, errors="coerce")
    v.columns = range(1, 13)
    v["Plant Id"] = s["Plant Id"].to_numpy()
    return v.groupby("Plant Id").sum(min_count=1)


def plant_heat_rate(gf: pd.DataFrame, year: int) -> pd.Series:
    """Plant-year coal heat rate, MMBtu/MWh, from EIA-923 generation-and-fuel."""
    g = gf[(gf["year"] == year) & gf["fuel_type"].isin(COAL_CODES)]
    a = g.groupby("plant_id")[["elec_fuel_mmbtu", "net_generation_mwh"]].sum()
    return (a["elec_fuel_mmbtu"] / a["net_generation_mwh"]).where(
        a["net_generation_mwh"] > 0
    )


def model_plant_month(bundle: Path, year: int) -> pd.DataFrame:
    """Keeper P1 coal MWh per plant-month from the committed per-unit layer."""
    d = pd.read_parquet(
        bundle / f"hourly/unit_marginal_{year}.parquet",
        columns=["pass", "plant_code", "plant_group", "fuel", "hour", "mw"],
    )
    d = d[(d["fuel"] == "coal") & (d["pass"] == "P1")]
    ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(d["hour"], unit="h")
    d = d.assign(month=ts.dt.month.to_numpy())
    out = d.groupby(["plant_code", "plant_group", "month"], observed=True)["mw"].sum()
    return out.rename("model_mwh").reset_index()


def census(bundle: Path) -> pd.DataFrame:
    """Return the plant-month census table over :data:`YEARS`."""
    gf = pd.read_csv(
        RAW / "eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
    )
    stocks = {
        y: load_stocks(y)
        for y in range(min(YEARS) - 3, max(YEARS) + 1)
        if (RAW / f"coal-stocks/coal_stocks_{y}.csv").exists()
    }
    rows = []
    for y in YEARS:
        mod = model_plant_month(bundle, y)
        rec = load_receipts(y)
        hr = plant_heat_rate(gf, y)
        for (pid, grp), m in mod.groupby(["plant_code", "plant_group"], observed=True):
            pid = int(pid)
            if pid == 0:
                continue
            r = (
                rec[rec["Plant Id"] == pid]
                .set_index("MONTH")
                .reindex(range(1, 13))
                .fillna(0.0)
            )
            tons_y = r["tons"].sum()
            hc = r["mmbtu"].sum() / tons_y if tons_y > 0 else np.nan
            s_y = stocks[y].loc[pid] if y in stocks and pid in stocks[y].index else None
            s_prev = stocks.get(y - 1)
            s_dec = (
                float(s_prev.loc[pid, 12])
                if s_prev is not None and pid in s_prev.index
                else np.nan
            )
            prior = [
                stocks[k].loc[pid]
                for k in (y - 3, y - 2, y - 1)
                if k in stocks and pid in stocks[k].index
            ]
            smin_p = (
                float(np.nanmin(pd.concat(prior).to_numpy(dtype=float)))
                if prior
                else np.nan
            )
            mm = m.set_index("month")["model_mwh"].reindex(range(1, 13)).fillna(0.0)
            for mo in range(1, 13):
                s_before = (
                    s_dec
                    if mo == 1
                    else (float(s_y[mo - 1]) if s_y is not None else np.nan)
                )
                rows.append(
                    dict(
                        year=y,
                        plant_id=pid,
                        plant_group=str(grp),
                        month=mo,
                        model_mwh=float(mm[mo]),
                        hr=float(hr.get(pid, np.nan)),
                        hc=hc,
                        receipts_tons=float(r.loc[mo, "tons"]),
                        receipts_mmbtu=float(r.loc[mo, "mmbtu"]),
                        stock_prev_tons=s_before,
                        stock_end_tons=float(s_y[mo]) if s_y is not None else np.nan,
                        stock_dec_prev_tons=s_dec,
                        stock_min_p_tons=smin_p,
                    )
                )
    t = pd.DataFrame(rows)
    for arm, smin in (("0", 0.0), ("P", t["stock_min_p_tons"])):
        env = (t["stock_prev_tons"] - smin).clip(lower=0.0) * t["hc"] + t[
            "receipts_mmbtu"
        ]
        t[f"feasA_{arm}_mwh"] = env / t["hr"]
        t[f"bindA_{arm}"] = t["model_mwh"] > t[f"feasA_{arm}_mwh"] * (1 + 1e-9)
        t[f"excessA_{arm}_mwh"] = (t["model_mwh"] - t[f"feasA_{arm}_mwh"]).clip(
            lower=0.0
        )
        g = t.groupby(["year", "plant_id"])
        cum_burn = g["model_mwh"].cumsum() * t["hr"]
        cum_r = g["receipts_mmbtu"].cumsum()
        open_ = (t["stock_dec_prev_tons"] - smin).clip(lower=0.0) * t["hc"]
        t[f"excessB_{arm}_mwh"] = ((cum_burn - open_ - cum_r) / t["hr"]).clip(lower=0.0)
    # Actual burn identity (provenance only, never an input): R + S_{m-1} - S_m.
    t["actual_mwh_identity"] = (
        t["receipts_mmbtu"] + (t["stock_prev_tons"] - t["stock_end_tons"]) * t["hc"]
    ) / t["hr"]
    return t


def main() -> None:
    """CLI entry point: write the census parquet + JSON summary."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle", type=Path, default=Path("results/calibration/r_ercot24_span")
    )
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    t = census(a.bundle)
    t.to_csv(a.out / "l1_coal_census_plant_month.csv", index=False)
    ann = (
        t.groupby(["year", "plant_id", "plant_group"])
        .agg(
            model_twh=("model_mwh", lambda x: x.sum() / 1e6),
            actual_identity_twh=("actual_mwh_identity", lambda x: x.sum() / 1e6),
            receipts_twh=("receipts_mmbtu", "sum"),
            bindA0_months=("bindA_0", "sum"),
            excessA0_twh=("excessA_0_mwh", lambda x: x.sum() / 1e6),
            bindAP_months=("bindA_P", "sum"),
            excessAP_twh=("excessA_P_mwh", lambda x: x.sum() / 1e6),
            excessB0_max_twh=("excessB_0_mwh", lambda x: x.max() / 1e6),
            excessBP_max_twh=("excessB_P_mwh", lambda x: x.max() / 1e6),
            hr=("hr", "first"),
        )
        .reset_index()
    )
    ann["receipts_twh"] = ann["receipts_twh"] / ann["hr"] / 1e6
    ann.to_csv(a.out / "l1_coal_census_plant_year.csv", index=False)
    print(ann.round(3).to_string())
    binds = t[t["bindA_0"] | t["bindA_P"]][
        [
            "year",
            "plant_id",
            "plant_group",
            "month",
            "model_mwh",
            "feasA_0_mwh",
            "feasA_P_mwh",
            "stock_prev_tons",
            "receipts_tons",
        ]
    ]
    print(binds.round(0).to_string())
    (a.out / "l1_summary.json").write_text(
        json.dumps(
            {
                "bind_plant_months_A0": binds[
                    ["year", "plant_id", "month"]
                ].values.tolist()
            }
        )
    )


if __name__ == "__main__":
    main()
