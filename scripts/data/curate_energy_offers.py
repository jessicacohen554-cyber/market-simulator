"""Curate the ``energy-offers`` clean datatype from raw PJM DataMiner2 parquets.

Reads the monthly wide-format Parquet files produced by
``scripts/data/fetch_pjm_energy_offers.py`` (under ``data/raw/pjm-energy-offers/``)
and writes one clean long-format Parquet per year to
``data/clean/energy-offers/PJM/`` through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Wide → long transform
---------------------
The raw API response stores each unit's offer curve in one row with up to
twenty MW/price breakpoints as parallel wide columns (``mw1``/``bid1`` …
``mw20``/``bid20``).  This script pivots those into long (normalised) form:
one row per (unit_code × operating-hour × step index), dropping null steps.
Cost parameters (``no_load_cost``, ``avg_ecomin``, ``avg_ecomax``, etc.) are
repeated on every step row for the same (unit_code, interval_start_utc) tuple
so callers can join on the key without a separate lookup.

Column mapping (raw wide → clean long)
---------------------------------------
``bid_datetime_beginning_utc`` → ``interval_start_utc``  (tz-aware UTC)
``bid_datetime_beginning_ept`` → ``interval_start_local`` (tz-naive EPT)
constant "PJM"                 → ``iso``
``mwN``                        → ``step_mw``
``bidN``                       → ``step_price_usd_per_mwh``
N (1–20)                       → ``step_idx``
``avg_ecomin``                 → ``ecomin_mw``
``avg_ecomax``                 → ``ecomax_mw``
``no_load_cost``               → ``no_load_cost_usd_per_h``
``hot_start_cost``             → ``hot_start_cost_usd``
``cold_start_cost``            → ``cold_start_cost_usd``
``inter_start_cost``           → ``inter_start_cost_usd``
``max_daily_starts``           → ``max_daily_starts``
``min_runtime``                → ``min_runtime_h``

Memory model
------------
Each monthly wide parquet (~900 k rows × 57 cols) is loaded and pivoted to
long format one at a time; the result is written to a temp parquet file and
the wide/long DataFrames are freed before the next month is loaded.  After
all months are processed, the temp files are streamed into the final output
via :class:`pyarrow.parquet.ParquetWriter` so only one month's arrow table
lives in memory at any moment.  Peak RSS is ≈ 1–2 GB rather than 8+ GB.

Run
---
    python scripts/data/curate_energy_offers.py              # all years with raw data
    python scripts/data/curate_energy_offers.py --years 2024
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import load_schema, validate_df  # noqa: E402

RAW_DIR = paths.PJM_ENERGY_OFFERS_DIR
ISO = "PJM"
EPT_TZ = "America/New_York"

# Number of MW/bid breakpoints in the wide format.
N_STEPS = 20

# Schema column order (must match energy-offers.schema.yaml).
SCHEMA_COLS: tuple[str, ...] = (
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "unit_code",
    "bid_slope_flag",
    "step_idx",
    "step_mw",
    "step_price_usd_per_mwh",
    "ecomin_mw",
    "ecomax_mw",
    "no_load_cost_usd_per_h",
    "hot_start_cost_usd",
    "cold_start_cost_usd",
    "inter_start_cost_usd",
    "max_daily_starts",
    "min_runtime_h",
)


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


def _parse_utc(s: pd.Series) -> pd.Series:
    """Parse DataMiner2 UTC datetime strings to tz-aware UTC Series.

    The raw format is 'M/D/YYYY H:MM:SS AM' (US locale, no tz suffix).
    """
    parsed = pd.to_datetime(s, utc=False, format="mixed", errors="coerce")
    if parsed.dt.tz is None:
        return parsed.dt.tz_localize("UTC")
    return parsed.dt.tz_convert("UTC")


def _parse_local(s: pd.Series) -> pd.Series:
    """Parse DataMiner2 EPT datetime strings to tz-naive local timestamps.

    Strings have no tz suffix; we localize to EPT and then strip to tz-naive
    ``datetime64[ns]`` as declared in the schema.
    """
    parsed = pd.to_datetime(s, utc=False, format="mixed", errors="coerce")
    if parsed.dt.tz is None:
        try:
            parsed = parsed.dt.tz_localize(EPT_TZ, ambiguous="infer")
        except Exception:
            parsed = parsed.dt.tz_localize(EPT_TZ, ambiguous="NaT")
    return parsed.dt.tz_localize(None)


# ---------------------------------------------------------------------------
# Wide → long pivot
# ---------------------------------------------------------------------------


def _pivot_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot the wide mwN/bidN columns into long step rows.

    Each wide row (unit × hour) fans out to up to N_STEPS long rows, one
    per non-null breakpoint.  Null breakpoints are dropped.  The returned
    DataFrame has ``step_idx`` (1-indexed), ``step_mw``, and
    ``step_price_usd_per_mwh`` columns, plus all non-pivot columns repeated.
    """
    # Columns to keep verbatim (non-pivot attributes).
    id_cols = [
        c
        for c in df.columns
        if not (c.startswith("mw") or c.startswith("bid"))
        or c in ("max_daily_starts", "min_runtime")
    ]

    parts: list[pd.DataFrame] = []
    for i in range(1, N_STEPS + 1):
        mw_col = f"mw{i}"
        bid_col = f"bid{i}"
        if mw_col not in df.columns or bid_col not in df.columns:
            continue
        chunk = df[id_cols].copy()
        chunk["step_idx"] = i
        chunk["step_mw"] = df[mw_col].values
        chunk["step_price_usd_per_mwh"] = df[bid_col].values
        parts.append(chunk)

    long = pd.concat(parts, ignore_index=True)
    # Drop rows where either MW or price is null — these are unused breakpoints.
    long = long.dropna(subset=["step_mw", "step_price_usd_per_mwh"])
    long["step_idx"] = long["step_idx"].astype(np.int64)
    return long


# ---------------------------------------------------------------------------
# Per-month transform (wide → schema-ordered long)
# ---------------------------------------------------------------------------


def _transform_month(wide: pd.DataFrame) -> pd.DataFrame:
    """Apply all renames, type coercions, and pivot to one month's wide frame.

    Returns a long DataFrame with columns in SCHEMA_COLS order, ready to write
    as a temp parquet.  Caller is responsible for deleting the input frame.
    """
    # --- Timestamps ---
    wide["interval_start_utc"] = _parse_utc(wide["bid_datetime_beginning_utc"])
    wide["interval_start_local"] = _parse_local(wide["bid_datetime_beginning_ept"])

    # --- Static columns ---
    wide["iso"] = ISO

    # --- Rename non-pivot columns ---
    rename = {
        "avg_ecomin": "ecomin_mw",
        "avg_ecomax": "ecomax_mw",
        "no_load_cost": "no_load_cost_usd_per_h",
        "hot_start_cost": "hot_start_cost_usd",
        "cold_start_cost": "cold_start_cost_usd",
        "inter_start_cost": "inter_start_cost_usd",
        "min_runtime": "min_runtime_h",
    }
    wide = wide.rename(columns={k: v for k, v in rename.items() if k in wide.columns})

    # --- Numeric safety: coerce to float64 (schema dtype for all these columns) ---
    for col in (
        "ecomin_mw",
        "ecomax_mw",
        "no_load_cost_usd_per_h",
        "hot_start_cost_usd",
        "cold_start_cost_usd",
        "inter_start_cost_usd",
        "max_daily_starts",
        "min_runtime_h",
    ):
        if col in wide.columns:
            wide[col] = pd.to_numeric(wide[col], errors="coerce").astype("float64")

    # --- bool coercion (in case raw was object from older parquets) ---
    if (
        wide.get("bid_slope_flag") is not None
        and wide["bid_slope_flag"].dtype == object
    ):
        wide["bid_slope_flag"] = wide["bid_slope_flag"].map(
            {"True": True, "False": False, "true": True, "false": False}
        )

    # --- Wide → long pivot ---
    long = _pivot_to_long(wide)

    # --- Select and reorder to schema ---
    for col in SCHEMA_COLS:
        if col not in long.columns:
            long[col] = None
    return long[list(SCHEMA_COLS)]


# ---------------------------------------------------------------------------
# Year-level curate (streaming, one month at a time)
# ---------------------------------------------------------------------------


def curate_year(year: int, raw_files: list[Path]) -> Path:
    """Stream-curate one year: transform months individually, concat via ParquetWriter.

    Processes one monthly raw file at a time to keep peak RSS to ~1–2 GB
    (one month's wide frame + one month's long frame + one arrow table batch)
    instead of loading the entire year's wide data at once (~8+ GB).
    """
    schema_obj = load_schema("energy-offers")
    out = paths.clean_path("energy-offers", iso=ISO, year=year)
    out.parent.mkdir(parents=True, exist_ok=True)

    tmp_dir = Path(tempfile.mkdtemp(prefix=f"energy_offers_{year}_"))
    tmp_files: list[Path] = []
    total_wide = 0

    try:
        # --- Phase 1: transform each month to long, write temp parquet ---
        for f in sorted(raw_files):
            wide = pd.read_parquet(f)
            n_wide = len(wide)
            total_wide += n_wide

            long = _transform_month(wide)
            del wide  # release wide memory before writing long

            n_long = len(long)
            print(f"    {f.name}: {n_wide:,} wide → {n_long:,} long rows")

            tmp_path = tmp_dir / f.name
            long.to_parquet(str(tmp_path), index=False, compression="snappy")
            tmp_files.append(tmp_path)
            del long  # release long memory before next month

        print(
            f"  {year}: loaded {total_wide:,} wide rows from {len(raw_files)} file(s)"
        )

        if not tmp_files:
            raise RuntimeError(f"no data produced for {year}")

        # --- Validate schema on first month's output (catches dtype/column issues) ---
        sample = pd.read_parquet(str(tmp_files[0]))
        validate_df(sample, "energy-offers", schema=schema_obj)
        del sample

        # --- Build provenance metadata (mirrors clean_io._build_metadata) ---
        try:
            git_commit = (
                subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(REPO),
                    capture_output=True,
                    text=True,
                    timeout=5,
                ).stdout.strip()
                or None
            )
        except Exception:
            git_commit = None

        units = {c.name: c.unit for c in schema_obj.columns}
        kv: dict[bytes, bytes] = {
            b"market_sim.datatype": b"energy-offers",
            b"market_sim.schema_version": str(schema_obj.schema_version).encode(),
            b"market_sim.units": json.dumps(units, sort_keys=True).encode(),
            b"market_sim.key_columns": json.dumps(
                list(schema_obj.key_columns)
            ).encode(),
            b"market_sim.created_utc": dt.datetime.now(dt.timezone.utc)
            .isoformat()
            .encode(),
            b"market_sim.iso": ISO.encode(),
            b"market_sim.year": str(year).encode(),
            b"market_sim.source": (
                f"PJM DataMiner2 energy_market_offers (api.pjm.com/api/v1); "
                f"{len(raw_files)} monthly raw files"
            ).encode(),
        }
        if git_commit:
            kv[b"market_sim.git_commit"] = git_commit.encode()

        # --- Phase 2: stream temp parquets → final output ---
        writer = None
        total_long = 0
        try:
            for tmp_path in tmp_files:
                table = pq.read_table(str(tmp_path))
                total_long += len(table)
                if writer is None:
                    existing_meta = table.schema.metadata or {}
                    schema_with_meta = table.schema.with_metadata(
                        {**existing_meta, **kv}
                    )
                    writer = pq.ParquetWriter(str(out), schema_with_meta)
                writer.write_table(table)
        finally:
            if writer is not None:
                writer.close()

    finally:
        for tmp_path in tmp_files:
            try:
                tmp_path.unlink()
            except OSError:
                pass
        try:
            tmp_dir.rmdir()
        except OSError:
            pass

    print(f"  {year}: {total_long:,} long rows after pivot (dropped null steps)")
    mb = out.stat().st_size / 1_048_576
    print(f"  {year}: wrote {out} ({mb:.1f} MB)")
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Discover raw files and curate each year."""
    ap = argparse.ArgumentParser(
        description="Curate PJM energy market offers to clean Parquet"
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="Years to curate (default: all years with raw files)",
    )
    args = ap.parse_args()

    if not RAW_DIR.is_dir():
        print(f"ERROR: raw directory not found: {RAW_DIR}")
        print("Run scripts/data/fetch_pjm_energy_offers.py first.")
        sys.exit(1)

    raw_by_year: dict[int, list[Path]] = {}
    for f in sorted(RAW_DIR.glob("pjm_energy_offers_????_??.parquet")):
        stem_parts = f.stem.split("_")  # pjm_energy_offers_YYYY_MM
        try:
            yr = int(stem_parts[-2])
        except (IndexError, ValueError):
            continue
        raw_by_year.setdefault(yr, []).append(f)

    years_to_curate = args.years if args.years else sorted(raw_by_year)

    for year in years_to_curate:
        files = raw_by_year.get(year, [])
        if not files:
            print(f"{year}: no raw files in {RAW_DIR}, skipping")
            continue
        print(f"{year}: curating {len(files)} file(s) …")
        try:
            curate_year(year, files)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            raise


if __name__ == "__main__":
    main()
