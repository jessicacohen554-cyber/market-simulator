"""Curate the canonical ``emissions`` clean datatype from EPA CAMPD (CEMS).

Reconciles the two EPA Clean Air Markets Program Data hourly layouts under
``data/raw`` into the single schema at
``data/dictionary/schema/emissions.schema.yaml``:

* ``campd-unit-level/{STATE}_{YEAR}.parquet`` — one row per ``(facility,
  unit, hour)`` with a real ``unitId``.
* ``campd-facility-level/{STATE}_{YEAR}.parquet`` — one row per ``(facility,
  hour)``; these rows carry ``unit_id = "ALL"`` so the key stays non-null.

Standardization applied (units confirmed against ``src/market_sim/data/campd.py``,
which is the repo's authoritative CAMPD spec — the constants are reused here so
there is one source of truth):

* ``facilityId`` -> ``plant_id`` (int64), ``unitId`` -> ``unit_id`` (string).
* ``date`` + ``hour`` -> ``interval_start_utc``. CAMPD reports the hour in
  **Local Standard Time** (no daylight saving) for the facility's state, so a
  fixed per-state standard offset converts it to UTC; the naive wall-clock LST
  is carried alongside as ``interval_start_local``.
* ``grossLoad`` (MW) -> ``gross_mw``; ``heatInput`` (MMBtu) ->
  ``heat_input_mmbtu`` (no conversion).
* ``co2Mass`` (**short tons**) -> ``co2_kg``; ``so2Mass`` / ``noxMass``
  (**pounds**) -> ``so2_kg`` / ``nox_kg``.
* ``iso`` is left null here — plants are mapped to an ISO later via the
  reference crosswalk.

CAMPD carries source columns the emissions schema deliberately does not (e.g.
``steamLoad`` = CHP host process steam in 1000 lb/hr, ``opTime``,
``primaryFuelInfo``, ``unitType``, ``stateCode``, ``facilityName``); these are
identifiers/metadata used only for reconciliation or are out of scope for an
emissions fact table, so they are dropped rather than carried.

Where a state appears in both grains, the more granular unit-level rows win:
any plant present in the unit-level extracts is taken from there, and the
facility-level "ALL" rows are kept only for plants with no unit-level
coverage. This represents every plant exactly once and never double-counts a
facility against its own units.

Output is partitioned by year (``iso`` is null, so no ISO/market partition):
``data/clean/emissions/emissions_{year}.parquet``. Every file is streamed
through ``scripts.lib.clean_io.write_clean_iter`` (row groups laid out
identically to a single-shot ``write_clean`` — its documented data-byte
identity) and round-trip checked with ``validate_clean``. Assembly is
Arrow-side and per-file: a year is never materialized as one pandas frame.
The previous whole-year ``pd.concat``/``drop_duplicates``/``sort_values``
pipeline peaked ~10 GiB RSS on 119 MiB of input and OOM-killed standard
7.8 GiB CI runners (``docs/bloat-removal-report-2026-08.md`` §4); the
streaming assembly produces row/order/dtype-identical output within a
standard runner's budget. The script reads only ``data/raw`` and is
idempotent — re-running regenerates each year's file in place.

Usage:
    python scripts/data/curate_emissions.py                 # all detected years
    python scripts/data/curate_emissions.py --years 2023 2024
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc

from market_sim.config import paths
from market_sim.data.campd import LB_TO_KG, SHORT_TON_TO_KG

# Repo root on sys.path so ``scripts.lib`` resolves when run as a script
# (the bare ``python scripts/data/curate_emissions.py`` puts only ``scripts/`` on
# the path). market_sim itself is installed, so it needs no such help.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import clean_io  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("curate_emissions")

# Raw CAMPD input directories (read-only).
RAW_UNIT_DIR: Path = paths.RAW_DATA_DIR / "campd-unit-level"
RAW_FACILITY_DIR: Path = paths.RAW_DATA_DIR / "campd-facility-level"

# Canonical schema column order (mirrors emissions.schema.yaml).
_SCHEMA_COLUMNS: tuple[str, ...] = (
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "plant_id",
    "unit_id",
    "gross_mw",
    "heat_input_mmbtu",
    "co2_kg",
    "nox_kg",
    "so2_kg",
)
_KEY_COLUMNS: list[str] = ["plant_id", "unit_id", "interval_start_utc"]

# Hours to ADD to a state's Local Standard Time to reach UTC. CAMPD timestamps
# are local *standard* time year-round (no DST), so a fixed integer offset is
# exact. The map uses each state's predominant standard zone (a few states span
# two zones — e.g. TX/KS/ND/SD western edges, OR — but CAMPD is reconciled at
# the state grain per the curation contract); Eastern=5, Central=6, Mountain=7,
# Pacific=8, Alaska=9, Hawaii=10 (Arizona never observes DST anyway).
STATE_STD_UTC_OFFSET_HOURS: dict[str, int] = {
    # Eastern (UTC-5)
    "CT": 5,
    "DC": 5,
    "DE": 5,
    "FL": 5,
    "GA": 5,
    "IN": 5,
    "KY": 5,
    "MA": 5,
    "MD": 5,
    "ME": 5,
    "MI": 5,
    "NC": 5,
    "NH": 5,
    "NJ": 5,
    "NY": 5,
    "OH": 5,
    "PA": 5,
    "RI": 5,
    "SC": 5,
    "VA": 5,
    "VT": 5,
    "WV": 5,
    # Central (UTC-6)
    "AL": 6,
    "AR": 6,
    "IA": 6,
    "IL": 6,
    "KS": 6,
    "LA": 6,
    "MN": 6,
    "MO": 6,
    "MS": 6,
    "ND": 6,
    "NE": 6,
    "OK": 6,
    "SD": 6,
    "TN": 6,
    "TX": 6,
    "WI": 6,
    # Mountain (UTC-7)
    "AZ": 7,
    "CO": 7,
    "ID": 7,
    "MT": 7,
    "NM": 7,
    "UT": 7,
    "WY": 7,
    # Pacific (UTC-8)
    "CA": 8,
    "NV": 8,
    "OR": 8,
    "WA": 8,
    # Alaska / Hawaii
    "AK": 9,
    "HI": 10,
}

_YEAR_RE = re.compile(r"_(\d{4})\.parquet$")


def _std_offset(states: pd.Series) -> pd.Series:
    """Map a Series of state codes to LST->UTC offsets (hours), strictly.

    Raises if any state has no entry in :data:`STATE_STD_UTC_OFFSET_HOURS` —
    we never want to silently mis-time a facility by guessing an offset.
    """
    offset = states.astype("string").str.upper().map(STATE_STD_UTC_OFFSET_HOURS)
    if offset.isna().any():
        bad = sorted(states[offset.isna()].astype("string").str.upper().unique())
        raise ValueError(
            f"no standard-time UTC offset for CAMPD state(s) {bad}; "
            "add them to STATE_STD_UTC_OFFSET_HOURS"
        )
    return offset.astype("int64")


def clean_campd_frame(raw: pd.DataFrame, *, facility_level: bool) -> pd.DataFrame:
    """Standardize one raw CAMPD extract to the emissions schema.

    ``facility_level`` selects the grain: unit-level frames map ``unitId`` to
    ``unit_id``; facility-level frames have no ``unitId`` and get
    ``unit_id = "ALL"``. Returns a frame with exactly the schema columns,
    dtypes and units (masses in kg). Rows whose ``facilityId`` does not parse
    to a number, or whose ``hour`` is missing, are dropped (they cannot key).
    """
    plant_id = pd.to_numeric(raw["facilityId"], errors="coerce")
    hour = pd.to_numeric(raw["hour"], errors="coerce")
    keep = plant_id.notna() & hour.notna()
    if facility_level:
        unit_id = pd.Series("ALL", index=raw.index, dtype="string")
    else:
        unit_id = raw["unitId"].astype("string")
        keep &= unit_id.notna() & (unit_id.str.len() > 0)

    raw = raw[keep]
    plant_id = plant_id[keep].astype("int64")
    hour = hour[keep].astype("int64")
    unit_id = unit_id[keep]

    local_naive = pd.to_datetime(raw["date"]) + pd.to_timedelta(hour, unit="h")
    utc = (
        local_naive + pd.to_timedelta(_std_offset(raw["stateCode"]), unit="h")
    ).dt.tz_localize("UTC")

    out = pd.DataFrame(
        {
            "interval_start_utc": utc.to_numpy(),
            "interval_start_local": local_naive.to_numpy("datetime64[ns]"),
            "iso": pd.array([pd.NA] * len(raw), dtype="string"),
            "plant_id": plant_id.to_numpy(),
            "unit_id": unit_id.to_numpy(),
            "gross_mw": pd.to_numeric(raw["grossLoad"], errors="coerce").astype(
                "float64"
            ),
            "heat_input_mmbtu": pd.to_numeric(raw["heatInput"], errors="coerce").astype(
                "float64"
            ),
            "co2_kg": pd.to_numeric(raw["co2Mass"], errors="coerce").astype("float64")
            * SHORT_TON_TO_KG,
            "nox_kg": pd.to_numeric(raw["noxMass"], errors="coerce").astype("float64")
            * LB_TO_KG,
            "so2_kg": pd.to_numeric(raw["so2Mass"], errors="coerce").astype("float64")
            * LB_TO_KG,
        }
    )
    # Make interval_start_utc tz-aware UTC (numpy round-trip above drops tz).
    out["interval_start_utc"] = pd.to_datetime(out["interval_start_utc"], utc=True)
    out["unit_id"] = out["unit_id"].astype("string")
    out["plant_id"] = out["plant_id"].astype("int64")
    return out[list(_SCHEMA_COLUMNS)]


def _detect_years(unit_dir: Path, fac_dir: Path) -> list[int]:
    """Return the sorted set of years present across both raw grains."""
    years: set[int] = set()
    for d in (unit_dir, fac_dir):
        if d.is_dir():
            for p in d.glob("*.parquet"):
                m = _YEAR_RE.search(p.name)
                if m:
                    years.add(int(m.group(1)))
    return sorted(years)


def _cleaned_arrow_tables(
    unit_paths: list[Path], fac_paths: list[Path]
) -> tuple[list[pa.Table], int, int]:
    """Clean every extract into per-file Arrow tables, one file at a time.

    Returns ``(tables, n_unit, n_fac)``: the cleaned tables in the canonical
    reconciliation order — unit grain first (in sorted path order), then the
    facility "ALL" rows for plants with no unit-level coverage — plus the
    pre-dedupe row count per grain. Each per-state pandas frame is converted
    to Arrow and released before the next file is read, so peak memory holds
    one state's frame plus the (much smaller) Arrow accumulation, never the
    year's frames simultaneously (the pre-2026-08 OOM,
    ``docs/bloat-removal-report-2026-08.md`` §4).
    """
    tables: list[pa.Table] = []
    covered: set[int] = set()
    n_unit = 0
    for p in unit_paths:
        f = clean_campd_frame(pd.read_parquet(p), facility_level=False)
        covered.update(f["plant_id"].unique())
        n_unit += len(f)
        tables.append(pa.Table.from_pandas(f, preserve_index=False))
    n_fac = 0
    for p in fac_paths:
        f = clean_campd_frame(pd.read_parquet(p), facility_level=True)
        f = f[~f["plant_id"].isin(covered)]  # unit-level wins where it exists
        if len(f):
            n_fac += len(f)
            tables.append(pa.Table.from_pandas(f, preserve_index=False))
    return tables, n_unit, n_fac


def _first_occurrence_sorted_indices(table: pa.Table) -> pa.Array:
    """Row indices that key-sort ``table``, keeping first duplicate-key rows.

    Order-equivalent to what this script's pandas pipeline always did —
    ``drop_duplicates(subset=_KEY_COLUMNS, keep="first")`` followed by
    ``sort_values(_KEY_COLUMNS)`` — by construction: the multi-key sort is
    made stable with an explicit original-row-order tiebreaker (rows with
    equal keys stay in first-appearance order, so the first row of each
    equal-key run is exactly the row pandas kept), nulls sort last (pandas
    ``na_position="last"``), and adjacent-key comparison treats null == null
    (pandas ``duplicated`` treats NaT as equal). Only the key columns plus
    one int64 order column are materialized; payload columns are untouched.
    """
    n = table.num_rows
    keys = table.select(_KEY_COLUMNS).append_column(
        "__row", pa.array(np.arange(n, dtype=np.int64))
    )
    idx = pc.sort_indices(
        keys,
        sort_keys=[(c, "ascending") for c in _KEY_COLUMNS] + [("__row", "ascending")],
    )
    if n < 2:
        return idx
    sorted_keys = keys.take(idx)
    dup = None
    for c in _KEY_COLUMNS:
        col = sorted_keys.column(c).combine_chunks()
        cur, prev = col.slice(1), col.slice(0, n - 1)
        col_eq = pc.or_(
            pc.fill_null(pc.equal(cur, prev), False),
            pc.and_(pc.is_null(cur), pc.is_null(prev)),
        )
        dup = col_eq if dup is None else pc.and_(dup, col_eq)
    if not pc.any(dup).as_py():
        return idx
    keep = pc.invert(pa.concat_arrays([pa.array([False]), dup]))
    return pc.filter(idx, keep)


def _row_group_frames(table: pa.Table, row_idx: pa.Array) -> Iterator[pd.DataFrame]:
    """Yield the selected rows as pandas frames of one row group each.

    Chunks are cut to ``clean_io``'s row-group size so ``write_clean_iter``
    flushes exactly the row groups a single-shot ``write_clean`` would have
    laid out (its documented data-byte identity). The Arrow→pandas round trip
    reconstructs the schema dtypes from the tables' pandas metadata, so each
    chunk carries the same dtypes the whole-year frame always had.
    """
    for lo in range(0, len(row_idx), clean_io._ROW_GROUP_ROWS):
        yield table.take(row_idx.slice(lo, clean_io._ROW_GROUP_ROWS)).to_pandas()


def curate_year(
    year: int,
    *,
    unit_dir: Path = RAW_UNIT_DIR,
    fac_dir: Path = RAW_FACILITY_DIR,
) -> Path:
    """Curate one year of CAMPD emissions and write the clean Parquet.

    Reads every ``*_{year}.parquet`` under ``unit_dir`` (unit grain) and
    ``fac_dir`` (facility grain), reconciles them unit-first (facility "ALL"
    rows only for plants with no unit-level coverage), streams the result out
    via :func:`clean_io.write_clean_iter`, and round-trip validates it.
    Returns the written path.

    The assembly is Arrow-side and streaming (see the module docstring): the
    output rows, order, dtypes and parquet layout are identical to the
    original whole-year pandas pipeline, but the year is never held as a
    single pandas frame, bounding peak RSS to a standard CI runner's budget.
    """
    unit_paths = sorted(unit_dir.glob(f"*_{year}.parquet")) if unit_dir.is_dir() else []
    fac_paths = sorted(fac_dir.glob(f"*_{year}.parquet")) if fac_dir.is_dir() else []
    if not unit_paths and not fac_paths:
        raise FileNotFoundError(
            f"no CAMPD extracts for {year} in {unit_dir} or {fac_dir}"
        )

    tables, n_unit, n_fac = _cleaned_arrow_tables(unit_paths, fac_paths)
    table = pa.concat_tables(tables) if tables else None
    tables.clear()

    source = (
        f"data/raw/campd-unit-level/*_{year}.parquet, "
        f"data/raw/campd-facility-level/*_{year}.parquet"
    )
    if table is None or table.num_rows == 0:
        # Zero cleaned rows: preserve the previous pipeline's exact behavior.
        # Unit-level extracts present -> write the typed empty frame (as the
        # old ``pd.concat`` produced); facility-only inputs that clean to
        # nothing -> the untyped empty frame, which write_clean rejects
        # loudly, exactly as before.
        df = (
            table.to_pandas()
            if table is not None
            else pd.DataFrame(columns=list(_SCHEMA_COLUMNS))
        )
        n_out = 0
        path = clean_io.write_clean(df, "emissions", year=year, source=source)
    else:
        row_idx = _first_occurrence_sorted_indices(table)
        n_out = len(row_idx)
        path = clean_io.write_clean_iter(
            _row_group_frames(table, row_idx), "emissions", year=year, source=source
        )
        del row_idx
    # Release the year's Arrow buffers before the round-trip read-back so the
    # validation read is the phase peak, not additive to the assembly.
    del table
    clean_io.validate_clean(path)
    logger.info(
        "emissions %d: %d rows (%d unit-grain, %d facility-ALL) -> %s",
        year,
        n_out,
        n_unit,
        n_fac,
        path,
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Curate CAMPD CEMS into the emissions clean datatype."
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=None,
        help="Years to curate (default: every year detected under data/raw).",
    )
    args = parser.parse_args(argv)

    years = args.years or _detect_years(RAW_UNIT_DIR, RAW_FACILITY_DIR)
    if not years:
        logger.error("no CAMPD extracts found under %s", paths.RAW_DATA_DIR)
        return 1
    for year in years:
        curate_year(year)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
