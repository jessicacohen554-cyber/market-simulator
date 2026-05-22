#!/usr/bin/env python3
"""Forecast nuclear refueling outage blocks for any ISO.

Backcast years use the measured EIA-923 refueling cadence
(:data:`market_sim.config.constants.NUCLEAR_MONTHLY_CF_BY_YEAR`). Forecast
years have no data, so this script projects refueling outages forward from the
known cadence: each nuclear unit takes one ~35-day outage every ``cycle_years``
(biannual = 2, or 3-year), staggered across the fleet so co-located units and
peers don't all refuel at once, and placed in a spring or fall shoulder window
(never the summer/winter peaks). Output is one row per unit-refuel, in the same
shape as the historic outage extracts so it can drive the availability overlay.

Universal across ISOs: the nuclear fleet is read from EIA-860 per ISO, so the
same cadence logic applies to ERCOT, CAISO, PJM, NYISO, NEISO, ...

Examples::

    python scripts/forecast_nuclear_refuel.py --isos ERCOT --years 2026 2027 2028
    python scripts/forecast_nuclear_refuel.py --isos ERCOT CAISO PJM \
        --years 2026 2027 --cycle-years 2 --out inputs/nuclear-refuel-forecast.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

# A refueling outage is a fixed-length block placed in a shoulder month so it
# never lands on the summer or winter demand peak. Spring and fall are
# alternated across units to spread the fleet's outages through the year.
_DEFAULT_OUTAGE_DAYS = 35
_SHOULDER_START = {"spring": (4, 1), "fall": (10, 1)}  # (month, day)


def _nuclear_units(iso: str):
    """Return ``[(plant_code, plant_name, unit_id, capacity_mw), ...]`` for one
    ISO's nuclear fleet, sorted so co-located units are adjacent (and thus get
    different refuel phases)."""
    cfg = get_iso_config(iso)
    units = [
        (int(g.plant_code), g.name, getattr(g, "unit_id", ""), float(g.pmax_mw))
        for g in load_fleet_from_csv(iso, cfg)
        if g.fuel_type == "nuclear" and g.pmax_mw > 0
    ]
    return sorted(units, key=lambda u: (u[0], u[2], -u[3]))


def forecast_refuel_blocks(
    isos: list[str],
    years: list[int],
    cycle_years: int = 2,
    outage_days: int = _DEFAULT_OUTAGE_DAYS,
    base_year: int = 2024,
) -> pd.DataFrame:
    """Return forecast nuclear refueling blocks for ``isos`` over ``years``.

    Each unit refuels once per ``cycle_years``; its phase (which year in the
    cycle) and season (spring/fall) are assigned deterministically by its order
    in the fleet, so the schedule is reproducible and the outages are staggered.
    """
    rows = []
    for iso in isos:
        units = _nuclear_units(iso)
        for i, (code, name, unit, cap) in enumerate(units):
            phase = i % cycle_years          # which year within the cycle
            season = "spring" if i % 2 == 0 else "fall"
            mo, day = _SHOULDER_START[season]
            for year in years:
                if (year - base_year) % cycle_years != phase % cycle_years:
                    continue
                start = pd.Timestamp(year=year, month=mo, day=day)
                end = start + pd.Timedelta(days=outage_days)
                rows.append({
                    "iso": iso,
                    "plant_code": code,
                    "plant_name": name,
                    "unit": unit,
                    "capacity_mw": round(cap, 1),
                    "outage_start": start.strftime("%Y-%m-%d"),
                    "outage_end": end.strftime("%Y-%m-%d"),
                    "duration_days": outage_days,
                    "season": season,
                    "cycle_years": cycle_years,
                })
    return pd.DataFrame(rows, columns=[
        "iso", "plant_code", "plant_name", "unit", "capacity_mw",
        "outage_start", "outage_end", "duration_days", "season", "cycle_years",
    ]).sort_values(["iso", "outage_start", "plant_code"]).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--isos", nargs="+", default=["ERCOT"],
                    help="ISOs to forecast (default ERCOT).")
    ap.add_argument("--years", nargs="+", type=int, required=True,
                    help="Forecast years.")
    ap.add_argument("--cycle-years", type=int, default=2,
                    help="Refuel cadence: 2 = biannual (default), 3 = 3-year.")
    ap.add_argument("--outage-days", type=int, default=_DEFAULT_OUTAGE_DAYS,
                    help="Refueling outage length in days (default 35).")
    ap.add_argument("--base-year", type=int, default=2024,
                    help="Phase anchor year (default 2024).")
    ap.add_argument("--out", default=None,
                    help="CSV output path; prints to stdout when omitted.")
    args = ap.parse_args()

    df = forecast_refuel_blocks(
        args.isos, args.years, args.cycle_years, args.outage_days, args.base_year
    )
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.out, index=False)
        print(f"wrote {len(df)} refuel blocks to {args.out}")
    else:
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
