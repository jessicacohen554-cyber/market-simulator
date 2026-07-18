#!/usr/bin/env python
"""Derive temperature-driven reliability-floor coefficients for any ISO.

Generic counterpart to the per-ISO ``derive_<iso>_*_reliability_floor.py``
scripts.  Reads CAMPD capacity-factor data and NOAA GHCN daily TMAX/TMIN
for the requested ISO, regresses CF vs temperature per (class, limb, zone),
and emits a ``ReliabilityFloorSpec`` registry entry ready to paste into
``iso_configs.py:RELIABILITY_FLOOR_REGISTRY``.

Usage::

    python scripts/data/derive_reliability_floor.py --iso PJM
    python scripts/data/derive_reliability_floor.py --iso PJM --years 2023 2024 2025
    python scripts/data/derive_reliability_floor.py --iso CAISO --class CT_PEAKER --limb hot

The script discovers the weather file at the canonical path
``data/raw/<iso>-weather/`` and the CAMPD unit-level data at
``data/raw/campd-unit-level/``.  It prints the derived coefficients and
a copy-pasteable ``ReliabilityFloorSpec(...)`` block.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))


def _load_weather(iso: str, zone: str | None, years: list[int]):
    """Load daily TMAX (and TMIN if available) for the ISO or zone."""
    from market_sim.data.eia_loader import iso_zone_tmax

    all_tmax, all_tmin = [], []
    for yr in years:
        result = iso_zone_tmax(iso, yr, 8760, zone=zone)
        if result is None:
            print(f"  WARNING: no weather data for {iso} zone={zone} year={yr}")
            continue
        tmax, tmin = result
        daily_tmax = tmax.reshape(-1, 24).mean(axis=1)
        all_tmax.append(daily_tmax)
        if tmin is not None:
            daily_tmin = tmin.reshape(-1, 24).mean(axis=1)
            all_tmin.append(daily_tmin)
    if not all_tmax:
        return None, None
    return np.concatenate(all_tmax), (np.concatenate(all_tmin) if all_tmin else None)


def _load_campd_cf(iso: str, plant_class: str, zone: str | None, years: list[int]):
    """Load measured CAMPD capacity factor for a plant class."""
    campd_dir = REPO / "data" / "raw" / "campd-unit-level"
    if not campd_dir.exists():
        print(f"  ERROR: CAMPD directory not found: {campd_dir}")
        return None
    # Placeholder: actual CAMPD loading would go here, using the same
    # classify_plant routing as the per-ISO scripts.
    print(
        f"  NOTE: CAMPD CF loading for {iso}/{plant_class}/{zone} "
        f"years={years} — implement per-ISO CAMPD routing for production use."
    )
    return None


def derive_coefficients(
    tmax: np.ndarray,
    cf: np.ndarray,
    limb: str = "hot",
    t0_init: float = 25.0,
):
    """Regress CF vs temperature and return (slope, t0, cap, base)."""
    if limb == "hot":
        mask = tmax >= t0_init
        x = tmax[mask] - t0_init
    else:
        mask = tmax <= t0_init
        x = t0_init - tmax[mask]
    y = cf[mask]
    if len(x) < 10:
        print(f"  WARNING: only {len(x)} points above/below t0={t0_init}")
        return None
    from numpy.polynomial.polynomial import polyfit

    coeffs = polyfit(x, y, 1)
    base = float(max(0.0, coeffs[0]))
    slope = float(max(0.0, coeffs[1]))
    cap = float(np.percentile(y, 97))
    return {
        "slope_per_c": round(slope, 4),
        "t0_c": t0_init,
        "cap": round(cap, 3),
        "base": round(base, 3),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO code (e.g. PJM, CAISO)")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="Years to pool (default: 2023 2024 2025)",
    )
    parser.add_argument(
        "--class", dest="plant_class", help="Plant class (e.g. CT_PEAKER)"
    )
    parser.add_argument("--limb", choices=["hot", "cold", "both"], default="both")
    parser.add_argument("--zone", help="Specific zone (default: system-wide)")
    parser.add_argument(
        "--t0", type=float, default=25.0, help="Zero-crossing temperature"
    )
    args = parser.parse_args()

    iso = args.iso.upper()
    print(f"Deriving reliability-floor coefficients for {iso}")
    print(f"  Years: {args.years}")
    print(f"  Class: {args.plant_class or 'all'}")
    print(f"  Limb:  {args.limb}")
    print(f"  Zone:  {args.zone or 'system-wide'}")
    print()

    tmax, tmin = _load_weather(iso, args.zone, args.years)
    if tmax is None:
        print("ERROR: no weather data found. Ensure weather files exist at")
        print(f"  data/raw/{iso.lower()}-weather/")
        sys.exit(1)

    print(f"  Loaded {len(tmax)} daily observations")
    print(f"  TMAX range: {tmax.min():.1f} - {tmax.max():.1f} C")
    if tmin is not None:
        print(f"  TMIN range: {tmin.min():.1f} - {tmin.max():.1f} C")

    cf = _load_campd_cf(iso, args.plant_class or "CT_PEAKER", args.zone, args.years)
    if cf is None:
        print()
        print("CAMPD CF not loaded — showing weather summary only.")
        print("To complete derivation, add CAMPD CF loading or use the")
        print(
            "per-ISO derive scripts (scripts/data/derive_<iso>_*_reliability_floor.py)."
        )
        print()
        print("Template ReliabilityFloorSpec for manual coefficient entry:")
        print()
        print("    ReliabilityFloorSpec(")
        print(f'        classes=("{args.plant_class or "CT_PEAKER"}",),')
        print(f'        limb="{args.limb if args.limb != "both" else "hot"}",')
        print("        hod_hours=(15, 22),")
        print("        hod_range=True,")
        print("        zones=None,")
        print('        tmax_mode="pooled",')
        print(f"        t0_c={args.t0},")
        print("        slope_per_c=0.0,  # fill from regression")
        print("        cap=0.0,  # fill from regression")
        print("        base=0.0,")
        print("    ),")
        sys.exit(0)

    if args.limb in ("hot", "both") and tmax is not None:
        print("\n--- Hot limb regression ---")
        result = derive_coefficients(tmax, cf, "hot", args.t0)
        if result:
            print(f"  {json.dumps(result, indent=2)}")

    if args.limb in ("cold", "both") and tmin is not None:
        print("\n--- Cold limb regression ---")
        result = derive_coefficients(tmin, cf, "cold", args.t0)
        if result:
            print(f"  {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
