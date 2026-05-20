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
    python scripts/tag_mixed_plants.py --bins inputs/custom-bin-assignments.csv
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

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("tag_mixed_plants")

DEFAULT_BINS = REPO / "inputs" / "custom-bin-assignments.csv"

# Plant_Group -> (fuel tag, code digit). Same digit groups configs of one fuel.
_GROUP_TAG: dict[str, tuple[str, int]] = {
    "COAL": ("COAL", 1),
    "ST_GAS": ("ST", 2), "ST_CHP": ("ST", 2),
    "CT_PEAKER": ("CT", 3), "CT_CHP": ("CT", 3),
    "CC_REGULAR": ("CC", 4), "CC_CHP": ("CC", 4),
}


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
        dominant = (
            grp.groupby("_tag")["Nameplate_MW"].sum().idxmax()
        )
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bins", default=str(DEFAULT_BINS))
    args = parser.parse_args()

    path = Path(args.bins)
    bins = pd.read_csv(path)
    tagged, changes = tag_mixed_plants(bins)
    if not changes:
        logger.info("no mixed-fuel plant codes to tag (already split)")
        return
    tagged.to_csv(path, index=False)
    logger.info("tagged %d minor fuel portion(s) in %s:", len(changes), path)
    for c in changes:
        logger.info("  %s", c)


if __name__ == "__main__":
    main()
