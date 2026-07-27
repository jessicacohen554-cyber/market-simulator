"""Compare the nyiso-89 measured-CT-heat-rate arm against its zero-delta control.

Reads only the two bundles' committed ``hourly/class_hourly_<year>.parquet``
sidecars, so the comparison needs no re-solve and no dashboard registration.
Both bundles are same-HEAD replays of the same keeper differing in exactly one
ScenarioConfig field, which is what makes the per-class delta attributable to
the input swap (CLAUDE.md: never compare to a registered keeper's metrics).

Reports per class and per year: control TWh, arm TWh, delta — plus the
CT_PEAKER residual against the benchmark actual, which is the quantity the
charter is about.

Usage::

    python scripts/probes/nyiso89_arm_vs_control.py \
        --control results/calibration/nyiso89_ctrl_zerodelta \
        --arm results/calibration/nyiso89_hrmeas_ctloaded
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


def class_twh(bundle: Path, year: int) -> pd.Series:
    """Return ``{class: TWh}`` of P1 dispatch for one bundle-year."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return pd.Series(dtype=float)
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    return df.groupby("klass")["mw"].sum() / 1e6


def main(argv: list[str] | None = None) -> int:
    """Print the per-class arm-vs-control dispatch delta."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--arm", type=Path, required=True)
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = parser.parse_args(argv)

    for year in args.years:
        ctrl = class_twh(args.control, year)
        arm = class_twh(args.arm, year)
        if ctrl.empty or arm.empty:
            print(f"{year}: missing sidecar in one bundle — skipped")
            continue
        both = pd.DataFrame({"control": ctrl, "arm": arm}).fillna(0.0)
        both["delta"] = both["arm"] - both["control"]
        both = both.sort_values("delta", key=abs, ascending=False)
        print(f"\n=== {year} — P1 dispatch TWh ===")
        print(f"{'class':<14}{'control':>10}{'arm':>10}{'delta':>10}")
        for klass, r in both.iterrows():
            if abs(r["delta"]) < 5e-4 and klass not in ("CT_PEAKER",):
                continue
            print(
                f"{klass:<14}{r['control']:>10.3f}{r['arm']:>10.3f}"
                f"{r['delta']:>+10.3f}"
            )
        print(
            f"{'TOTAL':<14}{both['control'].sum():>10.3f}"
            f"{both['arm'].sum():>10.3f}{both['delta'].sum():>+10.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
