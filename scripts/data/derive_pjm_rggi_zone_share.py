"""Derive PJM's per-zone RGGI-member fossil-capacity share (plan §5).

PJM's 8 model zones (`config/iso_configs.py::_pjm_config`) are multi-state
roll-ups straddling RGGI member states (MD, DE, NJ, and VA through 2023) and
non-member states (OH, IN, KY, WV, IL, most of PA), so a clean 0/1 zone map is
impossible. This script computes `m_zone[z]` = the RGGI-member share of each
PJM zone's operating fossil-fuel nameplate capacity, from:

* the EIA-860 plant + operable-generator tables for the year-matched vintage
  (`data/raw/eia-860/vintage_<year>/`, falling back to the canonical/current
  snapshot when no matching vintage is committed) — the same raw source the
  model's fleet builder reads (`data/fleet.py`);
* the same PJM zone assignment the dispatch model uses
  (`data.zone_assignment.build_zone_lookup("PJM")`, eGRID-2023-derived
  lat/lon/FIPS geography) — so the derived share is coherent with how the LP
  actually zones each plant;
* :data:`market_sim.config.constants.RGGI_MEMBER_STATES_BY_YEAR` for which
  states count as RGGI members in a given year (Virginia exited 1 Jan 2024).

Output feeds `PJM_RGGI_ZONE_SHARE` in `constants.py` (hand-copied, cited to
this script + the EIA-860 vintages, mirroring the existing intake discipline
for `STATE_CARBON_PRICE_BY_ISO` / `RGGI_STATE_CO2_BUDGET` — the clean tree is
gitignored so the authoritative in-repo value lives in `constants.py`).

Run: ``python scripts/data/derive_pjm_rggi_zone_share.py``
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from market_sim.config import paths
from market_sim.config.constants import RGGI_MEMBER_STATES_BY_YEAR
from market_sim.data import zone_assignment

# EIA-860 Schedule 3 "Energy Source" codes for coal / oil / fossil-gas units
# (RGGI covers fossil power plants ≥25 MW). Excludes renewables (SUN, WND,
# WAT, GEO), nuclear (NUC), storage (MWH), and biomass/waste (LFG, BLQ, WDS,
# MSW, OBG, AB, WDL, OBL, OBS) — none of which surrender RGGI allowances.
FOSSIL_ENERGY_SOURCES: frozenset[str] = frozenset(
    {
        "NG",  # natural gas
        "BIT",
        "SUB",
        "LIG",
        "RC",
        "WC",
        "PC",  # coal / coal-derived
        "SGC",  # coal synthesis gas
        "DFO",
        "RFO",
        "KER",
        "JF",  # oil
        "OG",
        "BFG",
        "PG",  # other fossil/refinery gas
    }
)

# Operating status code (EIA-860 Schedule 3): "OP" = in service.
_OPERATING_STATUS = "OP"


def _vintage_dir(year: int) -> Path:
    """Return the year-matched EIA-860 vintage directory, or the canonical one."""
    candidate = paths.EIA_860_DIR / f"vintage_{year}"
    return candidate if candidate.is_dir() else paths.EIA_860_DIR


def compute_zone_shares(year: int, iso: str = "PJM") -> dict[str, float]:
    """Return ``{zone: RGGI-member fossil-capacity share}`` for ``iso``/``year``.

    Joins the year-matched EIA-860 plant (state) and operable-generator
    (fuel/status/nameplate capacity) tables, filters to the ISO's balancing
    authority and to operating fossil units, assigns each plant to a model
    zone via :func:`zone_assignment.build_zone_lookup`, and returns the
    capacity-weighted RGGI-member share per zone. Plants the zone lookup
    cannot place (too new for the eGRID 2023 vintage; PJM has no EIA-860
    zone-lookup supplement, see ``zone_assignment._EIA860_SUPPLEMENT_ISOS``)
    are dropped — a small, logged-by-omission cohort, not guessed.
    """
    vintage = _vintage_dir(year)
    ba_code = zone_assignment._ISO_TO_BA_CODE[iso]

    plant = pd.read_parquet(
        vintage / "eia860_plant.parquet",
        columns=["Plant Code", "State", "Balancing Authority Code"],
    )
    ba = plant["Balancing Authority Code"].astype(str).str.strip()
    plant = plant[ba == ba_code]

    gen = pd.read_parquet(
        vintage / "eia860_generator_operable.parquet",
        columns=["Plant Code", "Energy Source 1", "Status", "Nameplate Capacity (MW)"],
    )
    gen = gen[gen["Status"] == _OPERATING_STATUS]
    gen = gen[gen["Energy Source 1"].isin(FOSSIL_ENERGY_SOURCES)]

    df = gen.merge(plant, on="Plant Code", how="inner")

    zone_lookup = zone_assignment.build_zone_lookup(iso)
    df = df.assign(zone=df["Plant Code"].map(zone_lookup)).dropna(subset=["zone"])

    member_states = RGGI_MEMBER_STATES_BY_YEAR.get(
        year, RGGI_MEMBER_STATES_BY_YEAR[max(RGGI_MEMBER_STATES_BY_YEAR)]
    )
    df = df.assign(is_member=df["State"].isin(member_states))

    cap = (
        df.groupby(["zone", "is_member"])["Nameplate Capacity (MW)"]
        .sum()
        .unstack(fill_value=0.0)
    )
    total = cap.sum(axis=1)
    member_cap = cap[True] if True in cap.columns else pd.Series(0.0, index=cap.index)
    share = (member_cap / total).fillna(0.0)
    return {zone: round(float(value), 4) for zone, value in share.items()}


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print the derived shares for each calibration year."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2023, 2024, 2025],
        help="Years to derive",
    )
    parser.add_argument("--iso", default="PJM")
    args = parser.parse_args(argv)

    for year in args.years:
        shares = compute_zone_shares(year, iso=args.iso)
        print(f"{year}:")
        for zone in sorted(shares):
            print(f"    {zone!r}: {shares[zone]},")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
