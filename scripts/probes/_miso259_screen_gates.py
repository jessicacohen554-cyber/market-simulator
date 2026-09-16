#!/usr/bin/env python3
"""Score the miso-259 screen's pre-registered STOP gates from two bundles.

Differences the ARM against its same-HEAD CONTROL on the quantities the
``PRECOMMIT-miso259-coal-fuel-inventory-2026-09-16.md`` §6 gates name, and
nothing else. STOP gates only: this script may report an arm dead, never
promote one, and it never touches C3a/C3b.

Reads only committed sidecars (``hourly/class_hourly_<year>.parquet`` and
``hourly/system_<year>.parquet``) plus the committed bench part for the actual
side — so it is zero-LP and re-runnable.

Usage:
    python scripts/probes/_miso259_screen_gates.py \
        --arm results/calibration/miso259_screen_arm \
        --control results/calibration/miso259_screen_control \
        --year 2022
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "MISO"

#: G-DIRECTION's floor: the coal fleet's best demonstrated capacity factor in
#: the published record (FINDING-miso256 §3). Coal falling BELOW this is an
#: overshoot and kills the arm.
BEST_DEMONSTRATED_CF = 0.641

#: Classes the released coal MWh are allowed to land on (G-DISPLACE).
DISPLACE_OK = ("CC_", "CT_", "ST_GAS", "OTHER_FOSSIL", "IMPORT", "oil")


def _classes(bundle: Path, year: int) -> pd.Series:
    """Return P1 annual TWh per class from a bundle's committed class sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    p1 = df[df["pass"] == "P1"]
    return p1.groupby("klass")["mw"].sum() / 1e6


def _system(bundle: Path, year: int) -> pd.DataFrame:
    path = bundle / "hourly" / f"system_{year}.parquet"
    return pd.read_parquet(path) if path.is_file() else pd.DataFrame()


def _coal(series: pd.Series) -> float:
    return float(series[[k for k in series.index if "COAL" in str(k).upper()]].sum())


def _coal_capacity_gw(bundle: Path, year: int) -> float | None:
    """Coal pmax in GW from the bundle's own dispatch parquet, if committed."""
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    col = next((c for c in ("pmax", "pmax_mw", "capacity_mw") if c in df.columns), None)
    kcol = next((c for c in ("klass", "class", "plant_group") if c in df.columns), None)
    if col is None or kcol is None:
        return None
    sel = df[df[kcol].astype(str).str.upper().str.contains("COAL")]
    return float(sel[col].sum()) / 1e3 if not sel.empty else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()
    year = args.year

    arm, ctl = _classes(args.arm, year), _classes(args.control, year)
    bench = ba.load_bench_part(BENCH / f"{year}.json.gz")["bench"]["classFull"]
    actual_coal = sum(v for k, v in bench.items() if "COAL" in str(k).upper())

    coal_arm, coal_ctl = _coal(arm), _coal(ctl)
    cap_gw = _coal_capacity_gw(args.control, year) or _coal_capacity_gw(args.arm, year)

    def cf(twh: float) -> float | None:
        return twh / (cap_gw * 8.76) if cap_gw else None

    print(f"=== miso-259 SCREEN GATES, {year} (arm vs same-HEAD control) ===")
    print(f"coal fleet capacity: {cap_gw if cap_gw else 'unavailable'} GW\n")

    print("G-DIRECTION — coal falls toward the best demonstrated CF, no overshoot")
    for label, twh in (("control", coal_ctl), ("ARM", coal_arm), ("actual", actual_coal)):
        c = cf(twh)
        print(f"  {label:8s} coal {twh:8.2f} TWh" + (f"   CF {c:.3f}" if c else ""))
    delta = coal_arm - coal_ctl
    closed = (coal_ctl - coal_arm) / (coal_ctl - actual_coal) if coal_ctl > actual_coal else float("nan")
    print(f"  arm - control      {delta:+8.2f} TWh")
    print(f"  arm - actual       {coal_arm - actual_coal:+8.2f} TWh")
    print(f"  share of the control's gap closed: {closed:.1%}")
    overshoot = coal_arm < actual_coal
    cf_arm = cf(coal_arm)
    print(f"  VERDICT: {'FAIL (overshoot below actual)' if overshoot else 'pass'}"
          + (f"; CF {cf_arm:.3f} vs best-demonstrated {BEST_DEMONSTRATED_CF}" if cf_arm else ""))

    print("\nG-DISPLACE — released MWh land on gas and imports, not slack/dump")
    both = sorted(set(arm.index) | set(ctl.index))
    rows = []
    for k in both:
        d = float(arm.get(k, 0.0)) - float(ctl.get(k, 0.0))
        if abs(d) >= 0.01:
            rows.append((k, d))
    for k, d in sorted(rows, key=lambda r: -abs(r[1])):
        tag = "  (coal, the target)" if "COAL" in str(k).upper() else ""
        print(f"  {str(k):26s} {d:+8.2f} TWh{tag}")
    absorbed = sum(d for k, d in rows if any(t in str(k).upper() for t in DISPLACE_OK))
    print(f"  absorbed by gas/import/oil classes: {absorbed:+.2f} TWh")

    sys_arm, sys_ctl = _system(args.arm, year), _system(args.control, year)
    for col in ("slack_mwh", "slack", "unserved_mwh", "dump_mwh", "dump", "curtail_mwh"):
        if col in sys_arm.columns and col in sys_ctl.columns:
            a, c = float(sys_arm[col].sum()) / 1e6, float(sys_ctl[col].sum()) / 1e6
            print(f"  system {col:14s} control {c:8.4f} -> arm {a:8.4f} TWh ({a - c:+.4f})")

    for col in ("price", "lmp", "price_mean", "load_weighted_lmp"):
        if col in sys_arm.columns and col in sys_ctl.columns:
            print(f"  system {col:14s} control {sys_ctl[col].mean():8.2f} -> "
                  f"arm {sys_arm[col].mean():8.2f} $/MWh (REPORTED ONLY, never a gate)")
            break

    if args.json_out:
        args.json_out.write_text(
            json.dumps(
                {
                    "year": year,
                    "coal_twh": {"arm": coal_arm, "control": coal_ctl, "actual": actual_coal},
                    "coal_cf": {"arm": cf(coal_arm), "control": cf(coal_ctl), "actual": cf(actual_coal)},
                    "coal_capacity_gw": cap_gw,
                    "class_deltas_twh": dict(rows),
                    "overshoot": bool(overshoot),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
