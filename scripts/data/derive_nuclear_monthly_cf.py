#!/usr/bin/env python3
"""Derive per-year nuclear monthly capacity factors from EIA-923 actuals.

The backcast analogue of :mod:`scripts.forecast_nuclear_refuel`: forecast
years project a refueling cadence forward, while backcast years have the
measured outcome — EIA-923 monthly net generation — so the model's nuclear
availability overlay (:data:`market_sim.config.constants.
NUCLEAR_MONTHLY_CF_BY_YEAR`) is derived straight from it. For each ISO-year,
monthly CF = fleet net generation / (fleet pmax x hours-in-month), computed
over exactly the nuclear plants the model's fleet carries and capped at 1.0
(EIA-860 nameplate slightly understates winter net capability, so raw
winter ratios can exceed 1; the LP availability bound cannot).

Run it after a new EIA-923 year lands to extend the constants table, or with
``--check`` to assert the committed table still matches the data::

    python scripts/data/derive_nuclear_monthly_cf.py --isos ERCOT --years 2023 2024 2025
    python scripts/data/derive_nuclear_monthly_cf.py --isos ERCOT --years 2023 2024 2025 --check
"""

from __future__ import annotations

import argparse
import calendar
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    NUCLEAR_DORMANT_UNTIL,
    NUCLEAR_MONTHLY_CF_BY_YEAR,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

_MONTH_COLS = [f"netgen_{calendar.month_name[m].lower()}_mwh" for m in range(1, 13)]


def _nuclear_fleet(iso: str, year: int) -> tuple[list[int], float]:
    """Return ``(plant_codes, total_pmax_mw)`` of an ISO's nuclear fleet.

    Plants dormant in ``year`` (NUCLEAR_DORMANT_UNTIL — listed OP in EIA-860
    but physically offline, e.g. the Crane/TMI-1 restart) are excluded, the
    same exclusion the backcast availability applies, so the derived CF is
    not diluted by capacity that cannot run.
    """
    cfg = get_iso_config(iso)
    units = [
        g
        for g in load_fleet_from_csv(iso, cfg)
        if g.fuel_type == "nuclear"
        and g.pmax_mw > 0
        and year >= NUCLEAR_DORMANT_UNTIL.get(int(g.plant_code), 0)
    ]
    if not units:
        raise SystemExit(f"{iso}: no nuclear units in the model fleet")
    return sorted({int(g.plant_code) for g in units}), sum(g.pmax_mw for g in units)


def derive_monthly_cf(iso: str, year: int) -> list[float] | None:
    """Return the 12 monthly CFs for one ISO-year, or ``None`` when EIA-923
    has no rows for the fleet's nuclear plants that year.

    CF is measured against the *model fleet's* pmax — not EIA capability —
    so the resulting availability bound reproduces the measured energy when
    the LP dispatches nuclear at its cap. Values are clipped to 1.0 and
    rounded to 2 decimals, matching the committed constants table.
    """
    plant_codes, pmax_mw = _nuclear_fleet(iso, year)
    gen = load_monthly_generation()
    rows = gen[(gen["year"] == year) & (gen["plant_id"].isin(plant_codes))]
    if rows.empty:
        return None
    monthly_mwh = rows[_MONTH_COLS].sum()
    cfs = []
    for m in range(1, 13):
        hours = calendar.monthrange(year, m)[1] * 24
        cf = float(monthly_mwh.iloc[m - 1]) / (pmax_mw * hours)
        cfs.append(round(min(cf, 1.0), 2))
    return cfs


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--isos", nargs="+", default=["ERCOT"], help="ISOs to derive (default ERCOT)."
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        required=True,
        help="Backcast years with EIA-923 data.",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="Compare against the committed "
        "NUCLEAR_MONTHLY_CF_BY_YEAR table and exit nonzero "
        "on any mismatch.",
    )
    args = ap.parse_args()

    mismatched = False
    for iso in args.isos:
        print(f'    "{iso}": {{')
        for year in args.years:
            cfs = derive_monthly_cf(iso, year)
            if cfs is None:
                print(f"        # {year}: no EIA-923 nuclear rows")
                continue
            rendered = ", ".join(f"{cf:.2f}" for cf in cfs)
            print(f"        {year}: [{rendered}],")
            if args.check:
                committed = NUCLEAR_MONTHLY_CF_BY_YEAR.get(iso, {}).get(year)
                if committed is None:
                    print(f"        # {year}: NOT IN constants table")
                    mismatched = True
                elif [round(c, 2) for c in committed] != cfs:
                    print(f"        # {year}: constants table DIFFERS: {committed}")
                    mismatched = True
        print("    },")
    if args.check:
        if mismatched:
            raise SystemExit(
                "constants table out of date — paste the block "
                "above into NUCLEAR_MONTHLY_CF_BY_YEAR"
            )
        print("# --check: committed table matches the EIA-923 derivation")


if __name__ == "__main__":
    main()
