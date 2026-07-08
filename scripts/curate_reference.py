"""Curate the ``reference`` clean datatype — heterogeneous lookup / crosswalk tables.

The reference datatype is the catch-all for the curated lookup tables that wire
the other datatypes together (see ``data/dictionary/schema/reference.schema.yaml``).
Each lookup table is intrinsically different, so the schema enforces *conventions*
(``lower_snake_case`` names, explicit unit suffixes, embedded provenance) and a
small set of canonical key columns (``plant_id`` / ``iso`` / ``zone`` / ``node``)
while allowing table-specific columns through (``allow_additional_columns=true``).

This script reads ONLY ``data/raw/reference`` and writes one schema-validated
Parquet file *per lookup table* through the frozen
:func:`scripts.lib.clean_io.write_clean` seam — never by hand-building a path.

Disambiguation convention (documented for the PR)
-------------------------------------------------
Reference tables share a single datatype, so we disambiguate them with the
``market`` partition slot, used here as a kebab-case *table name*. Each table
lands at::

    data/clean/reference/<table-name>/reference.parquet

The ``key`` column is a stable, self-describing per-row identifier of the form
``"<table-name>:<natural-key>"`` (the natural key is the plant code, which is
unique within each source table). Divergent raw key names are normalized onto
the standard keys — ``plantid`` / ``Plant_Code`` -> ``plant_id``,
``ERCOT_Zone`` -> ``zone`` — and table-specific columns are renamed to
``lower_snake_case`` with explicit unit suffixes (e.g. heat rate ->
``*_mmbtu_per_mwh``, percentages -> ``*_pct``, dimensionless ratios ->
``*_mult`` / ``*_frac``).

Idempotent and re-runnable: everything is derived from raw and the clean outputs
are overwritten in place.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_sim.config import paths
from scripts.lib import clean_io

RAW_DIR: Path = paths.REFERENCE_DIR


def _rel(path: Path) -> str:
    """Repo-relative path string for embedded provenance (``source=``)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# plant-registry: master plant registry, keyed by plant_id
# ---------------------------------------------------------------------------
def curate_plant_registry(raw_dir: Path = RAW_DIR) -> tuple[pd.DataFrame, str]:
    """Normalize ``master-plant-registry.csv`` into the plant-registry lookup.

    The raw file is already mostly snake_case; we normalize the key name
    (``plantid`` -> ``plant_id``), give the heat-rate / capacity-factor columns
    explicit unit suffixes, coerce the CHP indicator to a real boolean, and
    stamp a stable ``key``.
    """
    src = raw_dir / "master-plant-registry.csv"
    raw = pd.read_csv(src)

    df = raw.rename(
        columns={
            "plantid": "plant_id",
            # heat rate is MMBtu per MWh; capacity factor is a dimensionless fraction
            "annual_heat_rate": "annual_heat_rate_mmbtu_per_mwh",
            "annual_capacity_factor": "annual_capacity_factor_frac",
        }
    )

    # CHP indicator arrives as "Yes" / NaN — coerce to a real boolean flag
    # (blank/NaN means "not flagged" -> False, so the column carries no nulls).
    df["chp_flag"] = (
        df["chp_flag"]
        .astype("string")
        .str.strip()
        .str.lower()
        .eq("yes")
        .fillna(False)
        .astype(bool)
    )

    df["plant_id"] = df["plant_id"].astype("int64")
    df["key"] = "plant-registry:" + df["plant_id"].astype(str)
    df["key"] = df["key"].astype("string")

    df = _order_key_first(df)
    return df, _rel(src)


# ---------------------------------------------------------------------------
# bin-assignments: ERCOT custom commitment-bin assignments, keyed by plant_id
# ---------------------------------------------------------------------------
def curate_bin_assignments(raw_dir: Path = RAW_DIR) -> tuple[pd.DataFrame, str]:
    """Normalize ``custom-bin-assignments.csv`` into the bin-assignments lookup.

    Raw columns are TitleCase with mixed unit conventions. We map the plant code
    onto ``plant_id`` and ``ERCOT_Zone`` onto the standard ``zone`` key (stamping
    ``iso='ERCOT'`` for context), and rewrite table-specific columns to
    snake_case with explicit unit suffixes (heat rate -> ``*_mmbtu_per_mwh``,
    dispatch shares -> ``*_pct``, heat-rate multipliers -> ``*_mult``).
    """
    src = raw_dir / "custom-bin-assignments.csv"
    raw = pd.read_csv(src)

    df = raw.rename(
        columns={
            "Plant_Code": "plant_id",
            "ERCOT_Zone": "zone",
            "Plant_Group": "plant_group",
            "Bin_Number": "bin_number",
            "Bin_Label": "bin_label",
            "Plant_Name": "plant_name",
            "Nameplate_MW": "nameplate_mw",
            "Plant_Avg_HR_MMBtu_MWh": "plant_avg_heat_rate_mmbtu_per_mwh",
            "Config": "config",
            "Turbine_Class": "turbine_class",
            "Pct_Must_Run": "must_run_pct",
            "Pct_Committed": "committed_pct",
            "Pct_Economic": "economic_pct",
            "Pct_Peaking": "peaking_pct",
            "Min_Run_Hours": "min_run_hours",
            "Min_Down_Hours": "min_down_hours",
            "HR_Mult_Must_Run": "heat_rate_mult_must_run",
            "HR_Mult_Committed": "heat_rate_mult_committed",
            "HR_Mult_Economic": "heat_rate_mult_economic",
            "HR_Mult_Peaking": "heat_rate_mult_peaking",
        }
    )

    df["plant_id"] = df["plant_id"].astype("int64")
    df["iso"] = pd.array(["ERCOT"] * len(df), dtype="string")
    df["zone"] = df["zone"].astype("string")
    df["key"] = ("bin-assignments:" + df["plant_id"].astype(str)).astype("string")

    df = _order_key_first(df)
    return df, _rel(src)


# ---------------------------------------------------------------------------
# coal-region-crosswalk: coal plant -> EIA producing-region map, per ISO
# ---------------------------------------------------------------------------
def curate_coal_region_crosswalk(raw_dir: Path = RAW_DIR) -> tuple[pd.DataFrame, str]:
    """Normalize ``coal_region_crosswalk.csv`` into the coal-region-crosswalk lookup.

    Built by ``scripts/derive_coal_region_crosswalk.py`` from each ISO's coal
    fleet + ``market_sim.data.coal.coal_supply_class`` — maps every coal plant
    onto the EIA Annual Coal Report producing region/state its coal is
    sourced from (see that script's docstring for the resolution rules). Feeds
    a future re-derivation of the coal-vs-gas passthrough sigmoids (issue
    #1347) with a real per-region commodity price instead of the current
    hand-tuned, cross-ISO-byte-copied literals.
    """
    src = raw_dir / "coal_region_crosswalk.csv"
    raw = pd.read_csv(src)

    df = raw.rename(columns={"plant_code": "plant_id"})
    df["plant_id"] = df["plant_id"].astype("int64")
    df["iso"] = df["iso"].astype("string")
    df["zone"] = pd.array([pd.NA] * len(df), dtype="string")
    df["key"] = (
        "coal-region-crosswalk:" + df["iso"] + ":" + df["plant_id"].astype(str)
    ).astype("string")

    df = _order_key_first(df)
    return df, _rel(src)


def _order_key_first(df: pd.DataFrame) -> pd.DataFrame:
    """Put canonical keys first for readability (``key`` then standard keys)."""
    lead = [c for c in ("key", "plant_id", "iso", "zone", "node") if c in df.columns]
    rest = [c for c in df.columns if c not in lead]
    return df[lead + rest]


# Registry of (table-name, builder); table-name doubles as the `market` slot.
TABLES = {
    "plant-registry": curate_plant_registry,
    "bin-assignments": curate_bin_assignments,
    "coal-region-crosswalk": curate_coal_region_crosswalk,
}


def curate(raw_dir: Path = RAW_DIR) -> dict[str, Path]:
    """Curate every reference lookup table and return ``{table-name: path}``.

    Each table is validated by ``write_clean`` on the way in and re-validated
    via ``validate_clean`` after writing (a round-trip guard).
    """
    written: dict[str, Path] = {}
    for name, builder in TABLES.items():
        df, source = builder(raw_dir)
        path = clean_io.write_clean(df, "reference", market=name, source=source)
        clean_io.validate_clean(path)  # raises SchemaError on any drift
        written[name] = path
    return written


def main() -> None:
    written = curate()
    for name, path in written.items():
        print(f"reference[{name}] -> {path}")


if __name__ == "__main__":
    main()
