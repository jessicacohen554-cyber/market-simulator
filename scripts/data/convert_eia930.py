"""Convert long-format EIA-930 uploads into the wide per-BA hourly parquet.

The EIA Hourly Electric Grid Monitor bulk download ships two long (tidy)
parquet files per balancing authority in ``data/raw``:

* ``<BA>_fueltype.parquet`` -- one row per ``(period, fueltype)`` with the
  net generation by fuel code in ``value_mwh`` (period is UTC, tz-aware).
* ``<BA>_region.parquet``   -- one row per ``(period, type)`` with the demand
  family series (``type`` in ``D``/``DF``/``NG``/``TI``) in ``value_mwh``.

This script pivots both into the wide schema that
``data/raw/eia-930-hourly/<BA> hourly.parquet`` uses (the same layout as the existing
``ERCO hourly`` extract that ``market_sim.data.renewables`` /
``market_sim.data.eia_loader`` consume): one row per hour with ``NG: <CODE>``
generation columns, the ``Demand``/``Demand forecast``/``Net generation``/
``Total interchange`` series, and the ``UTC time`` / ``Local date`` /
``Hour`` / ``Local time`` index built from each BA's local timezone.

Only the columns the loader needs are reproduced; the original EIA "adjusted",
CO2 and subregion columns are not part of the long uploads and are omitted.

The conversion is idempotent: a BA whose output already exists is left
untouched (so the hand-curated ``ERCO hourly`` extract is never overwritten)
unless ``--force`` is given, and a BA with no input parquet is skipped.

Run:
    python scripts/data/convert_eia930.py            # all present BAs
    python scripts/data/convert_eia930.py CISO MISO  # selected BAs
    python scripts/data/convert_eia930.py --force     # regenerate existing outputs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import EIA_HOURLY_DIR, RAW_DIR  # noqa: E402

# Both roots moved in the W1 relocation: the raw EIA-930 downloads to
# paths.RAW_DIR (data/raw) and the converted hourly parquets to
# paths.EIA_HOURLY_DIR (data/raw/eia-930-hourly, formerly data/eia_hourly).
INPUT_DIR = RAW_DIR
OUTPUT_DIR = EIA_HOURLY_DIR

# EIA-930 balancing-authority local timezone. The Hourly Grid Monitor reports
# each BA on its own local clock; these are the IANA/Olson zones EIA uses for
# the BAs uploaded so far.
# Source: EIA Hourly Electric Grid Monitor, BA reference table.
BA_TIMEZONES: dict[str, str] = {
    "ERCO": "US/Central",  # ERCOT (Texas)
    "CISO": "US/Pacific",  # CAISO (California)
    "PJM": "US/Eastern",  # PJM Interconnection
    "NYIS": "US/Eastern",  # NYISO (New York)
    "MISO": "US/Central",  # Midcontinent ISO
    "SWPP": "US/Central",  # Southwest Power Pool
    "ISNE": "US/Eastern",  # ISO New England
    "FLA": "US/Eastern",  # Florida (FPL)
    "SOCO": "US/Central",  # Southern Company
}

# EIA-930 region ``type`` code -> wide demand-family column name.
REGION_TYPE_TO_COLUMN: dict[str, str] = {
    "D": "Demand",
    "DF": "Demand forecast",
    "NG": "Net generation",
    "TI": "Total interchange",
}

# Order of the wide demand-family columns, matching the existing ERCO extract.
_REGION_COLUMN_ORDER: tuple[str, ...] = (
    "Demand forecast",
    "Demand",
    "Net generation",
    "Total interchange",
)

# Canonical ordering of the ``NG: <CODE>`` generation columns, following the
# existing ``ERCO hourly`` extract; any fuel code not listed here is appended
# alphabetically so new BAs with extra fuels still convert.
_FUEL_CODE_ORDER: tuple[str, ...] = (
    "COL",
    "NG",
    "NUC",
    "WAT",
    "SUN",
    "WND",
    "GEO",
    "OIL",
    "BAT",
    "PS",
    "SNB",
    "UES",
    "OES",
    "OTH",
)

_TIME_COLUMNS: tuple[str, ...] = ("UTC time", "Local date", "Hour", "Local time")


def _pivot_long(
    df: pd.DataFrame, key_column: str, value_column: str = "value_mwh"
) -> pd.DataFrame:
    """Pivot a long EIA-930 frame to one column per ``key_column`` value.

    Args:
        df: Long-format frame with a UTC ``period`` column, ``key_column``
            and ``value_column``.
        key_column: Column whose distinct values become the wide columns
            (``fueltype`` or ``type``).
        value_column: Column holding the hourly MWh values.

    Returns:
        A frame indexed by ``period`` with one column per ``key_column``
        value (vectorized pivot; no per-hour iteration).
    """
    return df.pivot_table(
        index="period", columns=key_column, values=value_column, aggfunc="first"
    )


def _ordered_fuel_columns(codes: list[str]) -> list[str]:
    """Return ``NG: <CODE>`` column names in the canonical fuel order."""
    known = [c for c in _FUEL_CODE_ORDER if c in codes]
    extra = sorted(c for c in codes if c not in _FUEL_CODE_ORDER)
    return [f"NG: {code}" for code in known + extra]


def _build_time_columns(period: pd.Series, timezone: str) -> pd.DataFrame:
    """Build the ``UTC time`` / ``Local date`` / ``Hour`` / ``Local time`` index.

    ``period`` is tz-aware UTC. ``UTC time`` is the naive UTC wall clock and
    ``Local time`` is the naive local wall clock in ``timezone`` (with DST
    applied, so a spring-forward hour is skipped and a fall-back hour repeats).

    EIA uses an hour-ending convention: local midnight ``00:00`` is hour 24 of
    the *previous* local date, and ``Hour`` runs 1..24 (1..23 on a spring
    forward day, 1..25 on a fall back day). ``Local date`` is therefore the
    date of ``Local time`` shifted back one hour, and ``Hour`` is the 1-based
    ordinal of each row within its local date (chronological by UTC).

    Args:
        period: Sorted tz-aware UTC timestamps, one per hour.
        timezone: IANA/Olson zone name for the BA's local clock.

    Returns:
        A frame with the four index columns, aligned to ``period``'s index.
    """
    utc_naive = period.dt.tz_convert("UTC").dt.tz_localize(None)
    local_naive = period.dt.tz_convert(timezone).dt.tz_localize(None)
    shifted = local_naive - pd.Timedelta(hours=1)
    local_date = shifted.dt.normalize()
    # Hour is the 1-based position within each local date; cumcount over the
    # date groups (already in chronological UTC order) is fully vectorized and
    # reproduces the 1..25 EIA hour-ending numbering across DST transitions.
    hour = local_date.groupby(local_date).cumcount() + 1
    return pd.DataFrame(
        {
            "UTC time": utc_naive.astype("datetime64[us]"),
            "Local date": local_date.astype("datetime64[us]"),
            "Hour": hour.astype("int64"),
            "Local time": local_naive.astype("datetime64[us]"),
        }
    )


def convert_ba(ba: str, input_dir: Path) -> pd.DataFrame:
    """Convert one BA's long ``_fueltype`` + ``_region`` files to wide hourly.

    Args:
        ba: EIA-930 balancing-authority code, e.g. ``"CISO"``.
        input_dir: Directory holding ``<BA>_fueltype.parquet`` and
            ``<BA>_region.parquet``.

    Returns:
        The wide hourly frame in the ``ERCO hourly`` schema (time index +
        demand-family columns + ``NG: <CODE>`` generation columns), sorted
        chronologically by UTC.

    Raises:
        KeyError: if ``ba`` has no known local timezone.
    """
    timezone = BA_TIMEZONES[ba]
    region = pd.read_parquet(input_dir / f"{ba}_region.parquet")
    region_wide = _pivot_long(region, "type").rename(columns=REGION_TYPE_TO_COLUMN)

    # Fueltype (per-fuel net generation) is optional: some BAs (e.g. MISO)
    # publish only the region demand family. The reference-price seam needs only
    # the ``Demand`` column for its load shape, so a region-only BA still yields
    # a usable hourly extract — just with no ``NG: <CODE>`` generation columns.
    fueltype_path = input_dir / f"{ba}_fueltype.parquet"
    if fueltype_path.exists():
        gen_wide = _pivot_long(pd.read_parquet(fueltype_path), "fueltype")
        gen_wide.columns = [f"NG: {code}" for code in gen_wide.columns]
        wide = region_wide.join(gen_wide, how="outer").sort_index()
    else:
        wide = region_wide.sort_index()
    period = wide.index.to_series().reset_index(drop=True)
    wide = wide.reset_index(drop=True)

    time_df = _build_time_columns(period, timezone)

    region_cols = [c for c in _REGION_COLUMN_ORDER if c in wide.columns]
    fuel_codes = [c[len("NG: ") :] for c in wide.columns if c.startswith("NG: ")]
    fuel_cols = _ordered_fuel_columns(fuel_codes)

    value_cols = region_cols + fuel_cols
    values = wide[value_cols].astype("float32")
    return pd.concat([time_df, values], axis=1)[list(_TIME_COLUMNS) + value_cols]


def _has_input(ba: str, input_dir: Path) -> bool:
    """Return whether the (mandatory) region parquet exists for ``ba``.

    The ``_region`` demand family is required; ``_fueltype`` is optional (a
    region-only BA like MISO still builds, without ``NG: <CODE>`` columns).
    """
    return (input_dir / f"{ba}_region.parquet").exists()


def _present_bas(input_dir: Path) -> list[str]:
    """Return the known BAs that have the region input parquet, BA-sorted."""
    return sorted(ba for ba in BA_TIMEZONES if _has_input(ba, input_dir))


def _summarize(ba: str, df: pd.DataFrame) -> None:
    """Print a per-year row count and a Demand / wind / solar sanity check."""
    years = df["Local date"].dt.year
    print(f"  {ba}: {len(df)} rows, years {int(years.min())}-{int(years.max())}")
    for year, group in df.groupby(years):
        demand_nonnull = int(group["Demand"].notna().sum())
        parts = [f"Demand non-null {demand_nonnull}/{len(group)}"]
        for fuel, column in (("WND", "NG: WND"), ("SUN", "NG: SUN")):
            if column in group.columns:
                parts.append(f"{fuel} sum {group[column].sum() / 1e6:.2f} TWh")
        print(f"    {int(year)}: {len(group)} rows; " + ", ".join(parts))


def main(argv: list[str] | None = None) -> int:
    """Convert the requested (or all present) BAs to wide hourly parquet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bas", nargs="*", help="BA codes to convert (default: all present)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="regenerate even if the output parquet already exists",
    )
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    requested = [ba.upper() for ba in args.bas] or _present_bas(args.input_dir)

    for ba in requested:
        if ba not in BA_TIMEZONES:
            print(f"  {ba}: unknown BA (no timezone); skipping")
            continue
        if not _has_input(ba, args.input_dir):
            print(f"  {ba}: no input parquet; skipping")
            continue
        out_path = args.output_dir / f"{ba} hourly.parquet"
        if out_path.exists() and not args.force:
            print(
                f"  {ba}: {out_path.name} already exists; skipping (--force to rebuild)"
            )
            continue

        df = convert_ba(ba, args.input_dir)
        df.to_parquet(out_path, index=False)
        _summarize(ba, df)
        print(f"  -> wrote {out_path.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
