"""Tag co-located fuel portions of a plant as distinct dispatch entities.

A handful of physical plants run units of different fuel classes behind one
EIA plant code — W A Parish (coal + gas steam), Barney M Davis (gas CC + gas
steam). The CAMPD bin file already splits them into separate dispatch rows by
``Plant_Group``, but every row keeps the shared plant code, so plant-keyed data
(emission rates, fuel costs) cannot distinguish the coal portion from the gas
portion.

This rewrites the bin file so each fuel class of a mixed plant is its own
tagged entity:

* the largest-capacity fuel class keeps the real EIA plant code (so its
  fuel-cost and coal-supply wiring is unchanged);
* every other fuel class gets a synthetic code ``real_code * 10 + fuel_digit``
  (coal=1, ST=2, CT=3, CC=4) and a fuel tag appended to its name.

The split is by capacity here; once unit-level CEMS is available, each tagged
code can take its own measured emission rate. Idempotent: a plant whose code no
longer spans multiple fuel classes is left untouched.

Usage:
    python scripts/tag_mixed_plants.py
    python scripts/tag_mixed_plants.py --bins data/raw/reference/custom-bin-assignments.csv
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import CAMPD_BINS_CSV, PLANT_REGISTRY_CSV  # noqa: E402
from market_sim.config.plant_taxonomy import COAL_ARTIFACT_FAMILY, COAL_CLASSES  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("tag_mixed_plants")

# Curated reference sheets under the single W1 data root
# (paths.REFERENCE_DIR = data/raw/reference); the pre-W1 ``inputs/`` root was
# removed by the relocation.
DEFAULT_BINS = CAMPD_BINS_CSV
DEFAULT_REGISTRY = PLANT_REGISTRY_CSV

# Plant_Group -> (fuel tag, code digit). Same digit groups configs of one fuel.
_GROUP_TAG: dict[str, tuple[str, int]] = {
    # Every coal subclass tags as the registry's coal family token (COAL-SUB).
    **{c: (COAL_ARTIFACT_FAMILY, 1) for c in COAL_CLASSES},
    "ST_GAS": ("ST", 2),
    "ST_CHP": ("ST", 2),
    "CT_PEAKER": ("CT", 3),
    "CT_CHP": ("CT", 3),
    "CC_REGULAR": ("CC", 4),
    "CC_CHP": ("CC", 4),
}

# Per-tag registry metadata (fuel_type, prime_mover, primary_fuel, technology).
_TAG_META: dict[str, dict[str, str]] = {
    COAL_ARTIFACT_FAMILY: {
        "fuel_type": "SUB",
        "prime_mover": "ST",
        "primary_fuel": "SUB",
        "technology": "Conventional Steam Coal",
    },
    "ST": {
        "fuel_type": "NG",
        "prime_mover": "ST",
        "primary_fuel": "NG",
        "technology": "Natural Gas Steam Turbine",
    },
    "CT": {
        "fuel_type": "NG",
        "prime_mover": "GT",
        "primary_fuel": "NG",
        "technology": "Natural Gas Fired Combustion Turbine",
    },
    "CC": {
        "fuel_type": "NG",
        "prime_mover": "CA",
        "primary_fuel": "NG",
        "technology": "Natural Gas Fired Combined Cycle",
    },
}

# Registry columns cleared on a newly-created child row — portion-specific
# values that only unit-level data can fill.
_CLEAR_ON_CHILD: tuple[str, ...] = (
    "parasitic_load_pct",
    "annual_capacity_factor",
    "co2_kg_per_mwh_net",
    "nox_kg_per_mwh_net",
    "so2_kg_per_mwh_net",
    "startup_co2_kg",
    "startup_nox_kg",
    "startup_so2_kg",
    "starts_per_year",
    "heat_rate_bin",
)


def _tag(plant_group: str) -> tuple[str, int]:
    return _GROUP_TAG.get(plant_group, ("OTHER", 9))


def _name_stem(name: str) -> str:
    """Return a plant name without its parenthetical or trailing config token."""
    stem = str(name).split("(")[0].strip()
    return re.sub(r"\s+(ST|CT|CC|GT|IC)\d*$", "", stem).strip()


def tag_mixed_plants(bins: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Return ``(bins, changes)`` with mixed plants' minor fuels re-tagged."""
    bins = bins.copy()
    bins["_tag"] = bins["Plant_Group"].map(lambda g: _tag(g)[0])
    bins["_digit"] = bins["Plant_Group"].map(lambda g: _tag(g)[1])
    existing_codes = set(bins["Plant_Code"].astype(int))
    changes: list[str] = []

    for code, grp in bins.groupby("Plant_Code"):
        tags = grp["_tag"].unique()
        if len(tags) < 2:
            continue  # single fuel class — nothing to split
        # Dominant tag (most nameplate) keeps the real EIA code.
        dominant = grp.groupby("_tag")["Nameplate_MW"].sum().idxmax()
        for tag in tags:
            rows = (bins["Plant_Code"] == code) & (bins["_tag"] == tag)
            stem = _name_stem(bins.loc[rows, "Plant_Name"].iloc[0])
            bins.loc[rows, "Plant_Name"] = f"{stem} [{tag}]"
            if tag == dominant:
                continue
            digit = int(bins.loc[rows, "_digit"].iloc[0])
            new_code = int(code) * 10 + digit
            if new_code in existing_codes:
                raise ValueError(
                    f"synthetic code {new_code} for plant {code}/{tag} collides "
                    f"with an existing plant code"
                )
            existing_codes.add(new_code)
            bins.loc[rows, "Plant_Code"] = new_code
            changes.append(
                f"{int(code)} {tag}: code -> {new_code}, "
                f"name -> '{bins.loc[rows, 'Plant_Name'].iloc[0]}'"
            )

    return bins.drop(columns=["_tag", "_digit"]), changes


def _bin_attrs(bins: pd.DataFrame, code: int) -> dict:
    """Return derived registry attributes for one (post-tag) plant code."""
    rows = bins[bins["Plant_Code"] == code]
    group = str(rows["Plant_Group"].iloc[0])
    tag = _tag(group)[0]
    return {
        "plant_name": str(rows["Plant_Name"].iloc[0]),
        "nameplate_capacity_mw": round(float(rows["Nameplate_MW"].sum()), 1),
        "plant_group": group,
        "annual_heat_rate": float(rows["Plant_Avg_HR_MMBtu_MWh"].iloc[0]),
        **_TAG_META.get(tag, {}),
    }


def sync_registry_to_bins(
    bins: pd.DataFrame,
    registry: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    """Return ``(registry, changes)`` reconciled to the tagged bin file.

    For each split family — a synthetic child code ``parent*10+digit`` whose
    parent is a real registry plant — the parent row is updated to its
    dominant fuel portion and a child row is added (copied from the parent so
    it keeps the real vintage and balancing authority, with portion-specific
    derived columns cleared for later unit-level data).
    """
    registry = registry.copy()
    reg_codes = set(registry["plantid"].astype(int))
    bin_codes = set(bins["Plant_Code"].astype(int))
    children = {
        c
        for c in bin_codes
        if c not in reg_codes and (c // 10) in reg_codes and c % 10 in {1, 2, 3, 4}
    }
    changes: list[str] = []

    for child in sorted(children):
        parent = child // 10
        # Update the parent (dominant) row to its own fuel portion.
        for col, val in _bin_attrs(bins, parent).items():
            registry.loc[registry["plantid"] == parent, col] = val
        changes.append(f"updated registry row {parent} -> dominant portion")
        # Add the child row, copied from the parent's vintage / BA metadata.
        new_row = registry[registry["plantid"] == parent].iloc[0].copy()
        new_row["plantid"] = child
        for col, val in _bin_attrs(bins, child).items():
            new_row[col] = val
        for col in _CLEAR_ON_CHILD:
            if col in new_row.index:
                new_row[col] = pd.NA
        registry = pd.concat([registry, new_row.to_frame().T], ignore_index=True)
        changes.append(f"added registry row {child} ('{new_row['plant_name']}')")

    return registry, changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bins", default=str(DEFAULT_BINS))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    args = parser.parse_args()

    bins_path = Path(args.bins)
    bins = pd.read_csv(bins_path)
    tagged, changes = tag_mixed_plants(bins)
    if changes:
        tagged.to_csv(bins_path, index=False)
        logger.info("tagged %d minor fuel portion(s) in %s:", len(changes), bins_path)
        for c in changes:
            logger.info("  %s", c)
    else:
        logger.info("bins already split — reconciling registry only")
        tagged = bins

    # Reconcile the registry to the (now tagged) bins, idempotently.
    reg_path = Path(args.registry)
    if reg_path.exists():
        registry, reg_changes = sync_registry_to_bins(tagged, pd.read_csv(reg_path))
        if reg_changes:
            registry.to_csv(reg_path, index=False)
            logger.info("reconciled registry %s:", reg_path)
            for c in reg_changes:
                logger.info("  %s", c)
        else:
            logger.info("registry already in sync with bins")


if __name__ == "__main__":
    main()
