"""nyiso-136 — is the NYISO market-solar fleet-CF gap a TECHNOLOGY COMPOSITION object?

Measures, from published data only and BEFORE any mechanism is written or any
LP is solved, the three factual premises the fleet-CF composition object rests
on (``ASSESSMENT-nyiso135-promotion-2026-08-15.md`` §2 "LEVER QUEUE" item 2):

  P1  the 2024 build wave is TRACKING     -- named plants Morris Ridge,
      High River, East Point;
  P2  the fleet goes 100 % FIXED-TILT -> 56 % TRACKING across 2023-2025;
  P3  tracking plants run at a materially HIGHER capacity factor than
      fixed-tilt ones (quoted 0.198-0.221 vs 0.174-0.182), so ONE ISO-wide
      ``RENEWABLE_AVG_CF["NYISO"]["solar"]`` cannot track the mix.

and then the question that decides whether the mechanism is worth building at
all: even in its MOST GENEROUS form -- every plant carrying its OWN measured
mature capacity factor, not merely a per-technology one -- how much of the
implied fleet-CF swing (0.1613 / 0.1641 / 0.1955) can a composition weighting
actually reach?

Sources, both already committed and both PUBLISHED (rule 13 [R-MEASURED]):
  * ``data/raw/eia-860/eia860_solar_operable.parquet`` -- the per-plant
    ``Single-Axis Tracking?`` / ``Fixed Tilt?`` / ``Tilt Angle`` fields and each
    plant's ``Operating Year`` / ``Operating Month``;
  * ``data/raw/_processed-legacy/eia923_monthly_generation.parquet`` -- the same
    plants' metered monthly net generation.

The registry crosswalk is ``scripts/data/derive_nyiso_market_solar.PTID_TO_EIA``,
reused rather than re-derived so this probe measures the SAME 15-row registry the
keeper's capacity ramp is built from (rule 25 [R-ISO-SCOPE]: NYISO only).

A capacity factor is measured over MATURE months only -- age >= 2 months, the
threshold nyiso-133 established nationally (age-0/1/2 ratios 0.723 / 0.962 /
0.995 on a 1.0072 placebo) -- and over NON-ZERO months only, because a
full-month zero at a mature solar plant in a New York summer is an OUTAGE, not a
capacity factor, and averaging it in would measure availability as if it were
irradiance. The zeros are not discarded: they are counted and reported
separately, and they turn out to be the largest identified component of the
residual.

Writes ``results/calibration/_nyiso136_fleet_cf_composition.json``.

Usage:
    python scripts/probes/_nyiso136_fleet_cf_composition.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from data.derive_nyiso_market_solar import PTID_TO_EIA  # noqa: E402

EIA860_SOLAR = REPO / "data/raw/eia-860/eia860_solar_operable.parquet"
EIA923 = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
OUT = REPO / "results/calibration/_nyiso136_fleet_cf_composition.json"

MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
YEARS = (2023, 2024, 2025)

# Gold Book Table III-2a published Net Energy for the registered PV fleet, GWh
# (FINDING-nyiso133-market-solar-cod-basis-2026-08-08.md §6).
PUBLISHED_GWH = {2023: 229.9, 2024: 503.2, 2025: 981.8}
# The fleet CF that published energy implies, post date-repair (same source).
IMPLIED_CF = {2023: 0.1613, 2024: 0.1641, 2025: 0.1955}
# Mature-plant threshold in months since COD (nyiso-133, measured nationally).
MATURE_AGE_MONTHS = 2
# A plant-year needs this many usable mature months to yield a CF.
MIN_MATURE_MONTHS = 12


def _plant_names() -> dict[int, str]:
    """EIA plant code -> the Gold Book station name, from the crosswalk comments."""
    return {
        65125: "Puckett",
        65123: "Janis",
        68274: "Morris Ridge",
        65122: "Branscomb",
        65124: "Regan",
        65121: "Grissom",
        65839: "Darby",
        65841: "Stillwater",
        64077: "Albany County 1",
        65840: "Pattersonville",
        65805: "East Point",
        65765: "High River",
        57589: "Long Island Solar Farm",
        65679: "Calverton",
    }


def _technology(solar: pd.DataFrame, code: int) -> dict:
    """Return the plant's published mounting technology and corroborating angle."""
    sub = solar[solar["Plant Code"] == code]
    yes = lambda col: (  # noqa: E731
        sub[col].astype(str).str.strip().str.upper() == "Y"
    ).any()
    tracking = bool(yes("Single-Axis Tracking?") or yes("Dual-Axis Tracking?"))
    return {
        "technology": "TRACKING" if tracking else "FIXED",
        "single_axis": bool(yes("Single-Axis Tracking?")),
        "fixed_tilt": bool(yes("Fixed Tilt?")),
        "tilt_angle": str(sub["Tilt Angle"].iloc[0]).strip(),
        "nameplate_mw": float(
            pd.to_numeric(sub["Nameplate Capacity (MW)"], errors="coerce").sum()
        ),
        "cod_year": int(sub["Operating Year"].iloc[0]),
        "cod_month": int(sub["Operating Month"].iloc[0]),
    }


def main() -> int:
    solar = pd.read_parquet(EIA860_SOLAR)
    gen = pd.read_parquet(EIA923)
    gen = gen[gen["fuel_type"] == "SUN"]
    names = _plant_names()

    plants: dict[str, dict] = {}
    for ptid, code in PTID_TO_EIA.items():
        if code is None:
            plants[str(ptid)] = {
                "name": "Albany County Solar 2" if ptid == 323834 else f"ptid {ptid}",
                "eia_plant_code": None,
                "note": "no separate EIA-860 record; keeps its Gold Book date",
            }
            continue
        sub = solar[solar["Plant Code"] == code]
        if sub.empty:
            continue
        info = _technology(solar, code)
        mw, cy, cm = info["nameplate_mw"], info["cod_year"], info["cod_month"]

        energy = hours = 0.0
        zero_months: list[str] = []
        for year in YEARS:
            g = gen[(gen["plant_id"] == code) & (gen["year"] == year)]
            if g.empty:
                continue
            for i, month in enumerate(MONTHS):
                if (year - cy) * 12 + (i + 1 - cm) < MATURE_AGE_MONTHS:
                    continue
                mwh = float(
                    pd.to_numeric(g[f"netgen_{month}_mwh"], errors="coerce")
                    .fillna(0.0)
                    .sum()
                )
                if mwh <= 0.0:
                    zero_months.append(f"{year}-{i + 1:02d}")
                    continue
                energy += mwh
                hours += DAYS[i] * 24
        info.update(
            {
                "name": names.get(code, f"eia {code}"),
                "eia_plant_code": int(code),
                "mature_nonzero_months": int(hours / (30 * 24) + 0.5),
                "zero_output_mature_months": zero_months,
                "mature_cf": (
                    round(energy / (mw * hours), 4) if hours > 0 and mw > 0 else None
                ),
            }
        )
        if hours < MIN_MATURE_MONTHS * 28 * 24:
            info["mature_cf"] = None  # too little history to state a CF
        plants[str(ptid)] = info

    measured = [p for p in plants.values() if p.get("mature_cf")]
    by_tech = {}
    for tech in ("FIXED", "TRACKING"):
        sel = [p for p in measured if p["technology"] == tech]
        cfs = [p["mature_cf"] for p in sel]
        caps = [p["nameplate_mw"] for p in sel]
        by_tech[tech] = {
            "n_plants": len(sel),
            "cf_min": min(cfs),
            "cf_max": max(cfs),
            "cf_simple_mean": round(sum(cfs) / len(cfs), 4),
            "cf_capacity_weighted": round(
                sum(c * w for c, w in zip(cfs, caps)) / sum(caps), 4
            ),
            "plants": sorted(p["name"] for p in sel),
        }

    # The most generous composition mechanism:each plant carries its OWN measured
    # mature CF, weighted by its capacity-months online on the COD basis.
    composite = {}
    for year in YEARS:
        num = den = trk = tot = 0.0
        for p in measured:
            cy, cm, mw = p["cod_year"], p["cod_month"], p["nameplate_mw"]
            for i in range(12):
                if not (year > cy or (year == cy and (i + 1) >= cm)):
                    continue
                cap_h = mw * DAYS[i] * 24
                num += cap_h * p["mature_cf"]
                den += cap_h
                tot += cap_h
                if p["technology"] == "TRACKING":
                    trk += cap_h
        composite[str(year)] = {
            "composite_cf": round(num / den, 4),
            "mean_online_mw": round(den / 8760, 1),
            "tracking_share_of_capacity_months": round(trk / tot, 3),
            "implied_cf_from_published_energy": IMPLIED_CF[year],
        }

    swing_mech = composite["2025"]["composite_cf"] - composite["2023"]["composite_cf"]
    swing_real = IMPLIED_CF[2025] - IMPLIED_CF[2023]

    # Do the two published series agree? (Only where EIA-923 coverage is whole.)
    reconcile = {}
    codes = [c for c in PTID_TO_EIA.values() if c]
    for year in YEARS:
        g = gen[(gen["plant_id"].isin(codes)) & (gen["year"] == year)]
        total = (
            sum(
                float(
                    pd.to_numeric(g[f"netgen_{m}_mwh"], errors="coerce").fillna(0).sum()
                )
                for m in MONTHS
            )
            / 1000.0
        )
        reconcile[str(year)] = {
            "gold_book_net_energy_gwh": PUBLISHED_GWH[year],
            "eia923_metered_gwh": round(total, 1),
            "ratio": round(total / PUBLISHED_GWH[year], 3) if total else None,
            "plants_reporting": int(g["plant_id"].nunique()),
            "plants_crosswalked": len(codes),
        }

    # What the SAME measurement finds instead: how much of the residual against
    # each plant's own mature CF is full-month zero output at a MATURE plant --
    # i.e. an outage the model has no way to represent. Only stated for years
    # whose EIA-923 coverage is whole (2025 is a preliminary vintage).
    shortfall = {}
    for year in YEARS:
        # Coverage is judged against the plants ONLINE that year, not against
        # all 14 -- a plant with a 2024 COD is absent from 2023 by construction,
        # which is not a reporting gap. A year is usable only when every online
        # plant filed; 2025 is a preliminary EIA-923 vintage and is not.
        online = [
            p
            for p in measured
            if year > p["cod_year"] or (year == p["cod_year"] and p["cod_month"] <= 12)
        ]
        filed = gen[
            (gen["plant_id"].isin([p["eia_plant_code"] for p in online]))
            & (gen["year"] == year)
        ]["plant_id"].nunique()
        if filed < len(online):
            shortfall[str(year)] = {
                "skipped": "EIA-923 coverage incomplete (preliminary vintage)",
                "plants_online": len(online),
                "plants_reporting": int(filed),
            }
            continue
        expected = actual = lost = 0.0
        outages: list[str] = []
        for p in measured:
            cy, cm, mw = p["cod_year"], p["cod_month"], p["nameplate_mw"]
            g = gen[(gen["plant_id"] == p["eia_plant_code"]) & (gen["year"] == year)]
            for i, month in enumerate(MONTHS):
                if not (year > cy or (year == cy and (i + 1) >= cm)):
                    continue
                hrs = DAYS[i] * 24
                exp = mw * hrs * p["mature_cf"]
                act = (
                    float(
                        pd.to_numeric(g[f"netgen_{month}_mwh"], errors="coerce")
                        .fillna(0.0)
                        .sum()
                    )
                    if not g.empty
                    else 0.0
                )
                expected += exp
                actual += act
                if act <= 0.0 and (year - cy) * 12 + (i + 1 - cm) >= MATURE_AGE_MONTHS:
                    lost += exp
                    outages.append(f"{p['name']} {year}-{i + 1:02d}")
        gap = expected - actual
        shortfall[str(year)] = {
            "expected_at_own_mature_cf_gwh": round(expected / 1000.0, 1),
            "actual_metered_gwh": round(actual / 1000.0, 1),
            "shortfall_gwh": round(gap / 1000.0, 1),
            "shortfall_pct": round(100.0 * gap / expected, 1),
            "zero_output_at_mature_plant_gwh": round(lost / 1000.0, 1),
            "zero_output_share_of_shortfall": round(lost / gap, 2) if gap else None,
            "outage_months": outages,
        }

    record = {
        "probe": "nyiso-136 fleet-CF composition identification",
        "no_lp_solved": True,
        "premises_tested": {
            "P1_2024_wave_is_tracking": {
                "verdict": "FALSIFIED IN PART",
                "detail": (
                    "Morris Ridge and East Point are single-axis tracking, but "
                    "HIGH RIVER (90 MW, the second-largest plant and ~16 % of the "
                    "2025 fleet) is FIXED TILT: EIA-860 'Fixed Tilt?' = Y, "
                    "'Single-Axis Tracking?' blank, Tilt Angle 18 deg."
                ),
            },
            "P2_fleet_goes_100pct_fixed_to_56pct_tracking": {
                "verdict": "FALSIFIED",
                "detail": (
                    "The fleet is already "
                    f"{composite['2023']['tracking_share_of_capacity_months']:.0%} "
                    "tracking by capacity-months in 2023, reaching "
                    f"{composite['2025']['tracking_share_of_capacity_months']:.0%} "
                    "in 2025. Branscomb (COD 2021) and Regan (COD 2022) -- two of "
                    "the units the object calls 'small fixed-tilt NY8' -- are "
                    "single-axis tracking. The 56 % end point is right; the "
                    "100 % fixed-tilt start point is not."
                ),
            },
            "P3_tracking_runs_at_a_higher_cf": {
                "verdict": "FALSIFIED",
                "detail": (
                    "On mature, non-outage months the tracking flag has no "
                    f"explanatory power: FIXED mean {by_tech['FIXED']['cf_simple_mean']} "
                    f"(n={by_tech['FIXED']['n_plants']}, range "
                    f"{by_tech['FIXED']['cf_min']}-{by_tech['FIXED']['cf_max']}) vs "
                    f"TRACKING mean {by_tech['TRACKING']['cf_simple_mean']} "
                    f"(n={by_tech['TRACKING']['n_plants']}, range "
                    f"{by_tech['TRACKING']['cf_min']}-{by_tech['TRACKING']['cf_max']}). "
                    "The highest-CF plant in the fleet is FIXED TILT (Calverton) "
                    "and the lowest is TRACKING (Regan)."
                ),
            },
        },
        "by_technology": by_tech,
        "composition_ceiling": {
            "construction": (
                "every plant carries its OWN measured mature CF (strictly more "
                "expressive than any per-technology grouping), weighted by "
                "capacity-months online on the COD basis"
            ),
            "composite_cf_by_year": composite,
            "mechanism_swing": round(swing_mech, 4),
            "implied_swing": round(swing_real, 4),
            "fraction_of_named_effect_reachable": round(swing_mech / swing_real, 3),
        },
        "published_series_reconciliation": reconcile,
        "successor_object_sizing": {
            "claim": (
                "the residual is NOT technology composition; the largest single "
                "IDENTIFIED component is full-month zero output at a mature "
                "plant, which the VRE path cannot represent at all -- "
                "derive_cf_profile normalizes the EIA-930 shape to a flat annual "
                "mean CF and applies it to the full registered nameplate every "
                "hour, with no availability derate (the thermal fleet has "
                "THERMAL_AVAILABILITY / WEFOR; solar has nothing)"
            ),
            "by_year": shortfall,
        },
        "plants": plants,
    }
    OUT.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(
        f"  FIXED    n={by_tech['FIXED']['n_plants']} mean "
        f"{by_tech['FIXED']['cf_simple_mean']}   "
        f"TRACKING n={by_tech['TRACKING']['n_plants']} mean "
        f"{by_tech['TRACKING']['cf_simple_mean']}"
    )
    print(
        f"  composition ceiling: {swing_mech:+.4f} of a {swing_real:+.4f} swing "
        f"= {swing_mech / swing_real:.0%} of the named effect"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
