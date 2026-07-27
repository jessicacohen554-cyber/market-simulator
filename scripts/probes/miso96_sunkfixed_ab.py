"""miso-96 A/B readout: `coal_committed_takeorpay_sunk_fixed` vs its control.

No-LP. Reads two committed bundles' `legitimacy_diagnostics.json` + `hourly/`
sidecars and prints the C7 D-1 rows (the gated criterion this arm targets), the
COAL_PRB diurnal profile amplitude, and the diurnal price spread — the three
statistics FINDING-miso96 identifies as the same defect seen three ways.

Usage:
    python scripts/probes/miso96_sunkfixed_ab.py CONTROL_BUNDLE ARM_BUNDLE
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

D1_MIN_CV_RATIO = 0.5  # scripts/legitimacy_diagnostics.D1_MIN_CV_RATIO
D1_MIN_PROFILE_R = 0.8


def _d1_rows(bundle: Path, klass: str = "COAL_PRB") -> dict[int, dict]:
    """Return {year: D-1 row} for ``klass`` from a bundle's diagnostics."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return {}
    diag = json.loads(path.read_text())["diagnostics"]
    return {
        int(r["year"]): r
        for r in diag.get("D1", {}).get("rows", [])
        if r.get("class") == klass
    }


def _profile(bundle: Path, year: int, klass: str) -> np.ndarray | None:
    """Hour-of-day mean MW for ``klass`` from the bundle's class hourly sidecar."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[(df["klass"] == klass) & (df["pass"] == "P1")]
    if df.empty:
        return None
    return df.assign(hod=df["hour"] % 24).groupby("hod")["mw"].mean().to_numpy()


def _price_spread(bundle: Path, year: int) -> tuple[float, float] | None:
    """Return (night HE0-3, peak HE16-19) load-weighted price for a bundle-year."""
    path = bundle / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"].copy()
    df["hod"] = df["hour"] % 24

    def _lw(hours: list[int]) -> float:
        sub = df[df["hod"].isin(hours)]
        return float(np.average(sub["price"], weights=sub["demand"]))

    return _lw([0, 1, 2, 3]), _lw([16, 17, 18, 19])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("control", type=Path)
    ap.add_argument("arm", type=Path)
    ap.add_argument("--class", dest="klass", default="COAL_PRB")
    args = ap.parse_args()

    ctl, arm = _d1_rows(args.control, args.klass), _d1_rows(args.arm, args.klass)
    years = sorted(set(ctl) | set(arm))

    print(f"=== C7 D-1 {args.klass}: gate cv_ratio >= {D1_MIN_CV_RATIO}, r >= {D1_MIN_PROFILE_R}")
    print(f"  {'year':<6} {'control r/cv':>22} {'arm r/cv':>22} {'verdict':>10}")
    for y in years:
        c, a = ctl.get(y, {}), arm.get(y, {})
        cv_a = a.get("cv_ratio")
        ok = cv_a is not None and cv_a >= D1_MIN_CV_RATIO
        ok = ok and (a.get("profile_r") or 0.0) >= D1_MIN_PROFILE_R
        print(
            f"  {y:<6} {str(c.get('profile_r')) + ' / ' + str(c.get('cv_ratio')):>22}"
            f" {str(a.get('profile_r')) + ' / ' + str(a.get('cv_ratio')):>22}"
            f" {'PASS' if ok else 'FAIL':>10}"
        )

    print(f"\n=== {args.klass} off-peak profile amplitude (h0-14, % of off-peak mean)")
    for y in years:
        for tag, b in (("control", args.control), ("arm", args.arm)):
            p = _profile(b, y, args.klass)
            if p is None:
                continue
            off = p[:15]
            print(
                f"  {y} {tag:<8} span {off.min():8.0f}-{off.max():8.0f} MW"
                f"  ({(off.max() - off.min()) / off.mean() * 100:5.1f}% of mean)"
                f"  annual-mean {p.mean():8.0f} MW"
            )

    print("\n=== diurnal price spread (load-weighted, P1)")
    for y in years:
        for tag, b in (("control", args.control), ("arm", args.arm)):
            sp = _price_spread(b, y)
            if sp is None:
                continue
            print(
                f"  {y} {tag:<8} night HE0-3 ${sp[0]:6.2f}  peak HE16-19 ${sp[1]:6.2f}"
                f"  spread ${sp[1] - sp[0]:6.2f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
