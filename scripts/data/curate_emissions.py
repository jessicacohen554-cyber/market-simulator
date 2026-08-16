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
``data/clean/emissions/emissions_{year}.parquet``. Every file is written
through ``scripts.lib.clean_io.write_clean_iter`` (the streaming writer,
documented data-byte identical in layout to ``write_clean``) and round-trip
checked with ``validate_clean``. The script reads only ``data/raw`` and is
idempotent — re-running regenerates each year's file in place.

A full CEMS year is ~26.5 M rows, and the naive concat-everything assembly
peaks ~10 GiB RSS — past a standard GitHub runner's 7.8 GiB RAM + 3 GiB swap
ceiling (it OOM-killed the golden-data-tier runs; measured record:
``docs/handoffs/perf-recheck-2026-08.md`` §1.2/§1.5). ``curate_year`` is
therefore memory-bounded: column-wise stacking (per-state parts shed each
column as the output gains it), a factorized stable lexsort + neighbor dedupe
in place of whole-frame ``drop_duplicates`` + ``sort_values``, a column-wise
gather, and the streaming writer in place of ``write_clean``'s full second
Arrow copy. Peak RSS for 2023 is ~6.4 GiB, and the output is row-, dtype- and
byte-size-exact against the naive assembly (equivalence protocol + numbers:
``docs/handoffs/golden-tier-fix-2026-08.md``).

Usage:
    python scripts/data/curate_emissions.py                 # all detected years
    python scripts/data/curate_emissions.py --years 2023 2024
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

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

# Streaming-write chunk (rows); bounds the writer-side buffer independently of
# write_clean_iter's own row-group buffering.
_CHUNK_ROWS = 2_000_000

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


def _assemble_column(parts: list[pd.DataFrame], col: str) -> pd.Series:
    """Concat one column across parts, dropping it from each part as consumed."""
    series = pd.concat([p[col] for p in parts], ignore_index=True)
    for p in parts:
        del p[col]
    return series


def curate_year(
    year: int,
    *,
    unit_dir: Path = RAW_UNIT_DIR,
    fac_dir: Path = RAW_FACILITY_DIR,
) -> Path:
    """Curate one year of CAMPD emissions and write the clean Parquet.

    Reads every ``*_{year}.parquet`` under ``unit_dir`` (unit grain) and
    ``fac_dir`` (facility grain), reconciles them unit-first (facility "ALL"
    rows only for plants with no unit-level coverage), writes the result via
    :func:`clean_io.write_clean_iter`, and round-trip validates it. Returns
    the written path.

    The assembly is memory-bounded (see module docstring) but every transform
    is order-equivalent to stacking the parts and applying
    ``drop_duplicates(subset=_KEY_COLUMNS, keep="first")`` then
    ``sort_values(_KEY_COLUMNS)``: the lexsort is stable, so it preserves
    input order within equal keys and keeping the first row of each equal-key
    run selects exactly the rows ``keep="first"`` keeps; the final order
    equals the ``sort_values`` order because keys are unique post-dedupe.
    """
    unit_paths = sorted(unit_dir.glob(f"*_{year}.parquet")) if unit_dir.is_dir() else []
    fac_paths = sorted(fac_dir.glob(f"*_{year}.parquet")) if fac_dir.is_dir() else []
    if not unit_paths and not fac_paths:
        raise FileNotFoundError(
            f"no CAMPD extracts for {year} in {unit_dir} or {fac_dir}"
        )

    # Per-state cleaned parts, unit grain first: the list order fixes the
    # pre-sort row order that the stable dedupe's first-occurrence rule keys
    # off, so unit rows always beat facility "ALL" rows on a shared key.
    parts: list[pd.DataFrame] = []
    covered: set[int] = set()
    n_unit = 0
    for p in unit_paths:
        f = clean_campd_frame(pd.read_parquet(p), facility_level=False)
        covered.update(f["plant_id"].unique().tolist())
        n_unit += len(f)
        parts.append(f)
    n_fac = 0
    for p in fac_paths:
        f = clean_campd_frame(pd.read_parquet(p), facility_level=True)
        f = f[~f["plant_id"].isin(covered)]  # unit-level wins where it exists
        if len(f):
            n_fac += len(f)
            parts.append(f.reset_index(drop=True))

    if parts:
        # Column-wise stack: parts shed each column as the output gains it, so
        # the per-state parts and the stacked year never coexist in full.
        cols = {c: _assemble_column(parts, c) for c in _SCHEMA_COLUMNS}
        parts.clear()
        n_rows = len(cols["plant_id"])

        # Sort keys as flat int64 arrays. unit_id: factorize (hash, appearance
        # order), then re-rank the uniques lexicographically so integer order
        # == string order; interval_start_utc: tz-aware ns since epoch.
        plant = cols["plant_id"].to_numpy()
        codes, uniques = pd.factorize(cols["unit_id"], sort=False)
        rank = np.empty(len(uniques), dtype=np.int64)
        rank[np.argsort(uniques.astype(object), kind="stable")] = np.arange(
            len(uniques)
        )
        unit_key = rank[codes]
        del codes, rank
        ts = cols["interval_start_utc"].to_numpy(dtype="datetime64[ns]").view("i8")

        # Stable lexsort (primary key LAST in np.lexsort's tuple), then keep
        # the first row of each equal-key run == drop_duplicates(keep="first").
        order = np.lexsort((ts, unit_key, plant))
        p_s, u_s, t_s = plant[order], unit_key[order], ts[order]
        keep = np.empty(n_rows, dtype=bool)
        if n_rows:
            keep[0] = True
            keep[1:] = (
                (p_s[1:] != p_s[:-1]) | (u_s[1:] != u_s[:-1]) | (t_s[1:] != t_s[:-1])
            )
        idx = order[keep]
        del order, p_s, u_s, t_s, keep, plant, unit_key, ts

        # Column-wise gather of the kept rows, freeing each source column.
        out = {c: cols.pop(c).take(idx).reset_index(drop=True) for c in _SCHEMA_COLUMNS}
        del idx
        n_out = len(out["plant_id"])
    else:
        # Nothing survived cleaning: hand the writer an empty stream so it
        # raises its standard "no non-empty chunks" SchemaError.
        out = {}
        n_out = 0

    source = (
        f"data/raw/campd-unit-level/*_{year}.parquet, "
        f"data/raw/campd-facility-level/*_{year}.parquet"
    )

    def _chunks():
        for lo in range(0, n_out, _CHUNK_ROWS):
            hi = min(lo + _CHUNK_ROWS, n_out)
            yield pd.DataFrame(
                {c: out[c].iloc[lo:hi].reset_index(drop=True) for c in _SCHEMA_COLUMNS}
            )

    path = clean_io.write_clean_iter(_chunks(), "emissions", year=year, source=source)
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
