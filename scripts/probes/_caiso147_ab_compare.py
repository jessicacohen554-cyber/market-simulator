"""caiso-147: compare the control (A) and armed (B) arms of the CHP A/B.

No LP. Reads the two bundles' committed sidecars and reports class energy vs
the benchmark actuals, the live-delta check (prereg reject criterion 4), and
the protective C7/C8 rows for the classes that actually carry those gates.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
A = REPO / "results/calibration/caiso147_control_A"
B = REPO / "results/calibration/caiso147_chp_B"
YEARS = (2023, 2024, 2025)


def class_energy(bundle: Path, year: int) -> pd.Series:
    """Return P1 annual class energy in TWh."""
    d = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    return d[d["pass"] == "P1"].groupby("klass").mw.sum() / 1e6


def actuals(year: int) -> dict:
    """Return the committed benchmark's class totals for a year."""
    p = REPO / f"frontend/data/backcast/bench/CAISO/{year}.json.gz"
    return json.load(gzip.open(p))["bench"]["classFull"]


def main() -> int:
    """Print the A/B comparison."""
    print("=== CLASS ENERGY TWh (control A -> armed B), vs actual ===")
    for year in YEARS:
        a, b, act = class_energy(A, year), class_energy(B, year), actuals(year)
        print(f"\n-- {year} --")
        print(
            f"{'class':<12}{'A':>9}{'B':>9}{'delta':>9}{'actual':>9}{'A%':>6}{'B%':>6}"
        )
        for k in sorted(set(a.index) | set(b.index)):
            av, bv = a.get(k, 0.0), b.get(k, 0.0)
            if max(abs(av), abs(bv)) < 0.02:
                continue
            ac = act.get(k)
            ap = f"{100 * av / ac:.0f}" if ac else "-"
            bp = f"{100 * bv / ac:.0f}" if ac else "-"
            print(
                f"{k:<12}{av:>9.3f}{bv:>9.3f}{bv - av:>+9.3f}"
                f"{(ac if ac else float('nan')):>9.3f}{ap:>6}{bp:>6}"
            )
        print(f"{'TOTAL':<12}{a.sum():>9.3f}{b.sum():>9.3f}{b.sum() - a.sum():>+9.3f}")

    print("\n=== LIVE-DELTA CHECK (prereg reject #4: >=50 MW on a CHP class-hour) ===")
    for year in YEARS:
        da = pd.read_parquet(A / f"hourly/class_hourly_{year}.parquet")
        db = pd.read_parquet(B / f"hourly/class_hourly_{year}.parquet")
        for k in ("CC_CHP", "CT_CHP"):
            sa = da[(da["pass"] == "P1") & (da.klass == k)].set_index("hour").mw
            sb = db[(db["pass"] == "P1") & (db.klass == k)].set_index("hour").mw
            print(f"  {year} {k}: max |delta| = {(sb - sa).abs().max():8.1f} MW")

    print("\n=== PROTECTIVE GATES (D1/D2) ===")
    for lab, bundle in (("A", A), ("B", B)):
        p = bundle / "legitimacy_diagnostics.json"
        if not p.exists():
            print(f"  arm {lab}: MISSING legitimacy_diagnostics.json")
            continue
        d = json.load(open(p))
        print(f"  -- arm {lab} --")
        for r in d["diagnostics"]["D1"]:
            if r["class"] in ("CT_PEAKER", "ST_GAS", "COAL", "CC_CHP", "CT_CHP"):
                g = "GATED" if r.get("gated") else "ungated"
                print(
                    f"    D1 {r['year']} {r['class']:<10} profile_r {r['profile_r']:.3f} "
                    f"cv_ratio {r['cv_ratio']:.3f}  {g}  {r['verdict']}"
                )
        for r in d["diagnostics"]["D2"]:
            if r["class"] in ("CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP"):
                print(
                    f"    D2 {r['year']} {r['class']:<10} {r['mechanism']:<22} "
                    f"share {r['share_of_class']:.4f} of {r['class_total_twh']:.3f} TWh"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
