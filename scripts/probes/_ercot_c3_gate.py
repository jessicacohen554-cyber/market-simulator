"""Score an ERCOT bundle on the C3 rubric gates (mean / shape / tail), per year.

Reads a solved bundle's ``system.parquet`` and scores the three C3
sub-criteria of docs/calibration-determination-rubric.md (2026-07-02
re-balance) against the measured hourly RTSPP:

* **C3a mean** — system demand-weighted annual mean within +/-5% of actual RT.
* **C3b shape** — NRMSE of the 12 demand-weighted monthly price vectors
  <= 0.15.
* **C3c tail** — hours > $200 (and the > $500 deep companion) within
  [0.7x, 1.5x] of actual.

``--decompose-overlays`` additionally scores the price with each persisted
post-solve overlay column (``rtordpa_overlay`` / ``dam_as_overlay``) removed —
the one-event-one-channel audit view: the overlays are additive post-solve, so
the variant is exact, no re-solve. It also reports the endogenous-vs-overlay
min-overlap dollars (hours where BOTH the co-opt scarcity, proxied by
price-minus-overlays > $200, and a measured overlay are live).

Usage:
    python scripts/probes/_ercot_c3_gate.py <bundle_dir> [...] [--decompose-overlays]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
EDGES = np.cumsum([0] + [d * 24 for d in DAYS])
YEARS = (2023, 2024, 2025)


def _pivot(sy: pd.DataFrame, col: str) -> np.ndarray:
    return sy.pivot_table(index="hour", columns="zone", values=col).to_numpy()


def score_year(
    sy: pd.DataFrame,
    actual: np.ndarray,
    year: int,
    label: str,
    drop_cols: tuple[str, ...] = (),
) -> None:
    """Print one year's C3 gate line for the bundle's final pass."""
    sy = sy[sy["pass"] == sorted(sy["pass"].unique())[-1]]
    price = _pivot(sy, "price")
    dem = _pivot(sy, "demand")
    removed = np.zeros(price.shape[0])
    for c in drop_cols:
        if c in sy.columns:
            ov = sy.pivot_table(index="hour", columns="zone", values=c).to_numpy()
            price = price - ov
            removed = removed + ov[:, 0]
    m = (price * dem).sum(1) / dem.sum(1)
    dsum = dem.sum(1)
    n = min(len(m), len(actual))
    m, a, dsum = m[:n], actual[:n], dsum[:n]
    fin = np.isfinite(a)
    # Dashboard-payload basis (render_calibration_html.build_payload): the
    # MODEL side is fully demand-weighted (across zones per hour and across
    # hours within the month/year via pMon/dMon), the ACTUAL side is the
    # simple time-mean of the hub RT series (avgLMP.rt / rt_mon). Mirroring
    # the asymmetry keeps these numbers comparable to the keeper ledger.
    mean_m = float((m * dsum).sum() / dsum.sum())
    mean_a = float(np.nanmean(a[fin]))
    c3a = mean_m / mean_a - 1.0
    mm = np.array(
        [
            float((m[s2] * dsum[s2]).sum() / dsum[s2].sum()) if len(m[s2]) else np.nan
            for s2 in (slice(EDGES[k], min(EDGES[k + 1], n)) for k in range(12))
        ]
    )
    am = np.array(
        [
            float(np.nanmean(a[s2])) if fin[s2].any() else np.nan
            for s2 in (slice(EDGES[k], min(EDGES[k + 1], n)) for k in range(12))
        ]
    )
    ok = np.isfinite(am)
    nrmse = float(np.sqrt(np.nanmean((mm[ok] - am[ok]) ** 2)) / np.nanmean(am[ok]))
    # C3c
    t200_m, t200_a = int((m > 200).sum()), int((a[fin] > 200).sum())
    t500_m, t500_a = int((m > 500).sum()), int((a[fin] > 500).sum())
    ratio = t200_m / t200_a if t200_a else float("inf")
    g = lambda cond: "PASS" if cond else "FAIL"
    print(
        f"  {year} {label:18s} C3a {mean_m:6.2f}/{mean_a:6.2f} {c3a * 100:+5.1f}% "
        f"{g(abs(c3a) <= 0.05)} | C3b NRMSE {nrmse:.3f} {g(nrmse <= 0.15)} | "
        f"C3c >200 {t200_m}/{t200_a} = {ratio:.2f}x {g(0.7 <= ratio <= 1.5)} "
        f"(>500 {t500_m}/{t500_a})"
    )
    resid = mm - am
    print("       " + " ".join(f"{MONTHS[k]}{resid[k]:+.1f}" for k in range(12)))


def main(argv: list[str]) -> int:
    decomp = "--decompose-overlays" in argv
    bundles = [b for b in argv if not b.startswith("--")]
    if not bundles:
        print(__doc__)
        return 1
    act = pd.read_parquet(ACTUAL)
    for bundle in bundles:
        p = Path(bundle) / "system.parquet"
        if not p.exists():
            print(f"!! {bundle}: no system.parquet")
            continue
        print(f"\n################ {bundle} ################")
        sysf = pd.read_parquet(p)
        for year in YEARS:
            sy = sysf[sysf.year == year]
            if sy.empty:
                continue
            ay = act[act.year == year]
            actual = np.full(8760, np.nan)
            actual[ay["hour"].to_numpy()] = ay["rt"].to_numpy(dtype=float)
            score_year(sy, actual, year, "full")
            if decomp:
                for col in ("dam_as_overlay", "rtordpa_overlay"):
                    if col in sy.columns and sy[col].abs().sum() > 0:
                        score_year(sy, actual, year, f"minus {col}", (col,))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
