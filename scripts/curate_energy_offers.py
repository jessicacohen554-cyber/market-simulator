"""Curate the ``energy-offers`` clean datatype from raw PJM DataMiner2 parquets.

Reads the monthly wide-format Parquet files produced by
``scripts/fetch_pjm_energy_offers.py`` (under ``data/raw/pjm-energy-offers/``)
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

Run
---
    python scripts/curate_energy_offers.py              # all years with raw data
    python scripts/curate_energy_offers.py --years 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import write_clean  # noqa: E402

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
# Year-level curate
# ---------------------------------------------------------------------------


def curate_year(year: int, raw_files: list[Path]) -> Path:
    """Load all monthly raw files for ``year``, transform, and write clean Parquet."""
    parts: list[pd.DataFrame] = []
    for f in sorted(raw_files):
        parts.append(pd.read_parquet(f))

    wide = pd.concat(parts, ignore_index=True)
    print(f"  {year}: loaded {len(wide):,} wide rows from {len(raw_files)} file(s)")

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

    # --- Numeric safety ---
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
            wide[col] = pd.to_numeric(wide[col], errors="coerce")

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
    print(f"  {year}: {len(long):,} long rows after pivot (dropped null steps)")

    # --- Select and reorder to schema ---
    for col in SCHEMA_COLS:
        if col not in long.columns:
            long[col] = None
    long = long[list(SCHEMA_COLS)]

    out = write_clean(
        long,
        "energy-offers",
        iso=ISO,
        year=year,
        source=(
            f"PJM DataMiner2 energy_market_offers (api.pjm.com/api/v1); "
            f"{len(raw_files)} monthly raw files"
        ),
    )
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
        print("Run scripts/fetch_pjm_energy_offers.py first.")
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
