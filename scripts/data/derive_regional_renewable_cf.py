"""Derive each grid's measured new-build wind/solar capacity factor from eGRID.

The marginal-abatement page prices a project on the output it would actually
deliver ON THAT GRID. NREL ATB publishes ONE national capacity factor per
technology (``NEW_ENTRY_COSTS[tech]["base_cf"]`` — wind 0.38, solar 0.27), and
the committed ATB extract carries CAPEX and Fixed O&M only (one resource class
each: LandbasedWind/Class4, UtilityPV/Class5), so the regional number has to
come from measured plant data. This script derives it, and
:data:`market_sim.config.constants.REGIONAL_RENEWABLE_CF` holds the result.

METHOD. EPA eGRID, generator level (``GEN<yy>``), joined to the plant sheet
(``PLNT<yy>``) for the balancing-authority code:

  * ``GENSTAT == "OP"`` and ``NAMEPCAP > 0`` — operating nameplate only.
  * ``FUELG1`` in {``WND``, ``SUN``} — the generator's own primary fuel, never
    a plant-level rollup that would mix a hybrid's PV and battery MW.
  * ``GENYRONL <= vintage_year - 1`` — a unit that came online DURING the
    reported year has a part-year ``CFACT`` and would bias the average down.
  * ``GENYRONL >= MIN_COD`` — the NEW-BUILD cohort. The question the abatement
    page asks is what a project built TODAY yields, not what the installed base
    averages: ERCOT's whole wind fleet reads 0.335 against 0.358 for the
    post-2018 cohort, and the 1980s-90s CAISO turbines drag that grid's
    all-vintage wind to 0.261 against 0.371.
  * Capacity-weighted across generators and pooled across ``VINTAGE_YEARS`` so
    one windy or cloudy year cannot set a grid's number.

WHAT THE NUMBER INCLUDES, stated because it is a real modelling choice:
``CFACT`` is net generation over nameplate x 8760, so it is measured NET OF
CURTAILMENT. That is deliberate — the abatement denominator is DELIVERED MWh,
and a curtailed MWh is neither sold nor abating. It does mean a grid that
curtails heavily (ERCOT solar) reads a higher cost per delivered MWh than its
as-available resource quality alone implies, which is the honest answer to
"what does abatement cost HERE".

RULE 13 ``[R-MEASURED]``. This is a reproducible physical input, not an
outcome fed back to close a residual: it is the resource quality of a region,
it regenerates for a forward year from the then-current eGRID vintage (or from
ATB's own class CFs where no measured fleet exists yet), and it responds to
changed conditions. Rule 23 ``[R-FROZEN-DERIVE]``: re-derive ONLY when a new
eGRID vintage lands, and cite the data change in the commit.

Usage::

    python scripts/data/derive_regional_renewable_cf.py            # print block
    python scripts/data/derive_regional_renewable_cf.py --check    # CI assert
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EGRID_DIR = REPO / "data" / "raw" / "fleet-egrid"

# eGRID vintages pooled into one capacity-weighted average. Three years damps
# weather noise without reaching back into a materially different fleet.
VINTAGE_YEARS: dict[int, str] = {
    2022: "egrid2022_data.xlsx",
    2023: "egrid2023_data_rev2.xlsx",
    2024: "egrid2024_data.xlsx",
}

# Earliest commercial-operation year in the new-build cohort. 2018 is the
# turbine/module generation a project financed today actually resembles.
MIN_COD = 2018

# The BA -> region mapping is NOT redeclared here. It is read from the model's
# own footprint registry, ``fleet.models.ISO_TO_BA_CODES`` (rule 24
# ``[R-REGISTRY]``: one registry, no second copy that can drift out of step
# with the fleet the solve actually builds). That registry is what makes NWPP
# work: it is a POOL OF SEVENTEEN BALANCING AUTHORITIES rather than a BA, and
# a hand-written one-BA-per-region table could only ever drop it or reduce it
# to an arbitrary seventeenth of its fleet.
#
# ``ISO_NERC_REGION_ADMISSION`` rides along for the same reason. The eGRID BA
# code is respondent-entered and occasionally wrong across an interconnect
# seam, so NWPP admits a plant only when its NERC region is WECC; the 1:1
# regions carry no predicate and admit on the BA code alone, exactly as the
# solve path does.
#
# A region with no measured fleet for a technology simply gets no entry, and
# the consumer falls back to the national ATB base CF.

FUEL_TO_TECH: dict[str, str] = {"WND": "wind", "SUN": "solar"}

# Below this much pooled nameplate a grid's cohort is too thin to average, so
# no constant is emitted and the consumer falls back to the national CF.
MIN_COHORT_MW = 100.0


def ba_to_iso() -> "tuple[dict[str, str], dict[str, str]]":
    """Return ``(BA code -> region, region -> required NERC region)``.

    Both come straight from the model's footprint registry; see the note above
    the constants for why this is read rather than redeclared.
    """
    sys.path.insert(0, str(REPO / "src"))
    from market_sim.data.fleet.models import (
        ISO_NERC_REGION_ADMISSION,
        ISO_TO_BA_CODES,
    )

    return (
        {ba: iso for iso, bas in ISO_TO_BA_CODES.items() for ba in bas},
        dict(ISO_NERC_REGION_ADMISSION),
    )


def load_cohort():
    """Return the pooled new-build wind/solar generator cohort as a DataFrame."""
    import pandas as pd

    ba_map, nerc_required = ba_to_iso()
    frames = []
    for year, fname in VINTAGE_YEARS.items():
        path = EGRID_DIR / fname
        if not path.exists():
            raise SystemExit(f"missing eGRID vintage: {path}")
        suffix = str(year)[2:]
        gen = pd.read_excel(path, sheet_name=f"GEN{suffix}", header=1)
        plant = pd.read_excel(
            path,
            sheet_name=f"PLNT{suffix}",
            header=1,
            usecols=["ORISPL", "BACODE", "NERC"],
        )
        gen = gen.merge(plant.drop_duplicates("ORISPL"), on="ORISPL", how="left")
        gen = gen[
            (gen["GENSTAT"] == "OP")
            & (gen["NAMEPCAP"] > 0)
            & gen["CFACT"].notna()
            & (gen["GENYRONL"] <= year - 1)
            & (gen["GENYRONL"] >= MIN_COD)
            & gen["FUELG1"].isin(FUEL_TO_TECH)
        ].copy()
        gen["iso"] = gen["BACODE"].map(ba_map)
        # Footprint admission: where the registry names a required NERC region
        # for a pool, a row carrying a member BA code but the wrong NERC region
        # is a respondent mis-file across an interconnect seam, not a plant in
        # that pool. Regions with no declared predicate are untouched.
        for iso, nerc in nerc_required.items():
            wrong = (gen["iso"] == iso) & (gen["NERC"] != nerc)
            gen.loc[wrong, "iso"] = None
        gen["tech"] = gen["FUELG1"].map(FUEL_TO_TECH)
        gen["vintage"] = year
        frames.append(
            gen[gen["iso"].notna()][["vintage", "iso", "tech", "NAMEPCAP", "CFACT"]]
        )
    return pd.concat(frames, ignore_index=True)


def derive() -> "dict[str, dict[str, float]]":
    """Return ``{tech: {ISO: capacity-weighted CF}}`` from the pooled cohort."""
    cohort = load_cohort()
    n_years = cohort["vintage"].nunique()
    out: dict[str, dict[str, float]] = {}
    for tech, block in cohort.groupby("tech"):
        rows: dict[str, float] = {}
        for iso, grp in block.groupby("iso"):
            mw = grp["NAMEPCAP"].sum() / n_years
            if mw < MIN_COHORT_MW:
                continue
            rows[str(iso)] = round(
                float((grp["CFACT"] * grp["NAMEPCAP"]).sum() / grp["NAMEPCAP"].sum()), 4
            )
        out[str(tech)] = dict(sorted(rows.items()))
    return out


def render(table: "dict[str, dict[str, float]]") -> str:
    """Return the paste-ready ``constants.py`` literal for ``table``."""
    lines = ["REGIONAL_RENEWABLE_CF: dict[str, dict[str, float]] = {"]
    for tech in sorted(table):
        lines.append(f'    "{tech}": {{')
        for iso, cf in table[tech].items():
            lines.append(f'        "{iso}": {cf:.4f},')
        lines.append("    },")
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="compare against the committed constant and exit non-zero on drift",
    )
    args = ap.parse_args()

    table = derive()

    if args.check:
        sys.path.insert(0, str(REPO / "src"))
        from market_sim.config.constants import REGIONAL_RENEWABLE_CF

        if REGIONAL_RENEWABLE_CF != table:
            print("REGIONAL_RENEWABLE_CF has DRIFTED from the eGRID derivation.")
            print("committed:", REGIONAL_RENEWABLE_CF)
            print("derived  :", table)
            raise SystemExit(1)
        print("REGIONAL_RENEWABLE_CF matches the eGRID derivation.")
        return

    print(
        f"# eGRID {min(VINTAGE_YEARS)}-{max(VINTAGE_YEARS)} pooled, "
        f"COD >= {MIN_COD}, capacity-weighted\n"
    )
    print(render(table))


if __name__ == "__main__":
    main()
