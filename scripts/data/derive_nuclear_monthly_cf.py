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


def _nuclear_fleet(iso: str, year: int) -> tuple[list[int], list[float]]:
    """Return ``(plant_codes, online_pmax_by_month)`` of an ISO's nuclear fleet.

    Plants dormant in ``year`` (NUCLEAR_DORMANT_UNTIL — listed OP in EIA-860
    but physically offline, e.g. the Crane/TMI-1 restart) are excluded, the
    same exclusion the backcast availability applies, so the derived CF is
    not diluted by capacity that cannot run.

    The denominator is the fleet pmax ONLINE in each month — a unit counts
    from its own EIA-860 commercial-operation month (``online_year`` /
    ``online_month``, inclusive), the identical grain the LP's COD ramp
    serves since SOCO-15 (``data.cod_ramp.generator_online_mask``, owner
    card S12, 2026-09-13). ``_nuclear_monthly`` sets a nuclear unit's
    availability to this CF and the COD mask then multiplies it, so a CF
    divided by the WHOLE fleet's pmax in a month when a unit is not yet
    online would hand the online units a CF scaled down by the offline
    share: SOCO 2023 H1 (Vogtle 3 online 2023-07, Vogtle 4 2024-04) would
    read 6,054 / 8,282 of its measured output, a ~-27 % bias the LP could
    never recover — the mirror image of the phantom SOCO-15 removed. For
    every fleet with no in-window nuclear COD the monthly denominator equals
    the flat fleet pmax and the derived table is byte-identical
    (``--check`` proves it; SOCO-20, 2026-09-14).
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
    online_pmax = []
    for m in range(1, 13):
        online = 0.0
        for g in units:
            oy = int(getattr(g, "online_year", 0) or 0)
            om = int(getattr(g, "online_month", 1) or 1)
            if (oy, om) <= (year, m):
                online += g.pmax_mw
        online_pmax.append(online)
    return sorted({int(g.plant_code) for g in units}), online_pmax


def derive_monthly_cf(iso: str, year: int) -> list[float] | None:
    """Return the 12 monthly CFs for one ISO-year, or ``None`` when EIA-923
    has no rows for the fleet's nuclear plants that year.

    CF is measured against the *model fleet's* pmax ONLINE in the month —
    not EIA capability — so the resulting availability bound reproduces the
    measured energy when the LP dispatches nuclear at its cap (see
    :func:`_nuclear_fleet` for the COD-aware denominator). Values are clipped
    to 1.0 and rounded to 2 decimals, matching the committed constants table.
    A month with no unit online reads 0.0.
    """
    plant_codes, online_pmax = _nuclear_fleet(iso, year)
    gen = load_monthly_generation()
    rows = gen[(gen["year"] == year) & (gen["plant_id"].isin(plant_codes))]
    if rows.empty:
        return None
    monthly_mwh = rows[_MONTH_COLS].sum()
    cfs = []
    for m in range(1, 13):
        hours = calendar.monthrange(year, m)[1] * 24
        pmax_mw = online_pmax[m - 1]
        if pmax_mw <= 0.0:
            cfs.append(0.0)
            continue
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
