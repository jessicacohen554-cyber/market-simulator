"""ERCOT-161 Phase 0 addendum — the DISPATCHED-segment census at the gap hours.

The main probe (``ercot161_afternoon_wall_phase0.py``) measured that at the
top-100 gap hours the ON-status merchant gas SPARE (Base Point -> HASL) is
~0.45 GW of residue whose price distribution is statistically indistinguishable
from ordinary bin-6 hours (CC p90 197x vs 194x gas) and uncorrelated with the
cleared lambda (-0.10) — the wall's measured population does NOT carry the
scarcity signal. The implied mechanism: at those hours SCED had dispatched
THROUGH the hockey-stick tops, so the $500-3,000 conduct sits in the
DISPATCHED portion of the SCED2 curves (LSL -> Base Point), which the
spare-basis derive never samples.

This census verifies that directly, on the same corpus and clock:

* per class (CC/CT, the wall's own scope) at the top-100 gap hours and at the
  bin-6-rest contrast hours: MW-weighted quantiles of the ABOVE-LSL dispatched
  segment prices (effective-HR multipliers), the MW dispatched at >= $300 /
  $500 / $1,000 / $2,000, and the per-interval MAX dispatched price;
* the same for the full curve (dispatched + spare = LSL -> HASL) — the
  position-consistent population a repaired ladder would be measured on;
* the per-hour agreement between the highest dispatched segment price and
  ERCOT's published system lambda (NP6-905-CD) — the SCED-optimality
  cross-check that the dispatched-top, not the spare, is what formed lambda.

NO LP, no solve, no mechanism armed. Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot161_dispatched_segment_census.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DEFAULT_OUT = REPO / "results/calibration/_ercot161_dispatched_census.json"
PHASE0_JSON = REPO / "results/calibration/_ercot161_wall_phase0.json"
YEAR = 2023

#: Price thresholds ($/MWh) for the dispatched-MW census.
USD_RUNGS = (300.0, 500.0, 1000.0, 2000.0)

#: Reported quantiles (MW-weighted) of segment prices.
QUANTS = (0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99)


def _segments(
    df: pd.DataFrame, lo_col: str, hi_col: str
) -> pd.DataFrame:
    """(lo, hi]-bounded SCED2 curve segments, one row per (interval, step).

    The derive's ``_spare_segments`` construction generalized to any
    [lo, hi] window of the curve: ``lo=LSL, hi=Base Point`` yields the
    above-LSL DISPATCHED portion; ``lo=LSL, hi=HASL`` the full offered curve;
    ``lo=Base Point, hi=HASL`` reproduces the spare (cross-checked against the
    main probe).
    """
    from derive_ercot_sced_offer_wall import _SCED2_MW, _SCED2_PR
    from derive_ercot_dam_cleared_share import HCAP_USD_MWH

    MW = df[_SCED2_MW].to_numpy(float)
    PR = df[_SCED2_PR].to_numpy(float)
    lo = np.maximum(df[lo_col].to_numpy(float), 0.0)
    hi = df[hi_col].to_numpy(float)
    hoy = df["hoy"].to_numpy(int)
    ts = df["_ts_key"].to_numpy()
    cls_vals = df["cls"].to_numpy()
    gas = df["gas_day"].to_numpy(float)

    seg = {k: [] for k in ("hoy", "mw", "price", "ts", "cls", "gas")}
    prev = lo.copy()
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        cap = np.minimum(q, hi)
        mw = np.where(valid, np.maximum(cap - np.maximum(prev, lo), 0.0), 0.0)
        take = mw > 0
        if take.any():
            seg["hoy"].append(hoy[take])
            seg["mw"].append(mw[take])
            seg["price"].append(np.minimum(p[take], HCAP_USD_MWH))
            seg["ts"].append(ts[take])
            seg["cls"].append(cls_vals[take])
            seg["gas"].append(gas[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    if not seg["mw"]:
        return pd.DataFrame(columns=list(seg))
    return pd.DataFrame({k: np.concatenate(v) for k, v in seg.items()})


def _ladder(sub: pd.DataFrame) -> dict:
    """MW-weighted multiplier quantiles + USD-rung MW census for one hour set."""
    from derive_ercot_sced_offer_wall import _weighted_quantiles

    out = {}
    for cls, grp in sub.groupby("cls"):
        mult = (grp["price"] / grp["gas"]).to_numpy(float)
        mw = grp["mw"].to_numpy(float)
        qs = _weighted_quantiles(mult, mw, QUANTS)
        n_iv = grp["ts"].nunique()
        per_iv_mw = grp.groupby("ts")["mw"].sum()
        rungs = {}
        for r in USD_RUNGS:
            m = grp[grp["price"] >= r]
            rungs[f"gw_ge_{int(r)}"] = round(
                float(m.groupby("ts")["mw"].sum().reindex(per_iv_mw.index).fillna(0.0).mean() / 1e3),
                3,
            )
        out[cls] = {
            "mult_quantiles": {
                f"p{int(q * 100)}": round(float(v), 2) for q, v in zip(QUANTS, qs)
            },
            "max_mult": round(float(mult.max()), 2),
            "n_intervals": int(n_iv),
            "n_hours": int(grp["hoy"].nunique()),
            "mean_gw": round(float(per_iv_mw.mean() / 1e3), 3),
            "mean_gw_at_usd_rungs": rungs,
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    from derive_ercot_dam_cleared_share import (
        _MONTH_START_HOUR,
        _gas_day_series,
        _netload_pct,
    )
    from derive_ercot_sced_offer_wall import (
        CLASS_OF_RESTYPE,
        NETLOAD_PCT_EDGES,
        _READ_COLS,
        _coerce_sced_numeric,
        _delivery_year_rows,
        _sced_source_files,
    )

    read_cols = list(_READ_COLS) + ["LSL"]

    phase0 = json.loads(PHASE0_JSON.read_text())
    top = set(int(h) for h in phase0["hour_set"]["hours"])
    pct = _netload_pct(YEAR)
    eb = np.searchsorted(np.asarray(NETLOAD_PCT_EDGES), pct, side="right")
    bin6_rest = set(int(h) for h in np.where(eb == 6)[0]) - top
    keep_hours = top | bin6_rest
    gas_day = _gas_day_series()

    disp_acc: list[pd.DataFrame] = []
    full_acc: list[pd.DataFrame] = []
    n_files = 0
    for path in _sced_source_files(YEAR):
        df = pd.read_parquet(path, columns=read_cols)
        df = _delivery_year_rows(df, YEAR)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = _coerce_sced_numeric(df[stat.str.startswith("ON")].copy())
        n_files += 1
        if df.empty:
            continue
        ts = pd.to_datetime(df["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert("Etc/GMT+6")
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))
        df = df.loc[np.asarray(ok)].copy()
        if df.empty:
            continue
        df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        df = df[df["hoy"].isin(keep_hours)]
        if df.empty:
            continue
        df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
        df["_ts_key"] = df["SCED Time Stamp"].to_numpy()
        # ``cst`` keeps the pre-filter index, so a label-aligned .loc recovers
        # each surviving row's delivery date (the derive's own normalizer).
        dates = cst.dt.normalize().dt.tz_localize(None).loc[df.index]
        df["gas_day"] = gas_day.reindex(pd.DatetimeIndex(dates)).to_numpy(float)
        df = df[df["gas_day"] > 0]
        if df.empty:
            continue
        disp_acc.append(_segments(df, "LSL", "Base Point"))
        full_acc.append(_segments(df, "LSL", "HASL"))

    disp = pd.concat([d for d in disp_acc if not d.empty], ignore_index=True)
    full = pd.concat([d for d in full_acc if not d.empty], ignore_index=True)

    lam = (
        pd.read_parquet(REPO / f"data/raw/ercot/ercot_{YEAR}_ordc_reserves_hourly.parquet")
        .set_index("hour")["system_lambda"]
        .reindex(range(8760))
        .to_numpy(float)
    )

    # per-gap-hour: highest dispatched segment price vs lambda
    from derive_ercot_sced_offer_wall import _weighted_quantiles

    per_hour = []
    gap_disp = disp[disp["hoy"].isin(top)]
    for hoy, grp in gap_disp.groupby("hoy"):
        p99 = _weighted_quantiles(
            grp["price"].to_numpy(float), grp["mw"].to_numpy(float), (0.99,)
        )[0]
        per_hour.append(
            {
                "hoy": int(hoy),
                "max_dispatched_usd": round(float(grp["price"].max()), 1),
                "p99_dispatched_usd": round(float(p99), 1),
                "lambda_usd": round(float(lam[hoy]), 1) if np.isfinite(lam[hoy]) else None,
            }
        )
    ph = pd.DataFrame(per_hour)
    ratio = (
        (ph["max_dispatched_usd"] / ph["lambda_usd"])
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot161_dispatched_segment_census.py",
            "session": "ercot-161 Phase 0 addendum (no LP, no solve)",
            "population": (
                "ON-status merchant gas (CCGT90/CCLE90/SCGT90/SCLE90) SCED2 "
                "curve segments; dispatched = (LSL, Base Point]; full = "
                "(LSL, HASL]; same corpus/clock/gas normalizer as "
                "derive_ercot_sced_offer_wall"
            ),
            "n_files_read": n_files,
        },
        "dispatched": {
            "gap_hours": _ladder(disp[disp["hoy"].isin(top)]),
            "bin6_rest": _ladder(disp[disp["hoy"].isin(bin6_rest)]),
        },
        "full_curve": {
            "gap_hours": _ladder(full[full["hoy"].isin(top)]),
            "bin6_rest": _ladder(full[full["hoy"].isin(bin6_rest)]),
        },
        "per_hour_gap": per_hour,
        "max_dispatched_over_lambda": {
            "p25": round(float(ratio.quantile(0.25)), 3),
            "p50": round(float(ratio.quantile(0.50)), 3),
            "p75": round(float(ratio.quantile(0.75)), 3),
            "n": int(len(ratio)),
        },
    }
    args.out.write_text(json.dumps(out, indent=1))
    for pop in ("dispatched", "full_curve"):
        for hs in ("gap_hours", "bin6_rest"):
            for cls, r in out[pop][hs].items():
                print(
                    f"[{pop}|{hs}] {cls}: {r['mult_quantiles']} "
                    f"mean {r['mean_gw']} GW; >=$500 {r['mean_gw_at_usd_rungs']['gw_ge_500']} GW; "
                    f">=$1000 {r['mean_gw_at_usd_rungs']['gw_ge_1000']} GW"
                )
    print(f"max-dispatched/lambda p25/p50/p75: {out['max_dispatched_over_lambda']}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
