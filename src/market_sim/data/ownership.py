"""EIA-860 ownership pipeline: loader, parent mapping and attribution.

This module turns raw EIA-860 ownership data into a generator-to-parent
mapping and uses it to attribute fleet capacity and dispatch emissions to
ultimate parent companies.

The single most important design fact (see ``docs/us-gen-ownership.md`` §1) is
that EIA-860 **Schedule 4 is sparse**: a generator appears there only if it
is jointly owned or wholly owned by an entity other than its operator. Any
generator absent from Schedule 4 is 100% owned by the Schedule 3 operator.
:func:`load_eia860_ownership` implements that rule.

Tax-equity ownership is generally invisible in EIA-860 — ``percent_owned``
reflects legal/cash-equity ownership, not the partnership-flip economic
allocation of tax-equity-financed renewables. That limitation is documented
here and not corrected.
"""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

import pandas as pd

from market_sim.data.ownership_config import (
    MNA_OVERLAYS,
    PARENT_COMPANY_LOOKUP,
    UNKNOWN_PARENT,
    OwnershipChange,
)

logger = logging.getLogger(__name__)

# Tolerance for the per-generator ``percent_owned`` summation check. EIA
# does not enforce the constraint at survey time, so rounding drift is
# expected (see docs/us-gen-ownership.md §1).
PERCENT_OWNED_TOLERANCE: float = 0.02

# Canonical columns returned by :func:`load_eia860_ownership`.
OWNERSHIP_COLUMNS: list[str] = [
    "plant_code",
    "generator_id",
    "owner_utility_id",
    "owner_name",
    "percent_owned",
    "nameplate_capacity_mw",
    "energy_source_code",
    "prime_mover_code",
    "balancing_authority_code",
    "state",
    "status",
]

# Source column → canonical name aliases, lower-cased with spaces and
# punctuation collapsed to underscores. EIA renames sheets and columns
# between vintages, so the loader is deliberately defensive about drift.
_GENERATOR_ALIASES: dict[str, set[str]] = {
    "plant_code": {"plant_code", "plant_id", "oris_code"},
    "generator_id": {"generator_id", "gen_id", "unit_id"},
    "owner_utility_id": {"utility_id", "operator_id", "owner_utility_id"},
    "owner_name": {"utility_name", "operator_name", "owner_name"},
    "nameplate_capacity_mw": {
        "nameplate_capacity_mw",
        "nameplate_capacity",
        "namepcap",
    },
    "energy_source_code": {
        "energy_source_code",
        "energy_source_1",
        "energy_source",
    },
    "prime_mover_code": {"prime_mover_code", "prime_mover"},
    "state": {"state", "plant_state"},
    "status": {"status", "status_description"},
}

_OWNER_ALIASES: dict[str, set[str]] = {
    "plant_code": {"plant_code", "plant_id", "oris_code"},
    "generator_id": {"generator_id", "gen_id", "unit_id"},
    "owner_utility_id": {
        "owner_utility_id",
        "ownership_id",
        "owner_id",
    },
    "owner_name": {"owner_name", "ownership_name"},
    "percent_owned": {"percent_owned", "percent_ownership", "ownership_pct"},
    "state": {"state", "plant_state"},
    "status": {"status", "status_description"},
}

_PLANT_ALIASES: dict[str, set[str]] = {
    "plant_code": {"plant_code", "plant_id", "oris_code"},
    "balancing_authority_code": {
        "balancing_authority_code",
        "ba_code",
        "balancing_authority",
    },
    "state": {"state", "plant_state"},
}


def _normalize_key(name: object) -> str:
    """Return a column name normalized for alias matching."""
    text = str(name).strip().lower()
    for ch in (" ", "-", "/", "(", ")", "."):
        text = text.replace(ch, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


def _rename_to_canonical(
    df: pd.DataFrame, aliases: dict[str, set[str]]
) -> pd.DataFrame:
    """Rename a DataFrame's columns to canonical names via an alias map.

    Args:
        df: A raw EIA-860 sheet.
        aliases: Canonical name → set of accepted source names.

    Returns:
        ``df`` with recognized columns renamed; duplicate canonical columns
        keep their first occurrence.
    """
    lookup: dict[str, str] = {}
    for canon, names in aliases.items():
        for name in names:
            lookup[name] = canon

    rename: dict[object, str] = {}
    for col in df.columns:
        key = _normalize_key(col)
        if key in lookup:
            rename[col] = lookup[key]
    df = df.rename(columns=rename)
    return df.loc[:, ~df.columns.duplicated()]


def _read_eia860_sheet(
    path: Path,
    workbook_marker: str,
    sheet: str,
    parquet_names: list[str],
) -> pd.DataFrame:
    """Read one EIA-860 sheet from a zip archive or a directory of parquet.

    Args:
        path: Either the EIA-860 annual zip, or a directory holding the
            per-sheet parquet files written by ``scripts/data/process_eia860.py``.
        workbook_marker: Substring identifying the workbook inside a zip
            (e.g. ``"Owner_Y"``).
        sheet: Sheet name to read inside the zipped workbook.
        parquet_names: Candidate parquet filenames to try, in priority
            order, when ``path`` is a directory.

    Returns:
        The raw sheet as a DataFrame.

    Raises:
        FileNotFoundError: When no matching workbook or parquet is found.
    """
    path = Path(path)
    if path.is_dir():
        for name in parquet_names:
            parquet = path / name
            if parquet.exists():
                return pd.read_parquet(parquet)
        raise FileNotFoundError(
            f"no EIA-860 parquet in {path} matching any of {parquet_names}"
        )

    with zipfile.ZipFile(path) as zf:
        name = next((n for n in zf.namelist() if workbook_marker in n), None)
        if name is None:
            raise FileNotFoundError(
                f"no EIA-860 workbook matching '{workbook_marker}' in {path}"
            )
        # EIA-860 workbooks carry a one-line title above the header row.
        return pd.read_excel(io.BytesIO(zf.read(name)), sheet_name=sheet, header=1)


def load_eia860_ownership(eia860_path: Path, year: int) -> pd.DataFrame:
    """Load and join EIA-860 Schedule 3 (generators) and Schedule 4 (owners).

    Implements the sparse-ownership rule: every operable generator starts
    from Schedule 3 with its operator as the implicit 100% owner; wherever
    a ``(plant_code, generator_id)`` pair appears in Schedule 4, those owner
    rows *replace* the implicit operator row.

    Args:
        eia860_path: The EIA-860 annual zip, or a directory of the per-sheet
            parquet files produced by ``scripts/data/process_eia860.py``.
        year: Reporting year of the EIA-860 vintage; recorded for traceability.

    Returns:
        One row per generator-owner pair, with columns
        :data:`OWNERSHIP_COLUMNS`. ``percent_owned`` is a decimal in
        ``[0, 1]``; ``owner_utility_id`` is a nullable integer.
    """
    logger.info("Loading EIA-860 ownership for reporting year %d", year)

    generators = _rename_to_canonical(
        _read_eia860_sheet(
            eia860_path,
            "Generator_Y",
            "Operable",
            ["eia860_generator_operable.parquet", "eia860_generator.parquet"],
        ),
        _GENERATOR_ALIASES,
    )
    owners = _rename_to_canonical(
        _read_eia860_sheet(eia860_path, "Owner_Y", "Owner", ["eia860_owner.parquet"]),
        _OWNER_ALIASES,
    )
    plants = _rename_to_canonical(
        _read_eia860_sheet(eia860_path, "Plant_Y", "Plant", ["eia860_plant.parquet"]),
        _PLANT_ALIASES,
    )

    generators = _coerce_keys(generators)
    owners = _coerce_keys(owners)
    plants = _coerce_keys(plants)

    # Plant-level balancing authority and state, joined onto both schedules.
    ba_by_plant = plants.drop_duplicates("plant_code").set_index("plant_code")[
        ["balancing_authority_code", "state"]
    ]

    # Schedule 3 baseline: operator as the implicit 100% owner.
    base = generators.copy()
    base["percent_owned"] = 1.0
    if "owner_utility_id" not in base.columns:
        base["owner_utility_id"] = pd.NA

    base_keys = set(zip(base["plant_code"], base["generator_id"], strict=True))

    # Schedule 4 owner rows replace the operator row for the generators they
    # cover. ``percent_owned`` from EIA is already a 0–1 decimal.
    if not owners.empty:
        owners = owners.copy()
        owners["percent_owned"] = pd.to_numeric(
            owners["percent_owned"], errors="coerce"
        )
        owned_keys = set(zip(owners["plant_code"], owners["generator_id"], strict=True))
        # Generator attributes (capacity, fuel, mover) come from Schedule 3.
        gen_attrs = generators.drop_duplicates(["plant_code", "generator_id"])
        attr_cols = [
            c
            for c in (
                "nameplate_capacity_mw",
                "energy_source_code",
                "prime_mover_code",
                "status",
            )
            if c in gen_attrs.columns
        ]
        owners = owners.merge(
            gen_attrs[["plant_code", "generator_id", *attr_cols]],
            on=["plant_code", "generator_id"],
            how="left",
            suffixes=("", "_gen"),
        )
        for col in attr_cols:
            gen_col = f"{col}_gen"
            if gen_col in owners.columns:
                owners[col] = owners[col].fillna(owners[gen_col])
                owners = owners.drop(columns=gen_col)
    else:
        owned_keys = set()

    # Keep Schedule 3 rows only for generators absent from Schedule 4.
    if owned_keys:
        base_pairs = pd.MultiIndex.from_arrays(
            [base["plant_code"], base["generator_id"]]
        )
        base_unowned = base[~base_pairs.isin(owned_keys)]
    else:
        base_unowned = base

    combined = pd.concat([base_unowned, owners], ignore_index=True)

    # Attach plant-level balancing authority and state.
    combined = combined.merge(
        ba_by_plant, on="plant_code", how="left", suffixes=("", "_plant")
    )
    if "state_plant" in combined.columns:
        combined["state"] = combined["state"].fillna(combined["state_plant"])
        combined = combined.drop(columns="state_plant")

    for col in OWNERSHIP_COLUMNS:
        if col not in combined.columns:
            combined[col] = pd.NA

    combined["nameplate_capacity_mw"] = pd.to_numeric(
        combined["nameplate_capacity_mw"], errors="coerce"
    )
    combined["owner_utility_id"] = pd.to_numeric(
        combined["owner_utility_id"], errors="coerce"
    ).astype("Int64")

    n_joint = len(owned_keys)
    n_total = len(base_keys | owned_keys)
    logger.info(
        "EIA-860 ownership: %d generators, %d in Schedule 4 (jointly or "
        "non-operator owned)",
        n_total,
        n_joint,
    )
    return combined[OWNERSHIP_COLUMNS].reset_index(drop=True)


def _coerce_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce ``plant_code`` to int and ``generator_id`` to a clean string.

    Rows whose ``plant_code`` is not numeric (EIA footer rows) are dropped.
    """
    df = df.copy()
    if "plant_code" in df.columns:
        df["plant_code"] = pd.to_numeric(df["plant_code"], errors="coerce")
        df = df[df["plant_code"].notna()]
        df["plant_code"] = df["plant_code"].astype("int64")
    if "generator_id" in df.columns:
        df["generator_id"] = df["generator_id"].astype("string").str.strip()
    return df.reset_index(drop=True)


def validate_percent_owned(
    ownership_df: pd.DataFrame, tolerance: float = PERCENT_OWNED_TOLERANCE
) -> pd.DataFrame:
    """Return generators whose ``percent_owned`` does not sum to 1.0.

    Args:
        ownership_df: A frame with ``plant_code``, ``generator_id`` and
            ``percent_owned`` columns.
        tolerance: Allowed absolute deviation from 1.0.

    Returns:
        One row per offending generator with the observed share total. An
        empty frame means every generator's ownership shares are consistent.
    """
    totals = (
        ownership_df.groupby(["plant_code", "generator_id"], dropna=False)[
            "percent_owned"
        ]
        .sum()
        .reset_index(name="share_total")
    )
    return totals[(totals["share_total"] - 1.0).abs() > tolerance]


def build_parent_mapping(
    ownership_df: pd.DataFrame,
    as_of_date: str = "2026-01-15",
    parent_lookup: dict[int, str] | None = None,
    mna_overlays: list[OwnershipChange] | None = None,
) -> pd.DataFrame:
    """Map every generator-owner row to a canonical parent company.

    The ``as_of_date`` is decisive: the same EIA vintage maps to different
    parents depending on which M&A deals have closed by that date.

    Steps:

    1. Join ``owner_utility_id`` to :data:`PARENT_COMPANY_LOOKUP`.
    2. Apply every M&A overlay whose ``effective_date <= as_of_date`` and
       whose ``status == "closed"``, reassigning ``from_parent`` rows to
       ``to_parent``.
    3. Flag rows touched by ``pending`` or ``announced`` deals in a
       ``pending_change`` column without reassigning their parent.
    4. Generators with an unresolved owner get ``parent_company =
       "Other/Unknown"``.

    Args:
        ownership_df: Output of :func:`load_eia860_ownership`.
        as_of_date: ISO ``YYYY-MM-DD`` snapshot date for the overlay logic.
        parent_lookup: Override for :data:`PARENT_COMPANY_LOOKUP` (testing).
        mna_overlays: Override for :data:`MNA_OVERLAYS` (testing).

    Returns:
        ``ownership_df`` with two columns added: ``parent_company`` and
        ``ownership_mw`` (``nameplate_capacity_mw * percent_owned``), plus a
        ``pending_change`` column describing any non-closed deal that would
        affect the row.
    """
    lookup = PARENT_COMPANY_LOOKUP if parent_lookup is None else parent_lookup
    overlays = MNA_OVERLAYS if mna_overlays is None else mna_overlays

    df = ownership_df.copy()

    # Step 1 — static subsidiary → parent rollup.
    owner_id = df["owner_utility_id"]
    df["parent_company"] = owner_id.map(lookup).fillna(UNKNOWN_PARENT)
    df["pending_change"] = pd.NA

    # Steps 2 & 3 — date-aware M&A overlays, applied oldest deal first.
    closed = sorted(
        (o for o in overlays if o.status == "closed"),
        key=lambda o: o.effective_date,
    )
    for overlay in closed:
        if overlay.effective_date > as_of_date:
            continue
        mask = _overlay_mask(df, overlay)
        if mask.any():
            df.loc[mask, "parent_company"] = overlay.to_parent

    for overlay in overlays:
        if overlay.status == "closed":
            continue
        mask = _overlay_mask(df, overlay)
        if mask.any():
            df.loc[mask, "pending_change"] = f"{overlay.status}: {overlay.description}"

    # Step 4 — ownership-weighted capacity.
    df["ownership_mw"] = pd.to_numeric(
        df["nameplate_capacity_mw"], errors="coerce"
    ) * pd.to_numeric(df["percent_owned"], errors="coerce")
    return df


def _overlay_mask(df: pd.DataFrame, overlay: OwnershipChange) -> pd.Series:
    """Return the boolean row mask an M&A overlay applies to.

    Rows are matched on ``source_utility_ids`` when that list is non-empty,
    otherwise on the currently mapped ``parent_company == from_parent``.
    The match is then narrowed to ``plant_codes`` when that field is not
    ``None`` (an empty ``plant_codes`` list therefore matches nothing).
    """
    if overlay.source_utility_ids:
        mask = df["owner_utility_id"].isin(overlay.source_utility_ids)
    else:
        mask = df["parent_company"] == overlay.from_parent

    if overlay.plant_codes is not None:
        mask = mask & df["plant_code"].isin(overlay.plant_codes)
    return mask


def summarize_fleet_by_parent(
    parent_df: pd.DataFrame,
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Aggregate ownership-weighted capacity by parent company.

    Args:
        parent_df: Output of :func:`build_parent_mapping`.
        group_cols: Extra grouping columns alongside ``parent_company``
            (e.g. ``["energy_source_code", "balancing_authority_code"]``).
            Defaults to no extra grouping.

    Returns:
        One row per ``parent_company`` (× ``group_cols``) with summed
        ``ownership_mw`` and a ``generator_count``, sorted by capacity.
    """
    keys = ["parent_company", *(group_cols or [])]
    summary = (
        parent_df.groupby(keys, dropna=False)
        .agg(
            ownership_mw=("ownership_mw", "sum"),
            generator_count=("ownership_mw", "size"),
        )
        .reset_index()
    )
    return summary.sort_values("ownership_mw", ascending=False).reset_index(drop=True)


def attribute_emissions(
    dispatch_results_path: Path,
    parent_df: pd.DataFrame,
    year: int,
) -> pd.DataFrame:
    """Attribute dispatch emissions to parent companies.

    Joins a plant-level dispatch result (one row per plant-generator-hour,
    carrying ``dispatch_mw`` and an ``emission_rate`` in tCO2/MWh) with the
    parent mapping, scales emissions and generation by ``percent_owned``,
    and rolls up to parent companies at hourly, monthly and annual
    granularity.

    Args:
        dispatch_results_path: Parquet of plant-level dispatch. Required
            columns: ``plant_code``, ``generator_id``, ``hour``,
            ``dispatch_mw`` and an emission-rate column (``emission_rate``
            or ``emission_rate_tco2_mwh``).
        parent_df: Output of :func:`build_parent_mapping`.
        year: Calendar year of the dispatch, used to bucket months.

    Returns:
        Stacked rows with columns ``parent_company``, ``granularity``
        (``"hourly" | "monthly" | "annual"``), ``period``, ``emissions_tco2``,
        ``generation_mwh`` and ``emissions_intensity_tco2_per_mwh``.
    """
    dispatch = pd.read_parquet(dispatch_results_path)
    rate_col = (
        "emission_rate"
        if "emission_rate" in dispatch.columns
        else "emission_rate_tco2_mwh"
    )
    dispatch = dispatch.copy()
    dispatch["plant_code"] = dispatch["plant_code"].astype("int64")
    dispatch["generator_id"] = dispatch["generator_id"].astype("string").str.strip()

    owners = parent_df[
        ["plant_code", "generator_id", "parent_company", "percent_owned"]
    ].copy()
    owners["plant_code"] = owners["plant_code"].astype("int64")
    owners["generator_id"] = owners["generator_id"].astype("string").str.strip()

    merged = dispatch.merge(owners, on=["plant_code", "generator_id"], how="left")
    merged["parent_company"] = merged["parent_company"].fillna(UNKNOWN_PARENT)
    merged["percent_owned"] = merged["percent_owned"].fillna(1.0)

    merged["owned_generation_mwh"] = merged["dispatch_mw"] * merged["percent_owned"]
    merged["owned_emissions_tco2"] = merged["owned_generation_mwh"] * merged[rate_col]
    # Hour-of-year → calendar month (Jan = month 1), via the year's calendar.
    hour_index = pd.to_datetime(f"{year}-01-01") + pd.to_timedelta(
        merged["hour"], unit="h"
    )
    merged["month"] = hour_index.dt.month

    frames: list[pd.DataFrame] = []
    for granularity, period_col in (
        ("hourly", "hour"),
        ("monthly", "month"),
        ("annual", None),
    ):
        keys = ["parent_company"] + ([period_col] if period_col else [])
        agg = (
            merged.groupby(keys, dropna=False)
            .agg(
                emissions_tco2=("owned_emissions_tco2", "sum"),
                generation_mwh=("owned_generation_mwh", "sum"),
            )
            .reset_index()
        )
        agg["granularity"] = granularity
        agg["period"] = agg[period_col] if period_col else year
        if period_col:
            agg = agg.drop(columns=period_col)
        frames.append(agg)

    out = pd.concat(frames, ignore_index=True)
    out["emissions_intensity_tco2_per_mwh"] = out["emissions_tco2"] / out[
        "generation_mwh"
    ].where(out["generation_mwh"] > 0.0)
    return out[
        [
            "parent_company",
            "granularity",
            "period",
            "emissions_tco2",
            "generation_mwh",
            "emissions_intensity_tco2_per_mwh",
        ]
    ]
