"""nyiso-248 phase 0 — WHERE DOES THE MEASURED TRANSCO Z6 DAILY SWING GO?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Gate **G-2**.

G-1 (``nyiso248_gas_grain_census.py``) falsified the lane's opening premise:
100 % of NYISO gas capacity already carries a DAILY delivered-gas series, and
``_nyiso_hub_daily_gas_prices`` already takes its within-month shape from the
MEASURED Transco Z6 NY daily quotes, mean-preserving, on their true calendar
days. So the object is NOT grain and NOT the source series.

What remains testable is **AMPLITUDE**. The keeper's delivered gas tops out at
~2.6x its own median where the measured Transco Z6 daily tops out at ~15x. If
the shape leg is exactly mean-preserving and multiplicative, relative dispersion
should SURVIVE. This gate measures, stage by stage, how much of the measured
swing reaches the array the LP actually prices on, and names the stage that
removes it.

The comparator is deliberately LEVEL-FREE, so nothing here can be confused with
a level claim (rules 1 / 14, and the lane's own level-vs-shape guard):

* **within-month CV** — for each month, std/mean of the CALENDAR-DAY series
  inside that month; reported as the mean over the 12 months. A flat month
  reads 0. Two series with different levels but the same relative shape read
  the SAME CV.
* **p95/p50 ratio within month** — the same idea at the tail rather than the
  centre, averaged over months.

Stages compared, per year:

1. ``transco_raw``      — the measured Transco Z6 NY daily prints, on calendar
                          days, gaps held flat (the staircase the source is).
2. ``iso_gas_series``   — the keeper's own ``_gas_series`` (``gas_<year>.npy``),
                          i.e. the ISO-level delivered series AFTER the hub
                          overlay. This is what the lane prompt quoted.
3. ``delivered_<class>``— the keeper's per-unit ``fuel_prices`` rows, averaged
                          within each plant_group. This is what the LP prices.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso248_shape_attenuation.py
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
TRANSCO = REPO / "data" / "raw" / "gas-prices" / "transco_z6_ny_daily.csv"
OUT = REPO / "results" / "calibration" / "_nyiso248_shape_attenuation.json"
YEARS = (2022, 2023, 2024, 2025)
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
GAS_CLASS_TOKENS = ("CC", "CT", "ST_GAS")


def _month_of_day() -> np.ndarray:
    """Month index 0-11 for each of the 365 days of the non-leap clock."""
    return np.concatenate([np.full(d, m) for m, d in enumerate(DAYS_IN_MONTH)])


def _hour_to_day(series: np.ndarray) -> np.ndarray:
    """Collapse an (8760,) hourly series to (365,) calendar-day means."""
    return series[: 365 * 24].reshape(365, 24).mean(axis=1)


def transco_daily_calendar(year: int) -> np.ndarray:
    """Measured Transco Z6 NY prints on a (365,) calendar-day staircase.

    A day the archive never priced holds the last priced day forward (and the
    first priced day backward), which is what a flow day actually does — a
    Friday print prices the weekend package. No interpolation, so a one-day
    spike is never smeared into its neighbours.
    """
    import datetime

    by_doy: dict[int, float] = {}
    with TRANSCO.open() as fh:
        for r in csv.DictReader(fh):
            if not r["date"].startswith(str(year)):
                continue
            v = r["transco_z6_ny_usd_mmbtu"]
            if v in ("", "NA"):
                continue
            d = datetime.date.fromisoformat(r["date"])
            if d.month == 2 and d.day == 29:
                continue  # non-leap model clock
            doy = (
                sum(DAYS_IN_MONTH[: d.month - 1]) + d.day - 1
            )  # 0-based on the 365-day clock
            by_doy[doy] = float(v)
    if not by_doy:
        return np.full(365, np.nan)
    out = np.full(365, np.nan)
    for doy, v in by_doy.items():
        out[doy] = v
    # forward-fill then back-fill (the flow-day staircase)
    last = np.nan
    for i in range(365):
        if np.isnan(out[i]):
            out[i] = last
        else:
            last = out[i]
    nxt = np.nan
    for i in range(364, -1, -1):
        if np.isnan(out[i]):
            out[i] = nxt
        else:
            nxt = out[i]
    return out


def within_month_stats(day_series: np.ndarray) -> dict:
    """Level-free within-month dispersion of a (365,) calendar-day series."""
    mod = _month_of_day()
    cvs, ratios = [], []
    for m in range(12):
        seg = day_series[mod == m]
        seg = seg[~np.isnan(seg)]
        if seg.size < 5:
            continue
        mu = float(seg.mean())
        if mu <= 0:
            continue
        cvs.append(float(seg.std()) / mu)
        p50 = float(np.percentile(seg, 50))
        if p50 > 0:
            ratios.append(float(np.percentile(seg, 95)) / p50)
    return {
        "within_month_cv": float(np.mean(cvs)) if cvs else float("nan"),
        "within_month_p95_p50": float(np.mean(ratios)) if ratios else float("nan"),
        "n_months": len(cvs),
    }


def whole_year_stats(day_series: np.ndarray) -> dict:
    """Whole-year shape, for context only (carries the seasonal level move)."""
    s = day_series[~np.isnan(day_series)]
    p50 = float(np.percentile(s, 50))
    return {
        "min": float(s.min()),
        "p50": p50,
        "p90": float(np.percentile(s, 90)),
        "max": float(s.max()),
        "max_over_p50": float(s.max()) / p50 if p50 > 0 else float("nan"),
    }


def run_year(year: int) -> dict:
    z = np.load(CACHE / f"{year}.npz", allow_pickle=True)
    fp = np.asarray(z["fuel_prices"], dtype=float)
    groups = np.array([str(g) for g in z["plant_group"]])
    pmax = np.asarray(z["pmax"], dtype=float)
    iso_series = np.load(CACHE / f"gas_{year}.npy")

    stages: dict[str, dict] = {}

    tr = transco_daily_calendar(year)
    stages["1_transco_raw"] = {**within_month_stats(tr), **whole_year_stats(tr)}

    iso_day = _hour_to_day(np.asarray(iso_series, dtype=float))
    stages["2_iso_gas_series"] = {
        **within_month_stats(iso_day),
        **whole_year_stats(iso_day),
    }

    is_gas = np.array(
        [any(t in g.upper() for t in GAS_CLASS_TOKENS) for g in groups], dtype=bool
    )
    for klass in sorted(set(groups[is_gas])):
        rows = np.nonzero(is_gas & (groups == klass))[0]
        w = pmax[rows]
        if w.sum() <= 0:
            continue
        # capacity-weighted class mean delivered price, then to calendar days
        cls_hourly = (fp[rows, :] * w[:, None]).sum(axis=0) / w.sum()
        cls_day = _hour_to_day(cls_hourly)
        stages[f"3_delivered_{klass}"] = {
            **within_month_stats(cls_day),
            **whole_year_stats(cls_day),
            "mw": float(w.sum()),
        }
    return stages


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args()

    result = {"gate": "G-2", "years": {}}
    for y in args.year:
        st = run_year(y)
        result["years"][str(y)] = st
        print(f"\n================ {y} ================")
        print(
            f"  {'stage':<26} {'wm_CV':>8} {'wm_p95/p50':>11} "
            f"{'p50':>8} {'max':>9} {'max/p50':>8}"
        )
        base = st["1_transco_raw"]["within_month_cv"]
        for name, s in st.items():
            frac = s["within_month_cv"] / base if base and base > 0 else float("nan")
            tag = "" if name.startswith("1_") else f"   ({frac*100:5.1f}% of source)"
            print(
                f"  {name:<26} {s['within_month_cv']:>8.4f} "
                f"{s['within_month_p95_p50']:>11.4f} {s['p50']:>8.3f} "
                f"{s['max']:>9.3f} {s['max_over_p50']:>8.2f}{tag}"
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
