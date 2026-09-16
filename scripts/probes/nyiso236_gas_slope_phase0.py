"""nyiso-236 PHASE 0 (ZERO-LP): OBJECT B -- the model's price-vs-gas SLOPE and INTERCEPT.

Record: ``docs/FINDING-nyiso236-the-anchor-grain-and-the-gas-slope-2026-09-16.md``
(§3 the correct tail-stripped measurement; §3.3 the slope/intercept decomposition).

nyiso-235 recorded Object B as blocked because
``frontend/data/backcast/tail/actual_tail.json`` carries only tail HOUR COUNTS.
That is true of that file. The actual hourly series is a DIFFERENT file and it is
committed: ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet``
(``year, hour, rt, da``; 2018-2026, 8,760 h/yr), already read by
``scripts/data/derive_actual_amplitude.py``. Object B needs no new data and no solve.

The measurement nyiso-235 warned about is the one performed here: the tail is
stripped from BOTH sides on the SAME hours (the top N % BY ACTUAL price).
Stripping only the model's tail against the full-year actual is a different
measurement and gives the opposite sign.

Then it regresses each side's non-tail load-weighted price on that period's
delivered gas, at MONTH resolution pooled over the span (n = 48 for a four-year
NYISO bundle), and bootstraps the slope and intercept gaps.

DIAGNOSTIC ONLY. It identifies a defect; it cannot set a parameter, and nothing
here is on a solve path (rule 13 ``[R-MEASURED]``, rule 32 ``[R-SHARD]`` (a)).

Usage (from the repo root, ``--profile nyiso`` hydration)::

    python3 scripts/probes/nyiso236_gas_slope_phase0.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HOURS = 8760
ACTUAL = Path("data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet")


def month_index() -> np.ndarray:
    """Hour -> month (1..12) on the model's own non-leap 8,760 calendar."""
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    return np.concatenate([np.full(d * 24, m + 1) for m, d in enumerate(days)])


def model_hourly(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """``(load-weighted system price $/MWh, total load MW)`` per hour, P1 pass."""
    df = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    p = df.pivot(index="hour", columns="zone", values="price").sort_index().to_numpy(float)
    d = df.pivot(index="hour", columns="zone", values="demand").sort_index().to_numpy(float)
    load = d.sum(axis=1)
    return (p * d).sum(axis=1) / np.where(load == 0, np.nan, load), load


def lw(price: np.ndarray, load: np.ndarray, mask: np.ndarray) -> float:
    """Load-weighted mean of *price* over the hours *mask* selects.

    A hour whose price is NaN is dropped from the NUMERATOR **and** the
    denominator. Summing the numerator with ``nansum`` while leaving that hour's
    load in the denominator would bias the mean toward zero; NYISO's actual RT
    series carries two such hours (2025 h3525-3526), so the effect is tiny, but
    the identity has to be right rather than tiny.
    """
    ok = mask & np.isfinite(price) & np.isfinite(load)
    return float((price[ok] * load[ok]).sum() / load[ok].sum())


def main() -> None:
    """Measure the tail-stripped bias and the slope/intercept decomposition."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=Path("results/calibration/nyiso235_gasrepair_span"))
    ap.add_argument("--anchors", type=Path, default=None, help="JSON from nyiso236_anchor_grain_phase0 --out")
    ap.add_argument("--years", type=int, nargs="+", default=[2022, 2023, 2024, 2025])
    ap.add_argument("--strip-pct", type=float, default=1.0)
    ap.add_argument("--reference-zone", default="Capital_Hudson")
    ap.add_argument("--boot", type=int, default=4000)
    args = ap.parse_args()

    act = pd.read_parquet(ACTUAL)
    mi = month_index()
    k = int(round(HOURS * args.strip_pct / 100.0))

    print(f"=== tail-stripped bias (top {args.strip_pct:g}% BY ACTUAL, removed from BOTH sides) ===")
    print(f"{'year':>6}{'act full':>10}{'mod full':>10}{'bias':>9}{'thresh':>9}{'act NT':>9}{'mod NT':>9}{'bias NT':>9}")
    rows = []
    for year in args.years:
        a = act[act["year"] == year].sort_values("hour")["rt"].to_numpy(float)
        m, load = model_hourly(args.bundle, year)
        if a.size != HOURS or m.size != HOURS:
            raise SystemExit(f"{year}: expected {HOURS} h, got actual {a.size} / model {m.size}")
        allh = np.ones(HOURS, bool)
        thr = float(np.sort(a)[-k])
        keep = a < thr
        fa, fm = lw(a, load, allh), lw(m, load, allh)
        na, nm = lw(a, load, keep), lw(m, load, keep)
        print(
            f"{year:>6}{fa:10.2f}{fm:10.2f}{100 * (fm - fa) / fa:+9.2f}{thr:9.0f}{na:9.2f}{nm:9.2f}{100 * (nm - na) / na:+9.2f}"
        )
        rows.append((year, a, m, load, keep))

    if args.anchors is None:
        print("\n(no --anchors JSON given: skipping the slope/intercept decomposition)")
        return
    anchors = json.loads(args.anchors.read_text())

    X, YA, YM = [], [], []
    for year, a, m, load, keep in rows:
        z = anchors["years"][str(year)]["zones"][args.reference_zone]["monthly_anchor"]
        for mo in range(1, 13):
            sel = keep & (mi == mo)
            if sel.sum() < 24:
                continue
            X.append(z[str(mo)] if str(mo) in z else z[mo])
            YA.append(lw(a, load, sel))
            YM.append(lw(m, load, sel))
    X, YA, YM = np.asarray(X), np.asarray(YA), np.asarray(YM)

    print(f"\n=== price = slope x delivered gas + intercept, non-tail, n = {X.size} month-points "
          f"(gas {X.min():.2f}..{X.max():.2f} $/MMBtu) ===")
    sa, ia = np.polyfit(X, YA, 1)
    sm, im = np.polyfit(X, YM, 1)
    for lbl, s, i, y in (("ACTUAL", sa, ia, YA), ("MODEL ", sm, im, YM)):
        print(f"  {lbl} slope {s:+7.3f}  intercept {i:+7.2f}  r {np.corrcoef(X, y)[0, 1]:+.3f}")
    print(f"  slope gap     {sm - sa:+7.3f} $/MWh per $/MMBtu ({100 * (sm - sa) / sa:+.1f} %)")
    print(f"  intercept gap {im - ia:+7.3f} $/MWh               ({100 * (im - ia) / ia:+.1f} %)")
    print(f"  crossover     {(im - ia) / (sa - sm):7.2f} $/MMBtu")

    rng = np.random.default_rng(0)
    ds, di = [], []
    for _ in range(args.boot):
        idx = rng.integers(0, X.size, X.size)
        s1, i1 = np.polyfit(X[idx], YA[idx], 1)
        s2, i2 = np.polyfit(X[idx], YM[idx], 1)
        ds.append(s2 - s1)
        di.append(i2 - i1)
    print(
        f"  bootstrap 95% CI  slope gap [{np.percentile(ds, 2.5):+.3f}, {np.percentile(ds, 97.5):+.3f}]"
        f"   intercept gap [{np.percentile(di, 2.5):+.2f}, {np.percentile(di, 97.5):+.2f}]"
    )


if __name__ == "__main__":
    main()
