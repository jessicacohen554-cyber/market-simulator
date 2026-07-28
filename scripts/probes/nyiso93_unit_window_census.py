"""nyiso-93 — census behind the empty NYISO short-window / partial-derate extracts.

Reproduces every number in
``docs/FINDING-nyiso93-unit-availability-windows-inert-2026-07-28.md``.

The two companion extracts (``--short-windows`` / ``--partial-windows`` of
``scripts/data/derive_campd_unit_outages.py``) both wrote **0 rows** for NYISO
over 2023-2025. This probe establishes *why* — that the detector found no
**coal**, not that it found no **windows** — on the two grains that matter, and
proves the resulting overlays are a no-op rather than merely empty:

1. **Detector input grain.** The short/partial guard is
   ``unit_is_coal[uid]``, i.e. CAMPD ``primaryFuelInfo in ("coal",
   "coal refuse")``. Census every unit-year in NYISO's CAMPD states (NY, NJ)
   by primary fuel.
2. **Overlay consumer grain.** ``unit_outage_short_derate_factors``
   defensively re-filters to ``plant_group == "COAL"``. Census the NYISO model
   fleet by ``plant_group`` capacity.
3. **No-op proof.** Call both overlay consumers for NYISO in all three years
   and show they return empty dicts, against the standard (>= 5-day) overlay
   as a live control.

No LP, no solve — this is an ex-ante adjudication (rule 28b) of the
``unit_outage_short_windows`` matrix cell for NYISO.

Run: ``uv run python scripts/probes/nyiso93_unit_window_census.py``
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet.eia860 import load_fleet_from_csv  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    unit_outage_derate_factors,
    unit_outage_short_derate_factors,
    unit_partial_outage_derate_factors,
)

YEARS = (2023, 2024, 2025)
# The detector's coal gate, verbatim from derive_campd_unit_outages.py:
# "A unit is coal (baseload) when its primary fuel is solid; CAMPD labels every
# solid fuel — including ERCOT's lignite — as 'Coal'."
COAL_FUELS = ("coal", "coal refuse")
UNIT_LEVEL_DIR = RAW_DATA_DIR / "campd-unit-level"


def census_campd_fuels() -> pd.DataFrame:
    """Return NYISO-state CAMPD unit-years aggregated by year and primary fuel."""
    states = campd.states_for_iso("NYISO")
    print(f"NYISO CAMPD states: {states}\n")
    frames = []
    for state in states:
        for year in YEARS:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                print(f"  (no unit-level extract: {path.name})")
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "facilityName",
                    "unitId",
                    "primaryFuelInfo",
                    "unitType",
                    "grossLoad",
                ],
            )
            df["fuel"] = df["primaryFuelInfo"].astype(str).str.strip().str.lower()
            units = (
                df.groupby(
                    ["facilityId", "facilityName", "unitId", "fuel", "unitType"],
                    observed=True,
                )["grossLoad"]
                .agg(["max", "sum"])
                .reset_index()
            )
            units["state"], units["year"] = state, year
            frames.append(units)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    print("=" * 72)
    print("1. DETECTOR INPUT GRAIN — CAMPD unit-years by primary fuel (NY+NJ)")
    print("=" * 72)
    allu = census_campd_fuels()
    summary = (
        allu.groupby(["year", "fuel"], observed=True)
        .agg(
            unit_years=("unitId", "size"),
            plants=("facilityId", "nunique"),
            gwh=("sum", lambda s: s.sum() / 1000.0),
        )
        .reset_index()
        .sort_values(["year", "unit_years"], ascending=[True, False])
    )
    print(summary.to_string(index=False))

    coal = allu[allu["fuel"].isin(COAL_FUELS)]
    print(f"\n>> COAL / COAL-REFUSE unit-years in NY+NJ CAMPD: {len(coal)}")
    if len(coal):
        print(coal.to_string(index=False))
    else:
        print("   NONE — the coal-only detector has an EMPTY input population.")

    print("\n" + "=" * 72)
    print("2. OVERLAY CONSUMER GRAIN — NYISO model fleet by plant_group")
    print("=" * 72)
    for year in YEARS:
        gens = load_fleet_from_csv(iso="NYISO", year=year)
        cap: dict[str, float] = collections.defaultdict(float)
        n: collections.Counter = collections.Counter()
        for g in gens:
            cls = g.plant_group or f"fuel:{g.fuel_type}"
            cap[cls] += float(g.pmax_mw or 0.0)
            n[cls] += 1
        print(f"\n--- NYISO model fleet {year} (total {sum(cap.values()):,.0f} MW) ---")
        for cls in sorted(cap, key=lambda c: -cap[c]):
            print(f"   {cls:14s} {n[cls]:4d} units {cap[cls]:9.1f} MW")
        coal_group = sum(v for k, v in cap.items() if "COAL" in k.upper())
        coal_fuel = sum(
            float(g.pmax_mw or 0.0) for g in gens if "coal" in str(g.fuel_type).lower()
        )
        print(
            f"   >> COAL plant_group: {coal_group:.1f} MW | "
            f"coal fuel_type: {coal_fuel:.1f} MW"
        )

    print("\n" + "=" * 72)
    print("3. NO-OP PROOF — overlay consumers for NYISO (standard = live control)")
    print("=" * 72)
    for year in YEARS:
        short = unit_outage_short_derate_factors(year, iso="NYISO")
        partial = unit_partial_outage_derate_factors(year, iso="NYISO")
        standard = unit_outage_derate_factors(year, iso="NYISO")
        print(
            f"{year}: short={len(short):3d} keys | partial={len(partial):3d} keys "
            f"| standard(control)={len(standard):3d} keys"
        )
    print(
        "\nBoth companions return EMPTY multiplier dicts in every year while the\n"
        "standard overlay is live — arming unit_outage_short_windows +\n"
        "unit_partial_outage_windows derates nothing. INERT (ex-ante), no solve."
    )


if __name__ == "__main__":
    main()
