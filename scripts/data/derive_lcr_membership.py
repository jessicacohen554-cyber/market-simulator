"""Derive the CAISO LCR-area membership crosswalk for the model fleet.

Assigns each CAISO thermal fleet plant (EIA-860) to a Local Capacity
Requirement area consumed by the local-capacity dispatch rows
(``ScenarioConfig.local_capacity_constraints``,
``market_sim.data.local_capacity``; design:
docs/ramp-locational-design-2026-07.md §3). Phase 1 covers the two SP15 load
pockets the evening-CT finding names: **LA Basin** and **San Diego-Imperial
Valley**. Phase 2 (caiso-79 STEP-0) adds **Greater Bay** — county rule for
the five core Bay counties plus the LCT §3.3.5.1 substation-rule overrides
(Moss Landing bus in; Lambie SW Sta in) — to ground the local-commitment
driver's unit list (the GB import cap itself was measured non-binding:
results/calibration/FINDING-caiso79-step0-greaterbay-bind-2026-07-12.md).

Assignment logic, most-authoritative first:

1. **NQC-list override** — the CAISO Final Net Qualifying Capacity list
   (``data/raw/caiso-nqc/``, `Local Area` column) is the authoritative
   per-resource area assignment. The override table below pins every
   boundary-county plant ≥ ~100 MW to its NQC-listed area (resource IDs
   cited in-line).
2. **County rule** — Los Angeles / Orange counties → LA Basin; San Diego /
   Imperial → San Diego-IV. These counties lie wholly inside their areas for
   CAISO-metered plants (LADWP is a separate BA and never enters the fleet).
3. **Riverside / San Bernardino geographic rule** — the LA Basin boundary
   runs through these counties (Devers/Mira Loma substations IN; Lugo /
   Red Bluff OUT, per the LCT report area definition). Plants at
   ``lat < 34.35`` (south of the San Gabriel/Cajon rim, excluding
   Victorville) **and** ``lon < -115.8`` (west of the Red Bluff/Eagle
   Mountain desert) are IN; the rest are OUT. Every plant ≥ 100 MW this rule
   touches is double-checked against the NQC list via the override table —
   the rule only decides small cogens/peakers.

Output: ``data/raw/reference/lcr_area_membership_CAISO.csv`` with one row per
thermal fleet plant that belongs to a covered LCR area (plants outside every
covered area are omitted — absence means "no local-capacity row coefficient").

Governance: a documented crosswalk of published data onto the model fleet
(CLAUDE.md rule #14 reconciliation) — no residual-derived choice anywhere.
Re-derive when the NQC list or EIA-860 vintage updates.

Usage::

    python scripts/data/derive_lcr_membership.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.local_capacity import (  # noqa: E402
    BOUNDARY_COUNTIES_CAISO,
    COUNTY_AREA_CAISO,
    GREATER_BAY,
    LA_BASIN,
    caiso_area_of,
)

EIA860_DIR = RAW_DIR / "eia-860"
OUT_PATH = RAW_DIR / "reference" / "lcr_area_membership_CAISO.csv"

# NQC-list overrides (2024 Final NQC List, data/raw/caiso-nqc/nqc_2024.xls,
# `Local Area` column) for every boundary-county plant >= ~100 MW. Value None
# = outside every covered area ("CAISO System" in the NQC list).
_NQC_OVERRIDES: dict[int, str | None] = {
    57482: LA_BASIN,  # Sentinel (SENTNL_2_CTG1-8: "LA Basin")
    358: LA_BASIN,  # Mountainview (SBERDO_2_PSP3/4: "LA Basin")
    56143: LA_BASIN,  # Riverside Energy Resource Center (RVSIDE_*: "LA Basin")
    55541: LA_BASIN,  # Indigo (INDIGO_1_UNIT*: "LA Basin")
    55295: None,  # Blythe Energy (BUCKBL_2_PL1X3: "CAISO System")
    55518: None,  # High Desert, Victorville (HIDSRT_2_UNITS: "CAISO System")
    55077: None,  # Desert Star (Clark County NV; "CAISO System")
}

# Greater Bay substation-rule overrides (Final 2023 LCT §3.3.5.1 area
# definition — the delineating-substation list, not a county line): the Moss
# Landing bus is IN ("Los Banos is out Moss Landing is in", Monterey county),
# and the Lambie switching station is IN ("Lambie SW Sta is in Vaca Dixon is
# out", Solano county) — the three Lambie-bus LM6000 peakers. Every other
# Monterey / Solano / Santa Cruz plant is outside the area (Coburn, Las
# Aguilas, Vaca Dixon all out).
_SUBSTATION_OVERRIDES: dict[int, str] = {
    260: GREATER_BAY,  # Moss Landing (Moss Landing 500/230 kV bus)
    55625: GREATER_BAY,  # Creed Energy Center (Lambie bus)
    55626: GREATER_BAY,  # Lambie Energy Center (Lambie bus)
    55627: GREATER_BAY,  # Goose Haven Energy Center (Lambie bus)
}


def main() -> None:
    """Build and write the membership crosswalk; print a review summary."""
    fleet = load_fleet_from_csv("CAISO", get_iso_config("CAISO"))
    plant_codes = sorted({int(g.plant_code) for g in fleet if g.plant_code})

    plants = pd.read_parquet(
        EIA860_DIR / "eia860_plant.parquet",
        columns=["Plant Code", "Plant Name", "County", "Latitude", "Longitude"],
    )
    plants.columns = ["plant_id", "plant_name", "county", "lat", "lon"]
    plants["lat"] = pd.to_numeric(plants.lat, errors="coerce")
    plants["lon"] = pd.to_numeric(plants.lon, errors="coerce")
    plants = plants[plants.plant_id.isin(plant_codes)].drop_duplicates("plant_id")

    # Plant capacity (for the review printout only).
    pmax = {}
    for g in fleet:
        pmax[int(g.plant_code)] = pmax.get(int(g.plant_code), 0.0) + float(g.pmax_mw)

    rows = []
    unreviewed = []
    for _, p in plants.iterrows():
        pid = int(p.plant_id)
        mw = pmax.get(pid, 0.0)
        if pid in _NQC_OVERRIDES:
            area = _NQC_OVERRIDES[pid]
            source = "nqc-list"
        elif pid in _SUBSTATION_OVERRIDES:
            area = _SUBSTATION_OVERRIDES[pid]
            source = "substation-rule"
        elif p.county in COUNTY_AREA_CAISO:
            area = COUNTY_AREA_CAISO[p.county]
            source = "county-rule"
        elif p.county in BOUNDARY_COUNTIES_CAISO:
            area = caiso_area_of(
                str(p.county),
                float(p.lat) if pd.notna(p.lat) else float("nan"),
                float(p.lon) if pd.notna(p.lon) else float("nan"),
            )
            source = "geo-rule"
            if mw >= 100:
                unreviewed.append((pid, p.plant_name, p.county, mw, area))
        else:
            continue  # outside every covered area
        if area is not None:
            rows.append(
                {
                    "plant_id": pid,
                    "plant_name": p.plant_name,
                    "county": p.county,
                    "capacity_mw": round(mw, 1),
                    "lcr_area": area,
                    "source": source,
                }
            )

    out = pd.DataFrame(rows).sort_values(
        ["lcr_area", "capacity_mw"], ascending=[True, False]
    )
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)

    print(f"wrote {OUT_PATH} ({len(out)} plants)")
    for area, g in out.groupby("lcr_area"):
        print(f"  {area}: {len(g)} plants, {g.capacity_mw.sum():,.0f} MW")
    if unreviewed:
        print(
            "REVIEW — boundary-county plants >= 100 MW decided by the geo rule "
            "(verify against the NQC list and add to _NQC_OVERRIDES):"
        )
        for pid, name, county, mw, area in unreviewed:
            print(f"  {pid} {name} ({county}, {mw:.0f} MW) -> {area}")


if __name__ == "__main__":
    main()
