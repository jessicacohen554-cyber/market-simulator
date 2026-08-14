#!/usr/bin/env python3
"""neiso-93: cross-validate the extended NEISO nuclear anchor against EIA-930.

Two independent checks on the 2019-2022 rows this session adds to
:data:`market_sim.config.constants.NUCLEAR_MONTHLY_CF_BY_YEAR`:

1. **Per-plant attribution** — decompose the fleet monthly CF into its
   per-plant EIA-923 series (Millstone 2+3 = EIA 566, Seabrook = EIA 6115)
   so every dip in the committed comment can be traced to a single reactor
   going to ~0, the same evidentiary standard the 2023-2025 block carries.

2. **EIA-930 cross-validation** — reconstruct monthly nuclear CF from the
   independent EIA-930 ISNE ``NUC`` fuel-type series over the same model
   fleet pmax. EIA-923 (the anchor's source) and EIA-930 (hourly telemetry)
   are separate collections, so agreement is real corroboration. The
   neiso-92 assessment established the method tracks the committed anchor to
   0.007-0.016 in every year it exists; this reproduces that and extends it.

Also reports Pilgrim (EIA 6098, retired May 2019) so the fleet-vintage
caveat on the 2019 row is measured rather than asserted.

Usage::

    uv run python scripts/probes/_neiso93_nuclear_crossval.py
"""

from __future__ import annotations

import calendar
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

_MONTH_COLS = [f"netgen_{calendar.month_name[m].lower()}_mwh" for m in range(1, 13)]
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
# Pilgrim Nuclear Power Station, Plymouth MA — retired 31 May 2019 and absent
# from the EIA-860 operable snapshot the model fleet is built from. EIA plant
# code 1590, verified against the EIA-923 plant_name ("Pilgrim Nuclear Power
# Station", last generation year 2019). NOTE: the committed constants.py
# comment cites 6098 for Pilgrim, which is wrong — 6098 is "Big Stone", a
# South Dakota coal plant that generates in every year 2018-2025.
PILGRIM = 1590


def _fleet() -> tuple[list[int], float, dict[int, float]]:
    """Return ``(plant_codes, total_pmax_mw, per_plant_pmax)`` for NEISO nuclear."""
    cfg = get_iso_config("NEISO")
    units = [
        g
        for g in load_fleet_from_csv("NEISO", cfg)
        if g.fuel_type == "nuclear" and g.pmax_mw > 0
    ]
    per_plant: dict[int, float] = {}
    for g in units:
        per_plant[int(g.plant_code)] = per_plant.get(int(g.plant_code), 0.0) + g.pmax_mw
    return sorted(per_plant), sum(per_plant.values()), per_plant


def _eia930_monthly_cf(year: int, pmax_mw: float) -> list[float] | None:
    """Monthly nuclear CF reconstructed from EIA-930 ISNE ``NUC`` telemetry."""
    path = REPO / "data" / "raw" / "eia-930" / f"ISNE_fueltype_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df["period"] = pd.to_datetime(df["period"])
    # EIA-930 stamps UTC; convert to the ISO's local clock so the monthly
    # buckets line up with EIA-923's calendar months.
    local = df["period"].dt.tz_convert("America/New_York")
    sub = df[df["fueltype"].astype(str).str.upper() == "NUC"].copy()
    if sub.empty:
        return None
    sub["month"] = local[sub.index].dt.month
    sub["yr"] = local[sub.index].dt.year
    sub = sub[sub["yr"] == year]
    out = []
    for m in range(1, 13):
        mrows = sub[sub["month"] == m]
        hours = calendar.monthrange(year, m)[1] * 24
        if mrows.empty:
            out.append(float("nan"))
            continue
        out.append(round(float(mrows["value_mwh"].sum()) / (pmax_mw * hours), 3))
    return out


def main() -> None:
    codes, pmax, per_plant = _fleet()
    print(f"NEISO model nuclear fleet: plants {codes}, pmax {pmax:.1f} MW")
    for c in sorted(per_plant):
        print(f"    EIA {c}: {per_plant[c]:.1f} MW")

    gen = load_monthly_generation()
    report: dict = {"fleet_pmax_mw": pmax, "plants": per_plant, "years": {}}

    for year in YEARS:
        rows = gen[(gen["year"] == year) & (gen["plant_id"].isin(codes))]
        if rows.empty:
            print(f"\n{year}: no EIA-923 rows")
            continue

        # fleet CF (the anchor's own construction)
        monthly = rows[_MONTH_COLS].sum()
        fleet_cf = []
        for m in range(1, 13):
            hours = calendar.monthrange(year, m)[1] * 24
            fleet_cf.append(round(min(float(monthly.iloc[m - 1]) / (pmax * hours), 1.0), 2))

        # per-plant CF (dip attribution)
        per_plant_cf: dict[int, list[float]] = {}
        for c in codes:
            prow = rows[rows["plant_id"] == c][_MONTH_COLS].sum()
            per_plant_cf[c] = [
                round(float(prow.iloc[m - 1]) / (per_plant[c] * calendar.monthrange(year, m)[1] * 24), 2)
                for m in range(1, 13)
            ]

        cf930 = _eia930_monthly_cf(year, pmax)
        committed = NUCLEAR_MONTHLY_CF_BY_YEAR.get("NEISO", {}).get(year)

        mean923 = sum(fleet_cf) / 12
        print(f"\n{year}: EIA-923 fleet CF {fleet_cf}  (mean {mean923:.3f})")
        for c in codes:
            print(f"        EIA {c}: {per_plant_cf[c]}")
        if cf930:
            valid = [v for v in cf930 if v == v]
            mean930 = sum(valid) / len(valid) if valid else float("nan")
            delta = [round(a - b, 3) for a, b in zip(fleet_cf, cf930)]
            print(f"        EIA-930 NUC : {cf930}  (mean {mean930:.3f})")
            print(f"        923-930 diff: {delta}   |mean diff| {abs(mean923 - mean930):.3f}")
        if committed:
            match = [round(c, 2) for c in committed] == fleet_cf
            print(f"        committed   : {'MATCH' if match else 'DIFFERS ' + str(committed)}")

        # Pilgrim, for the fleet-vintage caveat
        prow = gen[(gen["year"] == year) & (gen["plant_id"] == PILGRIM)]
        if not prow.empty:
            twh = float(prow[_MONTH_COLS].sum().sum()) / 1e6
            months = [m for m in range(1, 13) if float(prow[_MONTH_COLS].sum().iloc[m - 1]) > 0]
            print(f"        PILGRIM ({PILGRIM}, off-fleet): {twh:.3f} TWh, months {months}")
            report.setdefault("pilgrim", {})[year] = {"twh": round(twh, 3), "months": months}

        report["years"][year] = {
            "eia923_fleet_cf": fleet_cf,
            "eia923_per_plant_cf": {str(k): v for k, v in per_plant_cf.items()},
            "eia930_cf": cf930,
            "committed": committed,
        }

    out = REPO / "results" / "calibration" / "_neiso93_nuclear_crossval.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
