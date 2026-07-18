"""miso-72 per-zone validation: base vs winter-overlay vs actuals, Jan-14-17-2024.

The mechanism's correctness is validated PER-ZONE (design
``docs/handoffs/miso-winter-fuel-security-design-2026-07.md`` §3.5), NEVER by the
C3c residual (the scored Indiana hub sees ~1 Heather tail hour). For each of the
six MISO model zones this compares the base (winter overlay OFF) and main (ON) P1
zone LMP against the measured per-zone actual (``rt``, the hub-mean reference the
scorer uses) over the Winter Storm Heather window, and checks:

  * IMPROVEMENT — does |main-actual| < |base-actual| on the Chicago-hub zones
    (MISO-Illinois/Indiana/East) the overlay targets?
  * NULL CONTROL — are the non-Chicago zones (West/Plains/South) ~unmoved?
  * R2 (SETEX) — does any overlay-lifted zone LMP reach the $1000+ range (the
    out-of-representation TEXAS.HUB $1070 print)? Any hour that does is a red flag.

Usage:
    .venv/bin/python scripts/miso72_perzone_validate.py \
        --base results/calibration/miso72_probe_base \
        --main results/calibration/miso72_probe_main
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
_ACTUALS = _REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"

# Overlay targets (published miso_zonal_gas_hub.csv hub == "Chicago Citygate (IL)").
_CHICAGO_ZONES = {"MISO-Illinois", "MISO-Indiana", "MISO-East"}
_ZONE_ORDER = [
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
]


def _jan_hour(day: int, he: int = 0) -> int:
    """Hour index (0-based, Jan-1 HE01 == 0) of Jan ``day`` hour-ending ``he+1``."""
    return (day - 1) * 24 + he


def _pick_pass(df: pd.DataFrame) -> str:
    """Return the scored pass label (P1 / bid), else the lexicographically last."""
    passes = sorted(df["pass"].astype(str).unique())
    for p in passes:
        if p.lower() in {"p1", "bid", "bidcost", "bid_cost"}:
            return p
    # Fall back to the pass with the most non-trivial prices (the real solve).
    return passes[-1]


def _zone_price(bundle: Path, year: int) -> pd.DataFrame:
    """Return a (zone, hour)->price frame for the scored pass of ``year``."""
    df = pd.read_parquet(bundle / "system.parquet")
    df = df[df["year"] == year]
    p = _pick_pass(df)
    df = df[df["pass"].astype(str) == p]
    return df[["zone", "hour", "price"]].copy(), p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--main", type=Path, required=True)
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    year = args.year
    base, bpass = _zone_price(args.base, year)
    main, mpass = _zone_price(args.main, year)
    act = pd.read_parquet(_ACTUALS)
    act = act[act["year"] == year][["zone", "hour", "rt"]].copy()

    print(f"pass: base={bpass} main={mpass}  year={year}")
    print(f"actual zones present: {sorted(act['zone'].unique())}")

    # Heather window: gas flow days Jan-13..16 + the priced tail Jan-14..17.
    heather = list(
        range(_jan_hour(14), _jan_hour(17, 23) + 1)
    )  # Jan-14 00 .. Jan-17 23
    flow = list(range(_jan_hour(13), _jan_hour(16, 23) + 1))  # Jan-13..16 flow days
    jan = list(range(_jan_hour(1), _jan_hour(31, 23) + 1))

    def _mean(df: pd.DataFrame, col: str, zone: str, hours: list[int]) -> float:
        s = df[(df["zone"] == zone) & (df["hour"].isin(hours))][col]
        return float(s.mean()) if len(s) else float("nan")

    def _max(df: pd.DataFrame, col: str, zone: str, hours: list[int]) -> float:
        s = df[(df["zone"] == zone) & (df["hour"].isin(hours))][col]
        return float(s.max()) if len(s) else float("nan")

    print("\n=== HEATHER WINDOW (Jan-14 00:00 .. Jan-17 23:00) mean LMP $/MWh ===")
    print(
        f"{'zone':<15}{'target?':<9}{'base':>9}{'main':>9}{'actual':>9}"
        f"{'|b-a|':>8}{'|m-a|':>8}{'Δerr':>8}{'main_max':>10}"
    )
    tot_b = tot_m = 0.0
    for z in _ZONE_ORDER:
        b = _mean(base, "price", z, heather)
        m = _mean(main, "price", z, heather)
        a = _mean(act, "rt", z, heather)
        eb, em = abs(b - a), abs(m - a)
        tag = "CHICAGO" if z in _CHICAGO_ZONES else "control"
        mmax = _max(main, "price", z, heather)
        tot_b += eb
        tot_m += em
        print(
            f"{z:<15}{tag:<9}{b:>9.2f}{m:>9.2f}{a:>9.2f}"
            f"{eb:>8.2f}{em:>8.2f}{em - eb:>8.2f}{mmax:>10.2f}"
        )
    print(
        f"{'TOTAL MAE':<15}{'':<9}{'':<9}{'':<9}{'':<9}{tot_b:>8.2f}{tot_m:>8.2f}{tot_m - tot_b:>8.2f}"
    )

    print(
        "\n=== PER-DAY mean LMP (Chicago zones): base -> main  (actual)  Jan-12..18 ==="
    )
    for z in ["MISO-Illinois", "MISO-Indiana", "MISO-East"]:
        print(f"  {z}")
        for d in range(12, 19):
            hrs = list(range(_jan_hour(d), _jan_hour(d, 23) + 1))
            b = _mean(base, "price", z, hrs)
            m = _mean(main, "price", z, hrs)
            a = _mean(act, "rt", z, hrs)
            flag = "  <-- flow" if d in (13, 14, 15, 16) else ""
            print(
                f"    Jan-{d:<2} base {b:7.2f} -> main {m:7.2f}   actual {a:7.2f}{flag}"
            )

    print("\n=== R2 SETEX check: max main LMP over Heather window, all zones ===")
    gmax = max(_max(main, "price", z, heather) for z in _ZONE_ORDER)
    print(
        f"  global max main LMP in window = ${gmax:.2f}  "
        f"({'RED FLAG >$1000' if gmax > 1000 else 'OK (<$1000, no SETEX fabrication)'})"
    )

    print("\n=== full-January MAE per zone (broadening check) ===")
    for z in _ZONE_ORDER:
        b = abs(_mean(base, "price", z, jan) - _mean(act, "rt", z, jan))
        m = abs(_mean(main, "price", z, jan) - _mean(act, "rt", z, jan))
        print(f"  {z:<15} base {b:7.2f}  main {m:7.2f}  Δ {m - b:+7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
