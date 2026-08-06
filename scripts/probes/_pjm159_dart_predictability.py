#!/usr/bin/env python3
"""pjm-159 task B, K-A1 / K-C1: is PJM's DA-RT spread a function of anything the
model can SEE?

This is the decisive test in `PREREG-pjm159-da-rt-architecture-2026-08-06.md`.
Both surviving candidate architectures depend on the same premise:

* **C-A (two-price LP)** — a second LP pass can differ from the first ONLY
  through state it can see. So the DA-RT spread it would have to reproduce must
  be a function of model-visible state.
* **C-C (measured reconciliation wedge)** — rule 13's forward test is *"could
  this same quantity be produced for a forward year from forward drivers, and
  would it respond to changed conditions?"* A wedge expressible as a function of
  model-visible state passes; a fixed measured hourly series fails, because it has
  no forward analogue and does not respond to changed model conditions.

**Pre-registered bar: adjusted R² < 0.25 kills BOTH.**

Design (all no-LP, in-sample 2023-2025, committed artifacts only):

* target — the measured hourly DA-RT spread from the canonical committed series
  ``actual_lmp_hourly_PJM.parquet``, the SAME series pjm-105 and pjm-158 used;
* regressors — **model-visible state only**: hour-of-day (23 dummies), month (11
  dummies), the model's own net-load percentile, and a reserve-tightness proxy
  (the model's own reserve headroom rank). Nothing measured-outcome enters the
  right-hand side: no LMP, no cleared price, no DA quantity. That is the whole
  point — a regressor the model cannot produce forward is not admissible as a
  driver, so including one would fake a pass;
* adjusted R² is reported for a nested ladder (calendar only -> + net load ->
  + tightness) so the marginal contribution of each block is visible;
* and the TWh consequence: how much of the pjm-158 DA-RT basis a
  state-conditional wedge would actually recover, at the measured gain, versus
  the raw measured wedge's full +5.84/+4.62/+6.58 TWh.

Ordinary least squares via ``numpy.linalg.lstsq`` on an explicit design matrix —
no scipy.optimize, no sklearn (rule: forbidden stack). This is a diagnostic
regression on measured data, not an LP or a fitted model parameter: nothing it
produces is written into any config.

Rule 22: reads committed artifacts only; no year is solved, scored or registered.

Usage::

    python scripts/probes/_pjm159_dart_predictability.py
    python scripts/probes/_pjm159_dart_predictability.py --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

YEARS = (2023, 2024, 2025)
BUNDLE = REPO / "results/calibration/pjm152_collapse_A"
CANON = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
T = 8760

#: pjm-158 §3, measured `dNet/dlambda` in MW per $/MWh (negative = net demand
#: falls as price rises). Used only to convert a $/MWh explained/unexplained
#: split into TWh, never as a fitted value.
GAIN_MW_PER_DOLLAR = {2023: -440.5, 2024: -462.8, 2025: -340.3}
#: pjm-158 §4, the DA-RT basis in TWh the wedge would have to close.
BASIS_TWH = {2023: 5.836, 2024: 4.621, 2025: 6.577}
#: pjm-158 §4's SHAPE / hour-by-hour dispersion leg of that basis -- the leg a
#: mean-only wedge cannot touch, and the larger leg in 2024 and 2025.
SHAPE_LEG_TWH = {2023: 2.845, 2024: 3.648, 2025: 4.145}
#: Pre-registered kill bar (PREREG §2, K-A1 / K-C1).
R2_BAR = 0.25


def measured_spread(year: int) -> np.ndarray:
    """Hourly measured DA-RT spread on the model clock, $/MWh.

    Same loader shape as ``_pjm158_virtual_basis.canonical_prices`` so the series
    is identical to the one the anchor was measured on.
    """
    df = pd.read_parquet(CANON)
    df = df[df["year"] == year]
    out = {}
    for run in ("da", "rt"):
        a = np.full(T, np.nan)
        idx = df["hour"].to_numpy(dtype=int)
        keep = (idx >= 0) & (idx < T)
        a[idx[keep]] = df[run].to_numpy(dtype=float)[keep]
        out[run] = pd.Series(a).ffill().bfill().to_numpy()
    return out["da"] - out["rt"]


def model_state(year: int) -> dict[str, np.ndarray]:
    """Model-visible state for one year, from the keeper's committed sidecars.

    Returns net load (MW), a reserve-tightness proxy, and the calendar keys. No
    measured price enters here — every series is something the model itself
    produces or is given as a forward driver.
    """
    sysd = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    load = sysd.groupby("hour")["demand"].sum().reindex(range(T)).to_numpy()

    cls = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    vre = (
        cls[cls["klass"].isin(("wind", "solar"))]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(T))
        .fillna(0.0)
        .to_numpy()
    )
    net_load = load - vre

    # Reserve tightness the model itself sees: the reserve balance-row dual is
    # ~0 in almost every PJM hour (the LP-vs-MIP boundary pjm-82 named), so the
    # usable proxy is thermal headroom -- committed thermal MW against its own
    # annual max, which the model produces and a forecast year reproduces.
    therm = (
        cls[
            cls["klass"].isin(
                (
                    "CC_REGULAR",
                    "CC_CHP",
                    "COAL_BIT",
                    "COAL_PRB",
                    "COAL_WC",
                    "CT_PEAKER",
                    "CT_CHP",
                    "ST_GAS",
                    "ST_CHP",
                    "oil",
                )
            )
        ]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(T))
        .fillna(0.0)
        .to_numpy()
    )
    tightness = therm / max(therm.max(), 1.0)

    cal = pd.date_range(f"{year}-01-01", periods=T, freq="h")
    return {
        "load": load,
        "net_load": net_load,
        "vre_share": vre / np.maximum(load, 1.0),
        "tightness": tightness,
        "hod": np.arange(T) % 24,
        "month": cal.month.to_numpy()[:T],
        "dow": cal.dayofweek.to_numpy()[:T],
    }


def _dummies(v: np.ndarray, drop_first: bool = True) -> np.ndarray:
    """One-hot design block for an integer key, first level dropped."""
    levels = np.unique(v)
    if drop_first:
        levels = levels[1:]
    return np.column_stack([(v == lv).astype(float) for lv in levels])


def _pct_rank(x: np.ndarray) -> np.ndarray:
    """Percentile rank in [0, 1] — scale-free, so it transfers across years."""
    order = np.argsort(np.argsort(x))
    return order / max(len(x) - 1, 1)


def adj_r2(y: np.ndarray, X: np.ndarray) -> tuple[float, np.ndarray]:
    """Adjusted R² and the fitted values for OLS of ``y`` on ``[1, X]``."""
    A = np.column_stack([np.ones(len(y)), X]) if X.size else np.ones((len(y), 1))
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    fit = A @ beta
    ss_res = float(((y - fit) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    n, k = len(y), A.shape[1] - 1
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    denom = n - k - 1
    return (1.0 - (1.0 - r2) * (n - 1) / denom if denom > 0 else float("nan")), fit


def run_year(year: int) -> dict:
    """The nested-ladder regression and its TWh consequence for one year."""
    y = measured_spread(year)
    st = model_state(year)
    ok = np.isfinite(y) & np.isfinite(st["net_load"])
    y = y[ok]

    # Deliberately generous regressor set: the honest way to conclude "no
    # admissible driver exists" is to try HARD to make the bar pass first, so the
    # ladder goes well past the pre-registered three blocks. Every block is still
    # model-visible (something the model produces or is given as a forward
    # driver) -- no measured price or measured quantity is ever on the RHS.
    nlp = _pct_rank(st["net_load"][ok])
    load = st["load"][ok]
    vre_share = st["vre_share"][ok]
    ramp = np.gradient(st["net_load"][ok])
    dow = st["dow"][ok]
    cal = np.column_stack([_dummies(st["hod"][ok]), _dummies(st["month"][ok])])
    weekend = (dow >= 5).astype(float).reshape(-1, 1)

    ladder = {
        "calendar (hod + month)": cal,
        "+ weekend": np.column_stack([cal, weekend]),
        "+ net-load percentile": np.column_stack([cal, weekend, nlp]),
        "+ load level & VRE share": np.column_stack(
            [cal, weekend, nlp, load, vre_share]
        ),
        "+ net-load ramp": np.column_stack([cal, weekend, nlp, load, vre_share, ramp]),
        "+ tightness proxy": np.column_stack(
            [cal, weekend, nlp, load, vre_share, ramp, st["tightness"][ok]]
        ),
        "+ hod x month interaction": np.column_stack(
            [
                cal,
                weekend,
                nlp,
                load,
                vre_share,
                ramp,
                st["tightness"][ok],
                # 264 interaction columns: the most flexible purely-calendar
                # form available. If the spread had a stable time-of-day-by-season
                # signature, this is where it would appear.
                _dummies(st["hod"][ok] * 100 + st["month"][ok]),
            ]
        ),
    }
    steps: dict[str, float] = {}
    fit_full = None
    for name, X in ladder.items():
        r2, fit = adj_r2(y, X)
        steps[name] = round(r2, 4)
        fit_full = fit
    best = max(steps.values())

    # TWh consequence, on the ONE decomposition that is not trivially true.
    #
    # An OLS fit with an intercept reproduces the annual MEAN exactly, so a wedge
    # carrying only the mean closes pjm-158's LEVEL leg by construction -- that
    # says nothing about identifiability, and a constant tuned to the measured
    # mean has no forward analogue anyway. The informative quantity is the SHAPE
    # leg (pjm-158 §4: +2.845/+3.648/+4.145 TWh, the larger leg in 2024 and
    # 2025), which requires HOUR-BY-HOUR predictability. To first order a
    # state-conditional wedge captures it in proportion to the variance it
    # explains, so the reachable share of the shape leg is ~ R2.
    shape_leg = SHAPE_LEG_TWH[year]
    return {
        "year": year,
        "n_hours": int(len(y)),
        "spread_mean": round(float(y.mean()), 3),
        "spread_sd": round(float(y.std()), 3),
        "spread_mean_abs": round(float(np.abs(y).mean()), 3),
        "adj_r2_ladder": steps,
        "adj_r2_best": best,
        "passes_bar": best >= R2_BAR,
        "basis_twh_pjm158": BASIS_TWH[year],
        "shape_leg_twh": shape_leg,
        "shape_leg_reachable_twh": round(shape_leg * max(best, 0.0), 3),
        "shape_leg_unreachable_twh": round(shape_leg * (1.0 - max(best, 0.0)), 3),
    }


def main() -> None:
    """Run the pre-registered K-A1 / K-C1 measurement."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    rows = [run_year(y) for y in YEARS]
    verdict = "PASS" if all(r["passes_bar"] for r in rows) else "FAIL"
    result = {
        "probe": "pjm-159 K-A1/K-C1 — DA-RT predictability from model-visible state",
        "bar": f"adjusted R2 >= {R2_BAR} in every year",
        "verdict": verdict,
        "kills": [] if verdict == "PASS" else ["C-A (two-price LP)", "C-C (wedge)"],
        "years": rows,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("=" * 78)
    print("pjm-159 K-A1 / K-C1 — is PJM's DA-RT spread model-visible?")
    print(f"PRE-REGISTERED BAR: adjusted R2 >= {R2_BAR} in every year, else C-A and C-C both die")
    print("=" * 78)
    for r in rows:
        print(f"\n{r['year']}   n = {r['n_hours']:,} h   "
              f"DA-RT mean {r['spread_mean']:+.3f}  sd {r['spread_sd']:.2f}  "
              f"mean|.| {r['spread_mean_abs']:.2f} $/MWh")
        for name, v in r["adj_r2_ladder"].items():
            print(f"     adj R2  {name:<28} {v:>8.4f}")
        print(f"     -> best {r['adj_r2_best']:.4f}: "
              f"{'PASSES' if r['passes_bar'] else 'FAILS'} the {R2_BAR} bar")
        print(f"     SHAPE leg {r['shape_leg_twh']:.3f} TWh -> a state-conditional "
              f"wedge reaches {r['shape_leg_reachable_twh']:.3f}, "
              f"leaves {r['shape_leg_unreachable_twh']:.3f} unreachable")

    print()
    print("=" * 78)
    print(f"VERDICT: {verdict}")
    if verdict == "FAIL":
        print(
            "C-A (two-price LP) and C-C (measured wedge) BOTH DIE on measurement.\n"
            "The DA-RT spread is not a function of state the model can see, so no\n"
            "second LP pass can reproduce it and no rule-13-admissible wedge exists\n"
            "(a fixed measured hourly series has no forward analogue and does not\n"
            "respond to changed conditions). With C-B killed by K-B1 or by rule 13\n"
            "on its face, and C-D refused ex ante, the DA/RT mismatch is a MEASURED,\n"
            "CLOSED representation boundary -- PREREG §4 branch 2."
        )
    else:
        print(
            "A state-conditional basis IS identifiable. C-C is the surviving\n"
            "candidate -- build default-off, matrix row in the same PR, then the\n"
            "pre-registered A/B (PREREG §4 branch 1)."
        )
    print("=" * 78)


if __name__ == "__main__":
    main()
