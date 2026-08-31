"""caiso-228 gate D1 — the PHYSICALLY-IDENTIFIED SoCalGas low-OFO derate, in MW,
derived from gas-system quantities alone and compared against the caiso-131 §5
(lambda, $200] band.

PRE-REGISTERED (PRECOMMIT-caiso227-ofo-arm-2026-08-31.md §4 D1). The derate's
magnitude is identified from the published tariff mechanic applied to measured
gas burn, and NEVER from the MW needed to move lambda (rules 13 [R-MEASURED] /
24 [R-DOF]). Nothing here reads a price residual, a tail-hour count, or any
model output.

THE TARIFF MECHANIC. A SoCalGas low OFO constrains each shipper's DAILY
IMBALANCE: on a declared gas day, deliveries into the system may fall short of
burn by no more than the published tolerance band (``tolerance_pct``, signed
negative on the low side) before a noncompliance charge attaches. It does not
confiscate gas already nominated and delivered. The quantity it removes from
the generation fleet is therefore the fleet's *unhedged incremental burn* — the
energy it could otherwise have drawn out of system linepack above its
nominations — and that quantity is exactly ``|tolerance_pct| x (measured daily
burn)``. This is the "declared tolerance applied to measured gas burn" route
the PRECOMMIT §4 D1 names.

MEASURED INPUTS (committed bytes only; no solve, no keeper replay):
- ``data/clean/gas-ofo-events/CAISO/gas-ofo-events.parquet`` — the qualifying
  gas days and each day's published ``tolerance_pct`` (caiso-226 intake).
- ``data/raw/campd-unit-level/CA_<year>.parquet`` — measured hourly heat input
  (MMBtu) and gross load (MW) of every CAMPD-reporting California unit.
- ``data/raw/reference/caiso-plant-hub-membership.csv`` — the measured
  generator/hub crosswalk (caiso-217 intake, the caiso-220 keeper's own input);
  ``TH_SP15`` is the SoCalGas-served fleet, ``TH_NP15``/``TH_ZP26`` are
  PG&E-served and out of a SoCalGas OFO's reach entirely.

The comparison target is caiso-131 §5's committed band table, quoted, NOT
re-measured (caiso-131 §10 DO-NOT-REDO).

Usage:
    uv run python scripts/probes/caiso228_ofo_d1_derate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

YEARS = (2023, 2024, 2025)
PACIFIC = ZoneInfo("America/Los_Angeles")
GAS_DAY_START_HOUR = 7  # SoCalGas gas day 07:00-07:00 Pacific

# caiso-131 §5, committed — the (lambda, $200] band in the MEASURED tail hours,
# MW by class. QUOTED, never re-measured (caiso-131 §10 DO-NOT-REDO).
CAISO131_BAND_MW = {
    2023: {"gas_cc": 2690, "gas_ct": 5219, "gas_st": 1280, "import": 3411, "hydro": 0},
    2024: {"gas_cc": 2772, "gas_ct": 5163, "gas_st": 414, "import": 4431, "hydro": 0},
    2025: {"gas_cc": 1541, "gas_ct": 7255, "gas_st": 2051, "import": 10365, "hydro": 0},
}

# CAMPD unitType strings that are gas-fired generating units in California.
_GAS_FUEL = "Pipeline Natural Gas"

# caiso-131 §4, committed — the keeper's MINIMUM dispatchable headroom over all
# 8,760 h, and the CAISO LOLP scarcity-overlay parameters the keeper runs
# (`caiso_scarcity_pricing=True`; VOLL $2,000, MCL 1,400 MW, sigma 2,500 MW).
# QUOTED, never re-measured (caiso-131 §10 DO-NOT-REDO).
CAISO131_MIN_HEADROOM_MW = {2023: 12173, 2024: 12689, 2025: 13137}
SCARCITY_MCL_MW = 1400.0
SCARCITY_SIGMA_MW = 2500.0


def local_hours(year: int) -> pd.DatetimeIndex:
    start = pd.Timestamp(year=year, month=1, day=1, tz=PACIFIC)
    end = pd.Timestamp(year=year + 1, month=1, day=1, tz=PACIFIC)
    return pd.date_range(start, end, freq="h", inclusive="left")


def main() -> None:
    hubs = pd.read_csv(REPO / "data/raw/reference/caiso-plant-hub-membership.csv")
    hub_of = dict(zip(hubs["plant_code"], hubs["hub"], strict=True))

    ofo = pd.read_parquet(
        REPO / "data/clean/gas-ofo-events/CAISO/gas-ofo-events.parquet"
    )
    low = ofo[ofo["side"] == "low"].copy()
    tol_of_day = dict(
        zip(low["gas_day"].dt.date, low["tolerance_pct"].abs(), strict=True)
    )

    result: dict[str, object] = {
        "method": (
            "derate_MW = |tolerance_pct| x measured SP15 gas heat input on the "
            "qualifying gas day, converted at the fleet's OWN measured heat rate "
            "that day. Identified from the tariff mechanic + measured burn; no "
            "model output, no residual, zero free parameters."
        ),
        "caiso131_band_mw": CAISO131_BAND_MW,
        "years": {},
    }

    for year in YEARS:
        campd = pd.read_parquet(REPO / f"data/raw/campd-unit-level/CA_{year}.parquet")
        campd = campd[campd["primaryFuelInfo"] == _GAS_FUEL].copy()
        # CAMPD facilityId (ORISPL) is published as a string; the crosswalk
        # keys on the integer EIA plant code, which is the same identifier.
        campd["hub"] = pd.to_numeric(campd["facilityId"], errors="coerce").map(hub_of)
        campd["ts"] = pd.to_datetime(campd["date"]) + pd.to_timedelta(
            campd["hour"], unit="h"
        )
        # the gas day OWNING an operating hour: the hour's date shifted back 7 h
        campd["gas_day"] = (
            campd["ts"] - pd.Timedelta(hours=GAS_DAY_START_HOUR)
        ).dt.date

        sp15 = campd[campd["hub"] == "TH_SP15"]
        unmapped_mmbtu = float(campd.loc[campd["hub"].isna(), "heatInput"].sum())

        # fleet-wide measured heat rate (MMBtu/MWh) on the SP15 gas fleet
        hi_all = float(sp15["heatInput"].sum())
        gl_all = float(sp15["grossLoad"].sum())
        fleet_hr = hi_all / gl_all if gl_all else float("nan")

        rows = []
        by_day = sp15.groupby("gas_day").agg(
            heat_input_mmbtu=("heatInput", "sum"),
            gross_load_mwh=("grossLoad", "sum"),
            hours=("heatInput", "size"),
        )
        for day, tol in sorted(tol_of_day.items()):
            if day.year != year or day not in by_day.index:
                continue
            r = by_day.loc[day]
            hr = (
                (r.heat_input_mmbtu / r.gross_load_mwh)
                if r.gross_load_mwh
                else fleet_hr
            )
            allowance_mmbtu = (tol / 100.0) * float(r.heat_input_mmbtu)
            mwh = allowance_mmbtu / hr
            rows.append(
                {
                    "gas_day": str(day),
                    "tolerance_pct": float(tol),
                    "sp15_gas_heat_input_mmbtu": round(float(r.heat_input_mmbtu), 1),
                    "sp15_gas_mwh": round(float(r.gross_load_mwh), 1),
                    "measured_heat_rate": round(float(hr), 3),
                    "derate_mwh_per_day": round(float(mwh), 1),
                    "derate_mw_day_avg": round(float(mwh) / 24.0, 1),
                    "derate_mw_if_all_in_6h_block": round(float(mwh) / 6.0, 1),
                }
            )

        band = CAISO131_BAND_MW[year]
        band_total = sum(band.values())
        gas_limbs = band["gas_cc"] + band["gas_ct"] + band["gas_st"]
        # The band limbs NO gas-side quantity mechanism can reach, at any
        # magnitude: imports are delivered across the WECC seam, not burned
        # on any California LDC system, and the hydro limb is 0.
        surviving_limbs = band_total - gas_limbs

        # SP15's measured share of the CAISO gas fleet's burn — the ceiling on
        # how much of the band's gas limbs an SP15-scoped mechanism can even
        # address (NP15/ZP26 gas is PG&E-served).
        caiso_gas = campd[campd["hub"].notna()]
        sp15_share = (
            float(sp15["heatInput"].sum()) / float(caiso_gas["heatInput"].sum())
            if len(caiso_gas)
            else float("nan")
        )

        derates = [r["derate_mw_day_avg"] for r in rows]
        peaks = [r["derate_mw_if_all_in_6h_block"] for r in rows]
        result["years"][str(year)] = {
            "qualifying_gas_days_with_campd": len(rows),
            "sp15_gas_fleet_measured_heat_rate": round(fleet_hr, 3),
            "sp15_share_of_caiso_gas_burn": round(sp15_share, 4),
            "unmapped_gas_heat_input_mmbtu": round(unmapped_mmbtu, 1),
            "derate_mw_day_avg": {
                "min": min(derates) if derates else None,
                "median": round(float(pd.Series(derates).median()), 1)
                if derates
                else None,
                "max": max(derates) if derates else None,
            },
            "derate_mw_if_all_in_6h_block": {
                "min": min(peaks) if peaks else None,
                "median": round(float(pd.Series(peaks).median()), 1) if peaks else None,
                "max": max(peaks) if peaks else None,
            },
            "band_total_mw": band_total,
            "band_gas_limbs_mw": gas_limbs,
            "band_mw_surviving_any_gas_side_derate": surviving_limbs,
            "band_addressable_ceiling_mw": round(gas_limbs * sp15_share, 1),
            "max_derate_as_frac_of_band": (
                round(max(peaks) / band_total, 4) if peaks else None
            ),
            # The LOLP overlay path (caiso-131 §4): the adder is
            # LOLP(R) x (VOLL - lambda) and needs headroom R within a few sigma
            # of MCL. How close does the derate bring R to that?
            "overlay_reachability": {
                "min_headroom_mw": CAISO131_MIN_HEADROOM_MW[year],
                "min_headroom_after_max_derate_mw": round(
                    CAISO131_MIN_HEADROOM_MW[year] - max(peaks), 1
                )
                if peaks
                else None,
                "sigmas_above_mcl_after_max_derate": round(
                    (CAISO131_MIN_HEADROOM_MW[year] - max(peaks) - SCARCITY_MCL_MW)
                    / SCARCITY_SIGMA_MW,
                    2,
                )
                if peaks
                else None,
                "sigmas_above_mcl_after_full_sp15_gas_ceiling": round(
                    (
                        CAISO131_MIN_HEADROOM_MW[year]
                        - gas_limbs * sp15_share
                        - SCARCITY_MCL_MW
                    )
                    / SCARCITY_SIGMA_MW,
                    2,
                ),
            },
            "days": rows,
        }

    dest = REPO / "results/calibration/_caiso228_d1_derate.json"
    dest.write_text(json.dumps(result, indent=2) + "\n")

    for year in YEARS:
        y = result["years"][str(year)]
        print(
            f"{year}: n_days={y['qualifying_gas_days_with_campd']:3d}  "
            f"HR={y['sp15_gas_fleet_measured_heat_rate']}  "
            f"SP15 share of CAISO gas burn={y['sp15_share_of_caiso_gas_burn']}\n"
            f"      derate MW (day-avg)  min/med/max = {y['derate_mw_day_avg']}\n"
            f"      derate MW (6h block) min/med/max = {y['derate_mw_if_all_in_6h_block']}\n"
            f"      band total {y['band_total_mw']} MW | gas limbs {y['band_gas_limbs_mw']} "
            f"| surviving ANY gas derate {y['band_mw_surviving_any_gas_side_derate']} MW "
            f"| addressable ceiling {y['band_addressable_ceiling_mw']} MW\n"
            f"      max derate / band = {y['max_derate_as_frac_of_band']}\n"
            f"      overlay reachability: {y['overlay_reachability']}"
        )
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
