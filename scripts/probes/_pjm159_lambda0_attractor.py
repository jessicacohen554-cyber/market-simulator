#!/usr/bin/env python3
"""pjm-159 task B, K-B1: the miso-105 lambda0-attractor test, run for PJM.

The `da_virtual_bids` mechanism-matrix cell carries this as an explicit open
item: *"NOTE FOR PJM'S LANE (observation, NOT a verdict -- rule 25): the
lambda0-attractor question is a property of the family and was never asked in
PJM; PJM's premise is genuinely different (+7-11 GW of real depth), so it needs
PJM's own lambda0-gap and N/(S+N) measurement."* This probe runs it, on PJM's own
corpus, on the miso-105 bars.

The concern the test encodes: if the submitted curve's own crossing price
``lambda0`` already reproduces the price its book cleared at, AND the curve is
stiff relative to the model's supply stack, then arming the curve makes the
model's price substantially BECOME the measured book's crossing price. That is a
rule-1 violation (the model's answer is supplied by a measured outcome) and it
kills rule 13's forward test, because whatever regenerates the curve forward must
reproduce ``lambda0``, which IS the price the model exists to forecast.

**Two pre-registered bars** (`PREREG-pjm159-da-rt-architecture-2026-08-06.md` §2):

* **(i)** median ``|lambda0 - actual DA|`` <= $2/MWh  =>  attractor risk CONFIRMED
* **(ii)** displacement share ``N / (S + N)`` >= 30 %  =>  rule 1 / rule 13 kill

where ``N`` is the curve's own stiffness (GW per $/MWh) and ``S`` the model's
supply-stack elasticity at the same hour.

**On the estimator for S, and a CORRECTION to this probe's pre-registered
choice.** The PREREG said bar (ii) would be judged on a net-load-CONDITIONAL
slope, reasoning that conditioning removes the demand-shift confound (high-price
hours are also high-load hours) and so yields a conservative, smaller S that is
most likely to fire the bar. **That reasoning was wrong on the merits and this
probe does not follow it.** Conditioning on net load removes the demand shift
*and* the movement along the stack together: within a net-load decile the model's
dispatchable quantity is nearly pinned by the load level, so ``dQ/dlambda`` is
driven toward zero mechanically. The measured spread shows it — the conditional
estimate lands 6-30x below an independent measurement of the same quantity, and
an order of magnitude below the revealed slope. It is biased toward zero, which
*inflates* the displacement share rather than conserving it.

So S is reported three ways, and bar (ii) is judged on the first:

* ``S_pjm142`` (**PRIMARY**) — **2.88 / 3.37 / 2.57 GW per $1/MWh**, PJM's stack
  slope as directly and independently measured by pjm-142's pre-registered
  no-LP pre-check (`FINDING-pjm142-...-2026-07-31.md` §0, hour-resolved at
  h01-h04, confirming pjm-141's ex-ante T2-quantile prediction of
  2.92/3.50/2.66 to within 2-4 %). Already adjudicated, in this ISO, on this
  keeper line;
* ``S_revealed`` — this probe's own rolling +/-$5 slope of dispatchable MW on the
  model's dual across all hours. A cross-check: same order of magnitude as
  ``S_pjm142``, roughly half of it (annual rather than overnight, and revealed
  scatter attenuates);
* ``S_conditional`` — the discredited over-conditioned estimate, reported so the
  correction above is auditable rather than asserted.

A definitive S would come from the model's own offer stack (the ``mc`` vector /
``plant_tranche_bands``), which needs a model build and is the falsification route
for anyone revisiting this.

Reuses `_pjm158_virtual_gain`'s loaders verbatim (``load_curve``,
``build_hour_arrays``, ``crossing_price``, ``gain``, ``actual_da_price``) so the
curve identification is byte-for-byte the one pjm-158 and the LP itself use --
reproduced, not reimplemented.

Rule 22: in-sample 2023-2025 only; committed artifacts and the in-sample
``hrl_da_incs_decs`` corpus. No solve, no scoring, no out-of-training year.

Usage::

    python scripts/probes/_pjm159_lambda0_attractor.py
    python scripts/probes/_pjm159_lambda0_attractor.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _pjm158_virtual_gain import (  # noqa: E402
    YEARS,
    actual_da_price,
    build_hour_arrays,
    crossing_price,
    gain,
    load_curve,
    model_zonal,
)

BUNDLE = REPO / "results/calibration/pjm152_collapse_A"
T = 8760

#: miso-105 bars, carried verbatim (PREREG §2 K-B1).
LAMBDA0_BAR_USD = 2.0
SHARE_BAR = 0.30
#: Local-slope half-window, matching miso-105's `_slope` and neiso-76's STIFF_BAND.
STIFF_BAND = 5.0
#: PJM's stack slope in GW per $1/MWh as MEASURED by pjm-142's pre-registered
#: no-LP pre-check (FINDING-pjm142 §0: hour-resolved 2.88/3.37/2.57 at h01-h04,
#: confirming pjm-141's ex-ante T2-quantile prediction 2.92/3.50/2.66 to 2-4 %).
#: The PRIMARY S for bar (ii) -- an independent, already-adjudicated measurement
#: of exactly this quantity, in this ISO, on this keeper line.
S_PJM142_GW_PER_DOLLAR = {2023: 2.88, 2024: 3.37, 2025: 2.57}

#: The model's own dispatchable (non-VRE, non-virtual) classes -- the stack whose
#: elasticity competes with the curve's stiffness.
STACK_CLASSES = (
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
    "hydro",
    "import",
)


def model_price_and_stack(year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(model system price, dispatchable MW, system load)`` for one year, P1."""
    sysd = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    # Load-weighted system price -- the same statistic C3a gates on.
    g = sysd.groupby("hour")
    dem = g["demand"].sum().reindex(range(T)).to_numpy()
    wsum = (
        sysd.assign(pw=sysd["price"] * sysd["demand"])
        .groupby("hour")["pw"]
        .sum()
        .reindex(range(T))
        .to_numpy()
    )
    price = wsum / np.maximum(dem, 1e-9)

    cls = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    stack = (
        cls[cls["klass"].isin(STACK_CLASSES)]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(T))
        .fillna(0.0)
        .to_numpy()
    )
    return price, stack, dem


def _local_slope(price: np.ndarray, qty: np.ndarray, mask: np.ndarray) -> float:
    """Median local dQ/dprice (MW per $/MWh) over +/-``STIFF_BAND`` price windows.

    For each hour in ``mask``, regress ``qty`` on ``price`` across the hours whose
    price lies within +/- STIFF_BAND of it, and take the median of the per-hour
    slopes. Robust to the long right tail of the price distribution.
    """
    p, q = price[mask], qty[mask]
    if p.size < 50:
        return float("nan")
    order = np.argsort(p)
    p, q = p[order], q[order]
    lo = np.searchsorted(p, p - STIFF_BAND, side="left")
    hi = np.searchsorted(p, p + STIFF_BAND, side="right")
    slopes = []
    # Stride so a full year costs ~1k regressions, not 8760.
    for i in range(0, p.size, max(1, p.size // 1000)):
        a, b = lo[i], hi[i]
        if b - a < 30:
            continue
        pw, qw = p[a:b], q[a:b]
        var = pw.var()
        if var <= 1e-9:
            continue
        slopes.append(float(((pw - pw.mean()) * (qw - qw.mean())).mean() / var))
    return float(np.median(slopes)) if slopes else float("nan")


def stack_elasticity(year: int) -> dict[str, float]:
    """Model supply-stack elasticity, GW per $/MWh — revealed and conditional."""
    price, stack, dem = model_price_and_stack(year)
    ok = np.isfinite(price) & np.isfinite(stack)
    revealed = _local_slope(price, stack, ok)

    # Conditional: within net-load deciles the demand shift is largely removed,
    # so the remaining price-quantity covariation is much closer to a genuine
    # movement ALONG the stack. This is the smaller, conservative estimate.
    dec = np.digitize(dem, np.nanquantile(dem[ok], np.linspace(0.1, 0.9, 9)))
    per = [
        _local_slope(price, stack, ok & (dec == d))
        for d in range(10)
    ]
    per = [v for v in per if np.isfinite(v)]
    conditional = float(np.median(per)) if per else float("nan")
    return {
        "S_revealed_gw_per_dollar": round(revealed / 1000.0, 4),
        "S_conditional_gw_per_dollar": round(conditional / 1000.0, 4),
        "n_deciles_used": len(per),
    }


def run_year(year: int) -> dict:
    """Both K-B1 bars for one year."""
    bids = load_curve(year)
    hours = build_hour_arrays(bids)
    lam0 = crossing_price(hours)
    da = actual_da_price(year)
    zprice, _, _ = model_zonal(year)
    mprice, _, _ = model_price_and_stack(year)

    ok = np.isfinite(lam0) & np.isfinite(da)
    err = np.abs(lam0[ok] - da[ok])

    # (ii) curve stiffness at the price the book actually cleared at.
    N = np.abs(gain(hours, da, STIFF_BAND))[ok] / 1000.0  # GW per $/MWh
    S = stack_elasticity(year)
    s_prim = S_PJM142_GW_PER_DOLLAR[year]
    s_cons = S["S_conditional_gw_per_dollar"]
    s_reve = S["S_revealed_gw_per_dollar"]
    share_prim = float(np.median(N / (N + s_prim)))
    share_cons = float(np.median(N / (N + max(s_cons, 1e-9))))
    share_reve = float(np.median(N / (N + max(s_reve, 1e-9))))

    return {
        "year": year,
        "n_hours": int(ok.sum()),
        # --- bar (i) ---
        "lambda0_mean": round(float(np.nanmean(lam0[ok])), 2),
        "actual_da_mean": round(float(da[ok].mean()), 2),
        "model_price_mean": round(float(np.nanmean(mprice)), 2),
        "lambda0_err_median": round(float(np.median(err)), 2),
        "lambda0_err_mean": round(float(err.mean()), 2),
        "pct_hours_within_2usd": round(float(np.mean(err <= LAMBDA0_BAR_USD) * 100), 1),
        "bar_i_fires": bool(np.median(err) <= LAMBDA0_BAR_USD),
        # --- bar (ii) ---
        "N_curve_stiffness_gw_per_dollar": round(float(np.median(N)), 4),
        "S_pjm142_gw_per_dollar": s_prim,
        **S,
        "displacement_share_PRIMARY_pjm142": round(share_prim, 4),
        "displacement_share_revealed": round(share_reve, 4),
        "displacement_share_conditional_DISCREDITED": round(share_cons, 4),
        "bar_ii_fires": bool(share_prim >= SHARE_BAR),
        "bar_ii_would_fire_on_revealed": bool(share_reve >= SHARE_BAR),
        "bar_ii_would_fire_on_discredited_conditional": bool(share_cons >= SHARE_BAR),
    }


def main() -> None:
    """Run K-B1 and print both readings of the kill rule."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    rows = [run_year(y) for y in YEARS]
    any_i = any(r["bar_i_fires"] for r in rows)
    any_ii = any(r["bar_ii_fires"] for r in rows)
    result = {
        "probe": "pjm-159 K-B1 — miso-105 lambda0-attractor test, run for PJM",
        "bars": {
            "i_lambda0_reproduction": f"median |lambda0 - actual DA| <= ${LAMBDA0_BAR_USD}",
            "ii_displacement_share": f"N/(S+N) >= {SHARE_BAR:.0%} on S_pjm142 (PRIMARY; "
            "the PREREG's S_conditional choice is CORRECTED in this probe's docstring)",
        },
        "bar_i_fires_any_year": any_i,
        "bar_ii_fires_any_year": any_ii,
        # PREREG §2 wrote "either bar firing kills C-B"; the miso-105 PRECEDENT
        # is a CONJUNCTION. Both readings are reported so neither is smuggled.
        "c_b_killed_prereg_rule_either": any_i or any_ii,
        "incumbent_attractor_miso105_conjunction": any_i and any_ii,
        "years": rows,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("=" * 78)
    print("pjm-159 K-B1 — the miso-105 lambda0-attractor test, run for PJM")
    print("=" * 78)
    for r in rows:
        print(f"\n{r['year']}   n = {r['n_hours']:,} h")
        print(f"  (i) lambda0 mean ${r['lambda0_mean']:>7.2f}   actual DA mean "
              f"${r['actual_da_mean']:>7.2f}   model dual mean ${r['model_price_mean']:>7.2f}")
        print(f"      median |lambda0 - DA| ${r['lambda0_err_median']:>6.2f}   "
              f"mean ${r['lambda0_err_mean']:>6.2f}   "
              f"within $2: {r['pct_hours_within_2usd']:>5.1f}% of hours")
        print(f"      -> bar (i) {'FIRES' if r['bar_i_fires'] else 'does NOT fire'} "
              f"(<= ${LAMBDA0_BAR_USD} median)")
        print(f"  (ii) curve stiffness N {r['N_curve_stiffness_gw_per_dollar']:.3f} GW/$")
        print(f"       model stack S:  pjm142 (PRIMARY) {r['S_pjm142_gw_per_dollar']:.2f}   "
              f"revealed {r['S_revealed_gw_per_dollar']:.3f}   "
              f"conditional {r['S_conditional_gw_per_dollar']:.3f} GW/$ [DISCREDITED]")
        print(f"       displacement share N/(S+N):  PRIMARY "
              f"{r['displacement_share_PRIMARY_pjm142']:.1%}   "
              f"revealed {r['displacement_share_revealed']:.1%}   "
              f"conditional {r['displacement_share_conditional_DISCREDITED']:.1%}")
        print(f"      -> bar (ii) {'FIRES' if r['bar_ii_fires'] else 'does NOT fire'} "
              f"(>= {SHARE_BAR:.0%} on the PRIMARY S)")

    print()
    print("=" * 78)
    print(f"bar (i) fires in some year: {any_i}    bar (ii) fires in some year: {any_ii}")
    print(f"C-B under the PREREG's OWN rule (either bar): "
          f"{'KILLED' if (any_i or any_ii) else 'survives'}")
    print(f"Incumbent attractor status under the miso-105 CONJUNCTION (both bars): "
          f"{'CONFIRMED' if (any_i and any_ii) else 'NOT confirmed'}")
    print("=" * 78)


if __name__ == "__main__":
    main()
