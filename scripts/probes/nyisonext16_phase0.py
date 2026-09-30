"""NYISO-NEXT-16 phase 0 (ZERO LP): where the 2022 C3b monthly price error sits.

Reads only the keeper's committed bundle (``results/calibration/nyisonext15_span``),
the committed NYISO bench parts, the measured NYISO DA zonal LBMP proxy
(``data/raw/seam-neighbour-price/nyiso``) and the curated ``nyiso-interface-flows``
datatype (run ``scripts/regenerate_clean.py nyiso-interface-flows`` first).

Three blocks, per year:

* ``c3b``: the scorer's monthly load-weighted model vs RT actual, and each month's
  share of the squared error (the C3b NRMSE numerator).
* ``zone_month``: model minus measured-DA zone LW monthly price.
* ``ce_df``: the distribution-factor test of a CENTRAL-EAST-projected cap on the
  Upstate_West -> Capital_Hudson link: ``CE = alpha * TE`` (through-origin OLS on
  measured hourly flows), cap(t) = min(TOTAL EAST envelope, CE posted limit(t) /
  alpha). Reports how often MEASURED TOTAL EAST exceeds that cap (a physical cap
  is rarely exceeded) and whether the measured E->F spread is higher near it.

Usage::

    python3 scripts/probes/nyisonext16_phase0.py [--out <json>]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in ("scripts", "scripts/probes", "scripts/data", "."):
    sys.path.insert(0, str(REPO / p))

import nyisonext13_ch_pricing_phase0 as p13  # noqa: E402
import score_bundle_price_shape as sps  # noqa: E402

from market_sim.config.constants import (  # noqa: E402
    NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH,
)
from scripts.lib.clean_io import read_clean  # noqa: E402

BUNDLE = REPO / "results/calibration/nyisonext15_span"
LINK = ("Upstate_West", "Capital_Hudson")
YEARS = (2022, 2023, 2024, 2025)
p13.BUNDLE = {y: "nyisonext15_span" for y in YEARS}


def _month_of_hour() -> np.ndarray:
    """Hour-of-year (0..8759) -> month 0..11 on the scorer's own month edges."""
    return np.clip(
        np.searchsorted(sps.rch._CUM, np.arange(8760), side="right") - 1, 0, 11
    )


def c3b_block(y: int) -> dict:
    """Monthly model vs actual LW price and each month's squared-error share."""
    z = sps.zone_lmp_block(BUNDLE, y)
    act = sps.bench_year("NYISO", y)["avgLMP"]["rt_lw_mon"]
    mod = [
        sum(v["pMon"][m] * v["dMon"][m] for v in z.values())
        / sum(v["dMon"][m] for v in z.values())
        for m in range(12)
    ]
    se = [(a - b) ** 2 for a, b in zip(mod, act)]
    return {
        "nrmse": round(math.sqrt(sum(se) / 12) / (sum(act) / 12), 3),
        "model": [round(v, 2) for v in mod],
        "actual": [round(v, 2) for v in act],
        "se_share": [round(v / sum(se), 3) for v in se],
    }


def zone_month_block(y: int) -> dict:
    """Model minus measured-DA LW monthly price by model zone."""
    meas, mod = p13.meas_da(y), p13.model_prices(y)
    sy = pd.read_parquet(BUNDLE / "hourly" / f"system_{y}.parquet")
    sy = sy[sy["pass"] == "P1"]
    dem = sy.pivot_table(index="hour", columns="zone", values="demand").reindex(
        range(8760)
    )
    mon = _month_of_hour()
    out = {}
    for z, cols in p13.MODEL_TO_MEAS.items():
        w, pm = dem[z].to_numpy(), mod[z].to_numpy()
        pa = meas[list(cols)].mean(axis=1).to_numpy()
        row = []
        for m in range(12):
            s = (mon == m) & np.isfinite(pa)
            row.append(round(float(((pm[s] - pa[s]) * w[s]).sum() / w[s].sum()), 2))
        out[z] = row
    return out


def ce_df_block(y: int) -> dict:
    """Distribution-factor projection of the posted CE limit onto the link."""
    f = read_clean("nyiso-interface-flows", iso="NYISO", year=y)
    f["lh"] = pd.to_datetime(f.interval_start_local).dt.floor("h")
    f = f[f.interface.isin(["TOTAL EAST", "CENTRAL EAST - VC"])]
    g = (
        f.groupby(["lh", "interface"])
        .agg(fl=("flow_mw", "mean"), lim=("positive_limit_mw", "mean"))
        .unstack()
        .dropna(
            subset=[
                ("fl", "TOTAL EAST"),
                ("fl", "CENTRAL EAST - VC"),
                ("lim", "CENTRAL EAST - VC"),
            ]
        )
    )
    g = g[g.index.year == y]
    te = g[("fl", "TOTAL EAST")].to_numpy()
    ce = g[("fl", "CENTRAL EAST - VC")].to_numpy()
    cel = g[("lim", "CENTRAL EAST - VC")].to_numpy()
    mon = g.index.month.to_numpy()
    env = np.asarray(NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH[y][LINK])[mon - 1]
    alpha = float((te * ce).sum() / (te * te).sum())
    cap = np.minimum(env, cel / alpha)
    meas = p13.meas_da(y)
    spread = meas["CAPITL"].to_numpy() - meas["MHK VL"].to_numpy()
    hoy = (
        ((g.index - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h"))
        .astype(int)
        .to_numpy()
    )
    ok = (hoy >= 0) & (hoy < 8760)
    sp = np.full(len(g), np.nan)
    sp[ok] = spread[hoy[ok]]
    near = te >= 0.95 * cap
    ratio = ce / cel
    return {
        "alpha": round(alpha, 3),
        "meas_te_above_envelope_pct": round(float(np.mean(te > env + 1)) * 100, 1),
        "meas_te_above_df_cap_pct": round(float(np.mean(te > cap + 1)) * 100, 1),
        "df_cap_below_envelope_pct": round(float(np.mean(cap < env)) * 100, 1),
        "ef_spread_near_cap": round(float(np.nanmean(sp[near])), 2),
        "ef_spread_elsewhere": round(float(np.nanmean(sp[~near])), 2),
        "ce_flow_ge_085_posted_pct": round(float(np.mean(ratio >= 0.85)) * 100, 1),
        "ef_spread_ce_ge_085": round(float(np.nanmean(sp[ratio >= 0.85])), 2),
        "ef_spread_ce_lt_070": round(float(np.nanmean(sp[ratio < 0.70])), 2),
        "ce_posted_limit_monthly": [
            round(float(cel[mon == m].mean())) for m in range(1, 13)
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/_nyisonext16_phase0.json")
    )
    a = ap.parse_args(argv)
    rec = {
        str(y): {"c3b": c3b_block(y), "zone_month": zone_month_block(y)} for y in YEARS
    }
    for y in (2021, *YEARS):
        rec.setdefault(str(y), {})["ce_df"] = ce_df_block(y)
    Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    for y, r in rec.items():
        if "c3b" in r:
            print(y, "C3b", r["c3b"]["nrmse"], "se_share", r["c3b"]["se_share"])
        print(y, "ce_df", r["ce_df"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
