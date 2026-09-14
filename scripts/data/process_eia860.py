"""Process the raw EIA-860 release into parquet.

Two outputs are produced from the official EIA-860 annual zip:

1. A faithful parquet of every data sheet in every workbook
   (``eia860_<workbook>[_<sheet>].parquet``) -- utilities, plants,
   generators, wind, solar, storage, multifuel, ownership and the
   environmental schedules.
2. ``eia860_generators.parquet`` -- operable generators for the seven
   wholesale markets, joined to their plant's balancing authority and
   reduced to the loader's canonical schema. This is the file consumed by
   :func:`market_sim.data.fleet.load_fleet_from_csv`.

Usage:
    python scripts/data/process_eia860.py --zip PATH [--out-dir DIR]

Defaults:
    --zip      data/raw/eia-860/eia8602024.zip
    --out-dir  data/raw/eia-860
"""

from __future__ import annotations

import argparse
import io
import logging
import re
import zipfile
from pathlib import Path

import pandas as pd

from market_sim.data.fleet import (
    BA_CODE_TO_ISO,
    EIA_860_CSV_COLUMNS,
    EIA_860_DIR,
    ISO_NERC_REGION_ADMISSION,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("process_eia860")


def _admit_footprint(df: pd.DataFrame, plant: pd.DataFrame) -> pd.DataFrame:
    """Keep the generator rows admitted to a modelled region's footprint.

    Two keys, applied in order: the plant's ``Balancing Authority Code`` must
    map to a region in ``BA_CODE_TO_ISO`` (the pre-existing filter, unchanged
    for every 1:1 region), and where ``ISO_NERC_REGION_ADMISSION`` names a
    NERC region for that region the plant's ``NERC Region`` must equal it.
    The second key exists for the NWPP pool (registered 2026-09-14, lane
    NWPP-20): the BA-code field is respondent-entered, and plant 68906 (Pine
    Forest Solar I, Hopkins County TX, NERC TRE, 500.0 MW) files under DOPD —
    a Washington PUD cannot balance a resource inside ERCOT, so the row is a
    source mis-key and leaves the footprint (docs/multi-iso/nwpp-data-audit.md
    §2.8(a)). A registry predicate, never a per-plant exclusion (rule 24).
    ``df`` must already carry ``plant_id`` and ``balancing_authority_code``.
    """
    df = df[df["balancing_authority_code"].isin(BA_CODE_TO_ISO)]
    if not ISO_NERC_REGION_ADMISSION:
        return df
    required = (
        df["balancing_authority_code"]
        .map(BA_CODE_TO_ISO)
        .map(ISO_NERC_REGION_ADMISSION)
    )
    if "NERC Region" not in plant.columns:
        # A plant frame with no NERC column (a unit-test fixture, or a vintage
        # sheet lacking the field) can only be admitted on the BA key. That is
        # exact for every 1:1 region (required is null everywhere); for a
        # region that DECLARES a NERC predicate it would silently admit the
        # mis-keyed rows the predicate exists to drop, so refuse loudly.
        if required.notna().any():
            raise KeyError(
                "plant frame carries no 'NERC Region' column but the footprint "
                f"predicate needs it for {sorted(set(required.dropna()))}"
            )
        return df
    nerc_by_plant = plant.drop_duplicates("Plant Code").set_index("Plant Code")[
        "NERC Region"
    ]
    nerc = df["plant_id"].map(nerc_by_plant).astype("string").str.strip()
    keep = required.isna() | (nerc == required)
    return df[keep.fillna(False).to_numpy(dtype=bool)]


# Filename marker (workbook) → short slug used in the output parquet name.
_WORKBOOK_SLUGS: dict[str, str] = {
    "Utility_Y": "utility",
    "Plant_Y": "plant",
    "Generator_Y": "generator",
    "Wind_Y": "wind",
    "Solar_Y": "solar",
    "Energy_Storage_Y": "energy_storage",
    "Multifuel_Y": "multifuel",
    "Owner_Y": "owner",
    "EnviroAssoc_Y": "enviro_assoc",
    "EnviroEquip_Y": "enviro_equip",
}

# EIA-860 generator-sheet column → canonical loader column.
_GENERATOR_COLUMN_MAP: dict[str, str] = {
    "Plant Code": "plant_id",
    "Generator ID": "generator_id",
    "Plant Name": "plant_name",
    "State": "state",
    "Technology": "technology",
    "Energy Source 1": "energy_source",
    "Prime Mover": "prime_mover",
    "Nameplate Capacity (MW)": "nameplate_capacity_mw",
    "Summer Capacity (MW)": "net_summer_capacity_mw",
    "Operating Year": "operating_year",
    "Planned Retirement Year": "planned_retirement_year",
    "Planned Retirement Month": "planned_retirement_month",
    "Status": "status",
}

# First backcast year the within-window retiree snapshot supports: a unit that
# retired in or after this calendar year operated for part of the backcast
# window and so belongs in the historical fleet snapshot (the COD ramp times it
# out by its retirement month). Units retired before it are gone for the whole
# window and are deliberately omitted. Bump only if the supported window moves.
#
# 2023 -> 2019 (session xiso-fuelvintage-1, executing
# docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md §3). The
# supported window moved by OWNER AMENDMENT, not by any residual: rule 22
# ``[R-HOLDOUT]`` as amended 2026-08-06 makes the program's working span
# 2019-2025 for every ISO, so 2019 is the program floor and therefore the
# value. Rule 23 ``[R-FROZEN-DERIVE]``: the basis is SOURCE COVERAGE. The
# cutoff must never be chosen, or later adjusted, to improve any year's fit —
# a future session proposing a different value must cite a span change, never
# a score.
RETIREMENT_WINDOW_START: int = 2019

# Physical window for an eGRID heat rate, Btu/kWh: below it a plant with
# near-zero net generation reports a negative or absurd ``PLHTRT``, above it
# the same. The plant-grain join (:func:`_join_egrid_heat_rate`) and the
# prime-mover-family derive (``scripts/data/derive_egrid_family_heat_rates``)
# share this ONE window so a family rate is admitted on exactly the plant
# rate's terms.
EGRID_HR_WINDOW_BTU_KWH: tuple[int, int] = (3_000, 30_000)

# Output parquet of within-window retirees (mid-window plant exits the latest
# operable EIA-860 vintage no longer carries). Same canonical schema as the
# operable fleet plus the month-precise ``operating_month`` /
# ``planned_retirement_month`` the COD ramp reads — its actual retirement
# month/year is written into the ``planned_retirement_*`` columns so the single
# COD mechanism (data.cod_ramp) ages it out exactly as it does a planned exit.
RETIRED_WITHIN_WINDOW_PARQUET = "eia860_generator_retired_within_window.parquet"


def _slug(text: str) -> str:
    """Return a lower-case underscore slug for a sheet or workbook name."""
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", text.lower())).strip("_")


def _stringify(value: object) -> object:
    """Coerce an object-column cell to a clean string (or ``None``)."""
    if value is None:
        return None
    if isinstance(value, float):
        if value != value:  # NaN
            return None
        return str(int(value)) if value.is_integer() else str(value)
    return str(value).strip()


def _clean_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Drop blank rows and make object columns parquet-safe."""
    df = df.dropna(how="all").reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(_stringify)
    return df


# Column names that mark the real header row of an EIA-860 data sheet.
_HEADER_ANCHORS: frozenset[str] = frozenset({"Utility ID", "Plant Code"})


def _read_sheet(data: bytes, sheet: str) -> pd.DataFrame:
    """Read one EIA-860 sheet, locating the header row by its anchor columns.

    The final annual release carries a one-line title above the header; the
    Early Release adds a disclaimer paragraph as a second preamble row, so the
    header row is found by scanning for the first row containing a known
    anchor column ("Utility ID" / "Plant Code") rather than hardcoding it.
    """
    probe = pd.read_excel(io.BytesIO(data), sheet_name=sheet, header=None, nrows=6)
    header_row = 1  # final-release default: one title line
    for i in range(len(probe)):
        cells = {str(c).strip() for c in probe.iloc[i].tolist()}
        if cells & _HEADER_ANCHORS:
            header_row = i
            break
    return pd.read_excel(io.BytesIO(data), sheet_name=sheet, header=header_row)


def extract_all_workbooks(zip_path: Path, out_dir: Path) -> int:
    """Write every data sheet of every EIA-860 workbook to a parquet.

    Returns the number of parquet files written.
    """
    written = 0
    with zipfile.ZipFile(zip_path) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".xlsx"):
                continue
            slug = next(
                (s for marker, s in _WORKBOOK_SLUGS.items() if marker in name),
                None,
            )
            if slug is None:  # blank form, layout key, etc.
                continue
            data = zf.read(name)
            sheets = pd.ExcelFile(io.BytesIO(data)).sheet_names
            for sheet in sheets:
                df = _clean_sheet(_read_sheet(data, sheet))
                stem = slug if len(sheets) == 1 else f"{slug}_{_slug(sheet)}"
                path = out_dir / f"eia860_{stem}.parquet"
                df.to_parquet(path, index=False)
                logger.info(
                    "  %-46s %6d rows x %2d cols", path.name, len(df), df.shape[1]
                )
                written += 1
    return written


def build_generator_table(zip_path: Path) -> pd.DataFrame:
    """Return the canonical-schema generator table for the seven markets."""
    with zipfile.ZipFile(zip_path) as zf:
        plant_name = next(n for n in zf.namelist() if "Plant_Y" in n)
        gen_name = next(n for n in zf.namelist() if "Generator_Y" in n)
        plant = _read_sheet(zf.read(plant_name), "Plant")
        generator = _read_sheet(zf.read(gen_name), "Operable")

    # Drop trailing footer/blank rows (Plant Code is non-numeric there).
    plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()]
    generator = generator[
        pd.to_numeric(generator["Plant Code"], errors="coerce").notna()
    ]

    ba_by_plant = plant.drop_duplicates("Plant Code").set_index("Plant Code")[
        "Balancing Authority Code"
    ]

    df = generator[list(_GENERATOR_COLUMN_MAP)].rename(columns=_GENERATOR_COLUMN_MAP)
    df["balancing_authority_code"] = (
        df["plant_id"].map(ba_by_plant).astype("string").str.strip()
    )
    df = _admit_footprint(df, plant)

    df["plant_id"] = df["plant_id"].astype("int64")
    df["generator_id"] = df["generator_id"].map(_stringify)
    for col in (
        "operating_year",
        "planned_retirement_year",
        "planned_retirement_month",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("nameplate_capacity_mw", "net_summer_capacity_mw"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["status"] = df["status"].astype("string").str.strip()

    _join_egrid_heat_rate(df)

    return df[EIA_860_CSV_COLUMNS].reset_index(drop=True)


def rescope_generator_table_from_parquet(
    vintage_dir: Path,
) -> tuple[int, int, list[str]]:
    """Re-derive ``eia860_generators.parquet`` from a vintage's OWN committed sheets.

    **Why this exists (rule 23 ``[R-FROZEN-DERIVE]``).** :func:`build_generator_table`
    filters generators to ``BA_CODE_TO_ISO`` — the set of balancing authorities the
    program models — and writes the result. That filter is applied AT DERIVATION TIME,
    so a vintage derived before an ISO joined the program permanently lacks that ISO's
    generators. Measured 2026-09-13: ``SWPP`` (SPP, registered by lane SPP-20 on
    2026-09-06) is absent from ``vintage_2018/2019/2021/2022`` — 0 rows each, 6 distinct
    BAs — while ``vintage_2020/2023/2024`` and the canonical snapshot carry 1,527 /
    1,576 / 1,626 / 1,646 SWPP rows at 7 BAs. This blocked SPP's entire held-out ladder:
    a 2019 solve dies in the fleet load with a ``FileNotFoundError`` whose message names
    a file that exists.

    **This re-derivation cites a SCOPE change, never a residual** — the admissible
    trigger rule 23 requires. The underlying EIA release is untouched; what changed is
    which BAs the program models.

    **No re-fetch is needed and none is performed.** The raw annual zips are not
    committed per vintage, but both inputs :func:`build_generator_table` uses are:
    ``eia860_generator_operable.parquet`` (its ``Generator_Y`` "Operable" sheet) and
    ``eia860_plant.parquet`` (its ``Plant_Y`` sheet, which carries the BA code joined
    onto each generator). This reproduces that construction from them.

    **STRICTLY ADDITIVE, AND ENFORCED RATHER THAN ASSERTED.** Every ``(plant_id,
    generator_id)`` key already committed must survive: the rebuild is refused with
    ``RuntimeError`` if any existing key would be dropped, so a vintage that six other
    ISOs' committed bundles read cannot lose a row. Verified on ``vintage_2019`` before
    this function was written: the six-BA rebuild reproduces the committed 14,043 keys
    exactly — 0 committed-only, 0 rebuilt-only — and adds 1,512 SWPP rows.

    Args:
        vintage_dir: An ``eia-860`` vintage directory (or the canonical snapshot).

    Returns:
        ``(rows_before, rows_after, added_bas)``.

    Raises:
        FileNotFoundError: A required committed sheet is absent.
        RuntimeError: The rebuild would drop an already-committed generator key.
    """
    out = vintage_dir / "eia860_generators.parquet"
    gen_path = vintage_dir / "eia860_generator_operable.parquet"
    plant_path = vintage_dir / "eia860_plant.parquet"
    for path in (out, gen_path, plant_path):
        if not path.exists():
            raise FileNotFoundError(f"{vintage_dir.name}: missing {path.name}")

    committed = pd.read_parquet(out)
    plant = pd.read_parquet(plant_path)
    generator = pd.read_parquet(gen_path)
    plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()]
    generator = generator[
        pd.to_numeric(generator["Plant Code"], errors="coerce").notna()
    ]

    ba_by_plant = plant.drop_duplicates("Plant Code").set_index("Plant Code")[
        "Balancing Authority Code"
    ]
    df = generator[list(_GENERATOR_COLUMN_MAP)].rename(columns=_GENERATOR_COLUMN_MAP)
    df["balancing_authority_code"] = (
        df["plant_id"].map(ba_by_plant).astype("string").str.strip()
    )
    df = _admit_footprint(df, plant)

    df["plant_id"] = df["plant_id"].astype("int64")
    df["generator_id"] = df["generator_id"].map(_stringify)
    for col in (
        "operating_year",
        "planned_retirement_year",
        "planned_retirement_month",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("nameplate_capacity_mw", "net_summer_capacity_mw"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["status"] = df["status"].astype("string").str.strip()

    def _keys(frame: pd.DataFrame) -> set[tuple[int, str]]:
        return set(
            zip(frame["plant_id"].astype("int64"), frame["generator_id"].astype(str))
        )

    lost = _keys(committed) - _keys(df)
    if lost:
        raise RuntimeError(
            f"{vintage_dir.name}: rebuild would DROP {len(lost)} committed generator "
            f"key(s) (e.g. {sorted(lost)[:5]}). Refusing — this re-derivation is "
            "strictly additive by contract."
        )

    before = set(committed["balancing_authority_code"].dropna().astype(str))
    added = sorted(set(df["balancing_authority_code"].dropna().astype(str)) - before)

    # STRICTLY ADDITIVE ON THE COMMITTED BYTES (tightened 2026-09-14, lane
    # NWPP-20). The first form of this function wrote the whole rebuilt frame,
    # which (a) dropped the ``heat_rate`` column the canonical build joins
    # (:func:`_join_egrid_heat_rate`) and re-ordered the columns — so every
    # region's thermal units would silently fall back to bin-centre heat
    # rates — and (b) admitted any generator the current sheets carry that
    # the committed build did not (measured: PJM plant 60781 unit PV1, 0.9 MW),
    # moving an already-registered region's fleet. Neither is a scope change.
    # So: every committed row survives byte-for-byte, in place, with its
    # columns; ONLY rows of the newly registered balancing authorities are
    # appended, heat-rate-joined the way the canonical build joins them when
    # the committed file carries that column.
    new_rows = df[df["balancing_authority_code"].astype(str).isin(added)].copy()
    if "heat_rate" in committed.columns:
        _join_egrid_heat_rate(new_rows)
    new_rows = new_rows.reindex(columns=committed.columns)
    # Write through pyarrow against the COMMITTED file's own schema, so the
    # appended rows take the committed column types field by field (a vintage
    # whose committed ``heat_rate`` is an all-null column stays an all-null
    # column — pandas alone would promote it to float64 and re-encode every
    # committed cell) and the committed rows are re-emitted from the table
    # that was read, untouched.
    import pyarrow as pa
    import pyarrow.parquet as pq

    committed_table = pq.read_table(out)
    schema = committed_table.schema
    new_table = pa.Table.from_pandas(new_rows, preserve_index=False)
    columns = []
    for field in schema:
        column = new_table.column(field.name)
        if pa.types.is_null(field.type):
            column = pa.nulls(new_table.num_rows, type=field.type)
        elif not column.type.equals(field.type):
            column = column.cast(field.type)
        columns.append(column)
    new_table = pa.Table.from_arrays(columns, schema=schema)
    merged = pa.concat_tables([committed_table, new_table])
    pq.write_table(merged, out)
    return len(committed), merged.num_rows, added


def _join_egrid_heat_rate(df: pd.DataFrame) -> None:
    """Add a plant-level ``heat_rate`` column (MMBtu/MWh) from eGRID PLNT23.

    The EIA-860 Generator_Y sheets carry no heat-rate column, so eGRID PLHTRT
    -- derived from CEMS fuel consumption -- is the source. It is plant-level,
    so every generator at a plant inherits the same value. Mutates ``df`` in
    place (keyed on its ``plant_id`` column); where the join misses, the fleet
    loader falls back to the vintage bin centers in HEAT_RATE_BINS.
    """
    from market_sim.config.paths import FLEET_DIR

    egrid_path = FLEET_DIR / "egrid2023_data_rev2.xlsx"
    if not egrid_path.exists():
        logger.warning(
            "eGRID workbook not found at %s; heat_rate left blank", egrid_path
        )
        df["heat_rate"] = pd.NA
        return
    egrid = pd.read_excel(
        egrid_path, sheet_name="PLNT23", skiprows=1, usecols=["ORISPL", "PLHTRT"]
    )
    hr = pd.to_numeric(egrid["PLHTRT"], errors="coerce")
    # Drop physically implausible plant heat rates -- negative or absurdly
    # large values appear for plants with near-zero net generation.
    lo, hi = EGRID_HR_WINDOW_BTU_KWH
    egrid["PLHTRT"] = hr.where((hr >= lo) & (hr <= hi))
    egrid_hr = (
        egrid.dropna(subset=["ORISPL", "PLHTRT"])
        .drop_duplicates("ORISPL")
        .set_index("ORISPL")["PLHTRT"]
    )
    # Convert BTU/kWh -> MMBtu/MWh (divide by 1000).
    df["heat_rate"] = df["plant_id"].map(egrid_hr) / 1000.0
    matched = int(df["heat_rate"].notna().sum())
    logger.info(
        "  joined eGRID heat rates: %d of %d generators matched", matched, len(df)
    )


# Within-window retiree schema: the canonical fleet columns (which now carry
# ``planned_retirement_month``) plus ``operating_month`` — the two month-precise
# fields the COD ramp reads (the loader only requires them when present).
_RETIRED_COLUMNS: list[str] = EIA_860_CSV_COLUMNS + ["operating_month"]


# Sheet parquets a `vintage_<year>/` directory carries, for the parquet-source
# arm of :func:`_read_retired_sheets`. The pre-2023 EIA-860 release zips are
# not committed (data/raw/eia-860 holds their EXTRACTED parquet vintages
# instead), so a source may be either a release zip or such a directory.
_RETIRED_SHEET_PARQUET = "eia860_generator_retired_and_canceled.parquet"
_PLANT_SHEET_PARQUET = "eia860_plant.parquet"


def _read_retired_sheets(source: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(retired_and_canceled, plant)`` sheets for one EIA-860 source.

    ``source`` is either an official annual release **zip** (the sheets are
    read out of it directly) or an extracted **vintage directory** under
    ``data/raw/eia-860`` carrying :data:`_RETIRED_SHEET_PARQUET` and
    :data:`_PLANT_SHEET_PARQUET`. The two arms return the same two frames
    with the same EIA column names, so every caller downstream is
    source-agnostic.
    """
    if source.is_dir():
        return (
            pd.read_parquet(source / _RETIRED_SHEET_PARQUET),
            pd.read_parquet(source / _PLANT_SHEET_PARQUET),
        )
    with zipfile.ZipFile(source) as zf:
        plant_name = next(n for n in zf.namelist() if "Plant_Y" in n)
        gen_name = next(n for n in zf.namelist() if "Generator_Y" in n)
        return (
            _read_sheet(zf.read(gen_name), "Retired and Canceled"),
            _read_sheet(zf.read(plant_name), "Plant"),
        )


def _project_retired_sheet(
    retired: pd.DataFrame,
    plant: pd.DataFrame,
    cutoff_year: int,
    until_year: int | None = None,
) -> pd.DataFrame:
    """Project one vintage's retired sheet onto the canonical fleet columns.

    Maps the shared EIA-860 generator columns, carries the sheet's **actual**
    ``Retirement Year/Month`` into the ``planned_retirement_*`` fields the COD
    ramp reads, attaches the plant's balancing authority, and keeps only
    modelled-ISO units that retired in or after ``cutoff_year`` (and, when
    ``until_year`` is given, strictly before it).
    """
    retired = retired[pd.to_numeric(retired["Plant Code"], errors="coerce").notna()]
    plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()]
    ba_by_plant = plant.drop_duplicates("Plant Code").set_index("Plant Code")[
        "Balancing Authority Code"
    ]

    # The retired sheet carries ACTUAL "Retirement Year/Month" rather than
    # the operable sheet's "Planned Retirement Year" -- map every shared
    # column, then fill the planned_retirement_* fields from the actuals.
    shared = {
        k: v
        for k, v in _GENERATOR_COLUMN_MAP.items()
        if k in retired.columns and k != "Planned Retirement Year"
    }
    df = retired[list(shared)].rename(columns=shared)
    # Carry the real retirement into the planned_retirement_* columns the
    # COD ramp reads.
    df["operating_month"] = pd.to_numeric(retired["Operating Month"], errors="coerce")
    df["planned_retirement_year"] = pd.to_numeric(
        retired["Retirement Year"], errors="coerce"
    )
    df["planned_retirement_month"] = pd.to_numeric(
        retired["Retirement Month"], errors="coerce"
    )
    df["balancing_authority_code"] = (
        df["plant_id"].map(ba_by_plant).astype("string").str.strip()
    )
    df = _admit_footprint(df, plant)
    # Within-window exits only.
    df = df[df["planned_retirement_year"] >= cutoff_year]
    if until_year is not None:
        df = df[df["planned_retirement_year"] < until_year]
    return df


def build_within_window_retirees(
    zip_paths: list[Path],
    operable_parquet: Path,
    cutoff_year: int = RETIREMENT_WINDOW_START,
    until_year: int | None = None,
    preserve: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return mid-window plant exits missing from the latest operable vintage.

    The committed operable EIA-860 vintage is a single recent snapshot, so a
    plant that retired *during* the backcast window (e.g. Mystic, plant 1588,
    a ~1.4 GW CC that ran through 2023 and retired mid-2024) is absent from
    every modeled year -- the COD ramp can only age out a unit that is in the
    snapshot. This reads the "Retired and Canceled" sheet of each *final*
    EIA-860 vintage in ``zip_paths``, keeps units that retired in or after
    ``cutoff_year`` (the window start), and returns them in the canonical fleet
    schema with their **actual** retirement month/year written into the
    ``planned_retirement_*`` columns and ``status`` forced to ``OP`` -- so the
    fleet loader keeps them and the single COD mechanism (:mod:`cod_ramp`) times
    each out by its real retirement month, exactly as it does a planned exit.

    Only *whole-plant* exits are emitted: any plant still present in
    ``operable_parquet`` is dropped (a partially-retired plant keeps its
    surviving units in the operable snapshot, and the plant-keyed COD map would
    hold the whole plant online -- so its retired units stay out to avoid an
    un-maskable over-count). Units are de-duplicated across vintages by
    ``(plant_id, generator_id)``, keeping the latest vintage's record.

    ``preserve`` is an ALREADY-BUILT artifact whose rows are carried through
    unchanged, and which no newly-read row may displace: a key present in
    ``preserve`` keeps the preserved record verbatim, and only genuinely new
    keys are appended. It exists because **EIA prunes older retirements from
    each new release** (``data/raw/eia-860/README.md``, FFR-7A): the release
    vintages that supplied the shipped 2023/2024 rows are no longer on disk,
    so a bare rebuild from the currently-available sources would silently
    DROP 161 real retired units rather than add any. Preserving is therefore
    the rule-14 ``[R-ACCURATE]`` reading — keep the measured rows that exist —
    and it is what makes a window extension provably ADDITIVE.

    ``until_year`` bounds the newly-read rows from ABOVE (exclusive), so a
    widening touches only the years it is widening INTO. Widening 2023 -> 2019
    passes ``until_year=2023``: without it the currently-committed (newer)
    release sheet also contributes 107 units / 497.7 MW of 2023-2025
    retirements the original build's vintages did not carry, which would
    change every ISO's 2023-2025 TRAINING fleet and re-key every committed
    keeper bundle. Those rows are a real, separate gap — see
    ``docs/FINDING-xiso-fuelvintage-retiree-window-2026-09-09.md`` §2 — and
    belong to a change scoped to the training window, not to this one.
    """
    operable_plant_ids: set[int] = set()
    if operable_parquet.exists():
        op = pd.read_parquet(operable_parquet, columns=["Plant Code"])
        operable_plant_ids = set(
            pd.to_numeric(op["Plant Code"], errors="coerce")
            .dropna()
            .astype(int)
            .tolist()
        )

    frames: list[pd.DataFrame] = [
        _project_retired_sheet(*_read_retired_sheets(src), cutoff_year, until_year)
        for src in zip_paths
    ]

    if not frames:
        return pd.DataFrame(columns=_RETIRED_COLUMNS)

    df = pd.concat(frames, ignore_index=True)
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce").astype("int64")
    df["generator_id"] = df["generator_id"].map(_stringify)
    for col in ("operating_year", "planned_retirement_year"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("operating_month", "planned_retirement_month"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("nameplate_capacity_mw", "net_summer_capacity_mw"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Whole-plant exits only: drop any plant still carried by the operable
    # snapshot (its surviving units are already dispatched there).
    df = df[~df["plant_id"].isin(operable_plant_ids)]
    # Keep the latest vintage's record per unit (frames are vintage-ordered).
    df = df.drop_duplicates(subset=["plant_id", "generator_id"], keep="last")

    # The within-window retiree operated during the window; mark it OP so the
    # fleet loader keeps it -- the COD ramp owns the actual exit timing.
    df["status"] = "OP"
    _join_egrid_heat_rate(df)
    df = df[_RETIRED_COLUMNS].reset_index(drop=True)

    if preserve is None or preserve.empty:
        return df
    # Additive by construction: the preserved rows come first and win every
    # shared key, so the result is `preserve` verbatim plus the keys it does
    # not already carry (see the ``preserve`` note above).
    kept = set(map(tuple, preserve[["plant_id", "generator_id"]].to_numpy()))
    fresh = df[
        [(pid, gid) not in kept for pid, gid in zip(df["plant_id"], df["generator_id"])]
    ]
    return pd.concat([preserve[_RETIRED_COLUMNS], fresh], ignore_index=True)


def main() -> None:
    """Extract the full EIA-860 release and build the fleet loader parquet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zip",
        type=Path,
        default=EIA_860_DIR / "eia8602024.zip",
        help="Path to the raw EIA-860 annual zip.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=EIA_860_DIR,
        help="Directory for the parquet outputs.",
    )
    parser.add_argument(
        "--rescope-from-parquet",
        type=Path,
        nargs="+",
        default=None,
        metavar="VINTAGE_DIR",
        help="Re-derive eia860_generators.parquet in each named vintage directory "
        "from that vintage's OWN committed Generator_Y/Plant_Y parquets, so a "
        "balancing authority registered in BA_CODE_TO_ISO after the vintage was "
        "first derived is no longer missing from it. Rule 23 [R-FROZEN-DERIVE]: the "
        "trigger is a SCOPE change (a new ISO joined the program), never a residual. "
        "No re-fetch. STRICTLY ADDITIVE -- refuses to drop any committed generator "
        "key. Runs this mode alone and exits.",
    )
    parser.add_argument(
        "--retired-window-from",
        type=Path,
        nargs="+",
        default=None,
        metavar="SOURCE",
        help="One or more EIA-860 sources whose 'Retired and Canceled' "
        "sheets supply within-window plant exits (e.g. Mystic) the latest "
        "operable vintage no longer carries. A source is either a FINAL "
        "annual release zip or an extracted vintage_<year>/ directory under "
        "data/raw/eia-860. Give them OLDEST FIRST: later sources win the "
        f"per-unit de-duplication. Writes {RETIRED_WITHIN_WINDOW_PARQUET}.",
    )
    parser.add_argument(
        "--retired-only",
        action="store_true",
        help="Only (re)build the within-window retiree parquet from "
        "--retired-window-from; leave the operable parquets untouched.",
    )
    parser.add_argument(
        "--retired-cutoff-year",
        type=int,
        default=RETIREMENT_WINDOW_START,
        help="First retirement year the snapshot supports (default "
        f"{RETIREMENT_WINDOW_START}). Rule 23 [R-FROZEN-DERIVE]: this tracks "
        "the program's supported backcast span, NEVER a residual.",
    )
    parser.add_argument(
        "--retired-until-year",
        type=int,
        default=None,
        help="Exclusive UPPER bound on the retirement year of newly-read "
        "rows. Pass the PREVIOUS cutoff when widening the window, so the "
        "change touches only the years it widens into and leaves the "
        "already-covered years (and every committed bundle keyed on them) "
        "untouched.",
    )
    parser.add_argument(
        "--retired-extend",
        action="store_true",
        help="Union the newly-read rows ONTO the committed "
        f"{RETIRED_WITHIN_WINDOW_PARQUET} instead of replacing it: every "
        "existing row survives byte-identically and only genuinely new "
        "(plant_id, generator_id) keys are appended. Required when widening "
        "the window, because EIA prunes older retirements from each release "
        "so the vintages that supplied the existing rows are no longer "
        "available to reproduce them.",
    )
    args = parser.parse_args()

    if args.rescope_from_parquet:
        for vintage_dir in args.rescope_from_parquet:
            before, after, added = rescope_generator_table_from_parquet(vintage_dir)
            note = f" (+{', '.join(added)})" if added else " (no BA added)"
            print(f"{vintage_dir.name}: {before} -> {after} generator rows{note}")
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.retired_only:
        if not args.retired_window_from:
            raise SystemExit("--retired-only requires --retired-window-from")
        _build_retired_window(
            args.retired_window_from,
            args.out_dir,
            cutoff_year=args.retired_cutoff_year,
            until_year=args.retired_until_year,
            extend=args.retired_extend,
        )
        return

    if not args.zip.exists():
        raise SystemExit(f"EIA-860 zip not found: {args.zip}")

    logger.info("Extracting all EIA-860 workbooks…")
    count = extract_all_workbooks(args.zip, args.out_dir)
    logger.info("Wrote %d raw parquet sheets", count)

    fleet = build_generator_table(args.zip)
    fleet_path = args.out_dir / "eia860_generators.parquet"
    fleet.to_parquet(fleet_path, index=False)

    if args.retired_window_from:
        _build_retired_window(
            args.retired_window_from,
            args.out_dir,
            cutoff_year=args.retired_cutoff_year,
            until_year=args.retired_until_year,
            extend=args.retired_extend,
        )

    by_iso = (
        fleet.assign(iso=fleet["balancing_authority_code"].map(BA_CODE_TO_ISO))
        .groupby("iso")
        .agg(
            generators=("generator_id", "size"),
            nameplate_gw=("nameplate_capacity_mw", lambda s: round(s.sum() / 1e3, 1)),
        )
    )
    logger.info("Wrote %d market generators to %s", len(fleet), fleet_path.name)
    for iso, row in by_iso.iterrows():
        logger.info(
            "  %-6s %5d generators  %7.1f GW nameplate",
            iso,
            int(row["generators"]),
            row["nameplate_gw"],
        )


def _build_retired_window(
    zip_paths: list[Path],
    out_dir: Path,
    cutoff_year: int = RETIREMENT_WINDOW_START,
    until_year: int | None = None,
    extend: bool = False,
) -> None:
    """Build and write the within-window retiree parquet, logging a summary.

    With ``extend`` set the committed artifact is loaded first and passed as
    ``preserve``, so the write is provably additive (see
    :func:`build_within_window_retirees`).
    """
    for zp in zip_paths:
        if not zp.exists():
            raise SystemExit(f"EIA-860 source not found: {zp}")
    operable_parquet = out_dir / "eia860_generator_operable.parquet"
    out_path = out_dir / RETIRED_WITHIN_WINDOW_PARQUET
    preserve = None
    if extend and out_path.exists():
        preserve = pd.read_parquet(out_path)
    retired = build_within_window_retirees(
        zip_paths,
        operable_parquet,
        cutoff_year=cutoff_year,
        until_year=until_year,
        preserve=preserve,
    )
    retired.to_parquet(out_path, index=False)
    logger.info(
        "Wrote %d within-window retiree units (%.1f GW, %d plants) to %s",
        len(retired),
        retired["nameplate_capacity_mw"].sum() / 1e3,
        retired["plant_id"].nunique(),
        out_path.name,
    )
    by_iso = (
        retired.assign(iso=retired["balancing_authority_code"].map(BA_CODE_TO_ISO))
        .groupby("iso")
        .agg(
            units=("generator_id", "size"),
            plants=("plant_id", "nunique"),
            nameplate_gw=("nameplate_capacity_mw", lambda s: round(s.sum() / 1e3, 2)),
        )
    )
    for iso, row in by_iso.iterrows():
        logger.info(
            "  %-6s %4d units / %3d plants  %6.2f GW",
            iso,
            int(row["units"]),
            int(row["plants"]),
            row["nameplate_gw"],
        )


if __name__ == "__main__":
    main()
