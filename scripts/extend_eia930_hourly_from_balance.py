#!/usr/bin/env python3
"""Fold extra years into a BA's wide hourly extract from the BALANCE bulk archive.

``data/raw/eia-930-hourly/<BA> hourly.parquet`` (read by
``market_sim.data.eia_loader._eia_hourly_frame``) was built for CISO/PJM/MISO
from the EIA API v2 long-format extracts, which only reach back to ~2022 on
disk and require ``api.eia.gov`` (blocked in this sandbox) to pull further
history. The six-month BALANCE bulk archive
(``data/raw/eia-930/EIA930_BALANCE_<year>_<half>.parquet``, fetched via
``fetch_eia930_balance.py`` from the unblocked ``www.eia.gov`` host) carries
the same demand + fuel-type series for every BA and reaches back to 2018.

This script rebuilds the wide row set for one BA from the requested BALANCE
bulk files and merges in any UTC hour not already present in the committed
hourly extract -- existing rows are never altered (``keep="last"`` on a
UTC-time dedup always favors the already-committed row), and the merged frame
is re-sorted by UTC time, so ``--years`` may fall before, inside, or after the
extract's current span (a prepend, a gap-fill, or an append) in the same
pass. A requested ``<year>_<half>`` file that doesn't exist on disk yet (e.g.
the second half of the current year) is skipped with a note, not an error.

Fidelity caveat: the BALANCE bulk archive's legacy (pre-mid-2024) taxonomy
does not break out geothermal or battery storage as their own fuel columns
at all, and reports hydro + pumped storage as one combined figure -- rows
sourced from a legacy year fold "NG: GEO" and "NG: BAT" into "NG: OTH" (NaN,
not zero, real missing granularity, not a fabricated split). EIA's mid-2024
taxonomy revamp (2024H2 BALANCE files onward) DOES break out Geothermal and
Battery Storage as their own columns, and splits hydro/solar/wind by
pumped-storage / integrated-battery status; a new-taxonomy source year maps
Geothermal/Battery 1:1 into "NG: GEO"/"NG: BAT" when the target extract
already carries that column (folding into OTH otherwise, e.g. MISO has no
"NG: GEO" column), and sums the hydro/solar/wind splits back into the one
"NG: WAT"/"NG: SUN"/"NG: WND" code the legacy taxonomy (and the existing
CISO/PJM/MISO extracts) use for that fuel -- unchanged meaning either way.

Usage:
    python scripts/extend_eia930_hourly_from_balance.py --ba CISO
    python scripts/extend_eia930_hourly_from_balance.py --ba PJM --ba MISO
    python scripts/extend_eia930_hourly_from_balance.py --ba PJM --ba CISO \
        --ba MISO --year 2018
    python scripts/extend_eia930_hourly_from_balance.py --ba CISO --ba MISO \
        --year 2026
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

REPO = Path(__file__).resolve().parent.parent
BALANCE_DIR = REPO / "data" / "raw" / "eia-930"
OUT_DIR = REPO / "data" / "raw" / "eia-930-hourly"

# Default years/halves -- the original 2019-2021 backfill pass. Override with
# --year / --half to fold in a different span (e.g. 2018, or 2026 H1-only).
_DEFAULT_EXTEND_YEARS: tuple[int, ...] = (2019, 2020, 2021)
_DEFAULT_HALVES: tuple[str, ...] = ("Jan_Jun", "Jul_Dec")

_REGION_MAP: dict[str, str] = {
    "Demand Forecast (MW)": "Demand forecast",
    "Demand (MW)": "Demand",
    "Net Generation (MW)": "Net generation",
    "Total Interchange (MW)": "Total interchange",
}

# BALANCE bulk fuel column -> ``NG: <code>`` (legacy, pre-mid-2024 taxonomy).
# Geothermal/battery are not broken out at all -- see the module docstring.
_LEGACY_FUEL_MAP: dict[str, str] = {
    "Net Generation (MW) from Coal": "COL",
    "Net Generation (MW) from Natural Gas": "NG",
    "Net Generation (MW) from Nuclear": "NUC",
    "Net Generation (MW) from All Petroleum Products": "OIL",
    "Net Generation (MW) from Hydropower and Pumped Storage": "WAT",
    "Net Generation (MW) from Solar": "SUN",
    "Net Generation (MW) from Wind": "WND",
}
_LEGACY_OTHER_COLS: tuple[str, ...] = (
    "Net Generation (MW) from Other Fuel Sources",
    "Net Generation (MW) from Unknown Fuel Sources",
)

# EIA's mid-2024 taxonomy revamp (detected via the "Excluding Pumped Storage"
# marker column, same test as fetch_eia930_balance.py's ``is_new``) splits
# hydro/solar/wind by pumped-storage / integrated-battery status and adds
# Geothermal + Battery/Other/Unknown Energy Storage as their own columns.
# Direct 1:1 fuel codes:
_NEW_FUEL_MAP: dict[str, str] = {
    "Net Generation (MW) from Coal": "COL",
    "Net Generation (MW) from Natural Gas": "NG",
    "Net Generation (MW) from Nuclear": "NUC",
    "Net Generation (MW) from All Petroleum Products": "OIL",
}
# Split pairs summed back into the one code the legacy taxonomy (and the
# existing CISO/PJM/MISO extracts) use for that fuel.
_NEW_SUM_MAP: dict[str, tuple[str, ...]] = {
    "WAT": (
        "Net Generation (MW) from Hydropower Excluding Pumped Storage",
        "Net Generation (MW) from Pumped Storage",
    ),
    "SUN": (
        "Net Generation (MW) from Solar without Integrated Battery Storage",
        "Net Generation (MW) from Solar with Integrated Battery Storage",
    ),
    "WND": (
        "Net Generation (MW) from Wind without Integrated Battery Storage",
        "Net Generation (MW) from Wind with Integrated Battery Storage",
    ),
}
# Mapped 1:1 ONLY when the target extract already carries that column (e.g.
# CISO has NG: GEO, MISO has NG: BAT) -- otherwise folded into OTH like any
# other ungranular source, same as the legacy fold.
_NEW_OPTIONAL_MAP: dict[str, str] = {
    "GEO": "Net Generation (MW) from Geothermal",
    "BAT": "Net Generation (MW) from Battery Storage",
}
_NEW_OTHER_COLS: tuple[str, ...] = (
    "Net Generation (MW) from Other Energy Storage",
    "Net Generation (MW) from Unknown Energy Storage",
    "Net Generation (MW) from Other Fuel Sources",
    "Net Generation (MW) from Unknown Fuel Sources",
)


def _sum_or_nan(cols: list[pd.Series]) -> pd.Series:
    """Sum real values across ``cols``; NaN (not 0) where ALL are absent."""
    total = sum(c.fillna(0.0) for c in cols)
    total[pd.concat(cols, axis=1).isna().all(axis=1)] = pd.NA
    return total


def _load_balance_rows(
    ba: str, years: tuple[int, ...], halves: tuple[str, ...]
) -> pd.DataFrame:
    """Concatenate one BA's rows across every requested BALANCE file."""
    frames = []
    for year in years:
        for half in halves:
            path = BALANCE_DIR / f"EIA930_BALANCE_{year}_{half}.parquet"
            if not path.exists():
                print(f"  ({path.name} not on disk yet -- skipping)")
                continue
            df = pd.read_parquet(path)
            frames.append(df[df["Balancing Authority"] == ba])
    if not frames or sum(len(f) for f in frames) == 0:
        raise ValueError(f"no BALANCE rows found for BA {ba!r} in {years} {halves}")
    return pd.concat(frames, ignore_index=True)


def build_new_rows(
    ba: str,
    target_fuel_cols: list[str],
    years: tuple[int, ...],
    halves: tuple[str, ...],
) -> pd.DataFrame:
    """Build the wide extension rows for ``ba`` in the existing extract's schema.

    Args:
        ba: EIA-930 balancing-authority code (e.g. ``"CISO"``).
        target_fuel_cols: The ``NG: <code>`` columns of the extract being
            extended, in order -- a code absent from the BALANCE taxonomy
            (e.g. ``NG: GEO``, ``NG: BAT``) is filled NaN, never zero.

    Returns:
        Wide frame in the existing extract's exact column layout, sorted by
        ``UTC time``, one row per BALANCE hour for the extended years.
    """
    raw = _load_balance_rows(ba, years, halves)

    out = pd.DataFrame(
        {
            "UTC time": pd.to_datetime(raw["UTC Time at End of Hour"]).astype(
                "datetime64[us]"
            ),
            "Local date": pd.to_datetime(raw["Data Date"]).astype("datetime64[us]"),
            "Hour": raw["Hour Number"].astype("int64"),
            "Local time": pd.to_datetime(raw["Local Time at End of Hour"]).astype(
                "datetime64[us]"
            ),
        }
    )
    for col, name in _REGION_MAP.items():
        out[name] = pd.to_numeric(raw[col], errors="coerce").astype("float32")

    is_new_taxonomy = any("Excluding Pumped Storage" in c for c in raw.columns)
    fuel = pd.DataFrame(index=raw.index)
    if is_new_taxonomy:
        for col, code in _NEW_FUEL_MAP.items():
            fuel[code] = pd.to_numeric(raw[col], errors="coerce")
        for code, cols in _NEW_SUM_MAP.items():
            fuel[code] = _sum_or_nan(
                [pd.to_numeric(raw[c], errors="coerce") for c in cols]
            )
        other_cols = list(_NEW_OTHER_COLS)
        for code, col in _NEW_OPTIONAL_MAP.items():
            if f"NG: {code}" in target_fuel_cols:
                fuel[code] = pd.to_numeric(raw[col], errors="coerce")
            else:
                other_cols.append(col)
    else:
        for col, code in _LEGACY_FUEL_MAP.items():
            fuel[code] = pd.to_numeric(raw[col], errors="coerce")
        other_cols = list(_LEGACY_OTHER_COLS)

    # A row where every "other"-bucket source column is absent (e.g. all of
    # 2018 H1, which predates EIA-930 per-fuel reporting entirely) has no
    # real value to sum -- NaN, not a fabricated 0.
    fuel["OTH"] = _sum_or_nan(
        [pd.to_numeric(raw[c], errors="coerce") for c in other_cols]
    )

    for name in target_fuel_cols:
        code = name[len("NG: ") :]
        out[name] = fuel[code].astype("float32") if code in fuel.columns else pd.NA

    return out.sort_values("UTC time").reset_index(drop=True)


def extend_ba(
    ba: str, force: bool, years: tuple[int, ...], halves: tuple[str, ...]
) -> Path:
    """Fold the requested years into ``<ba> hourly.parquet``, existing rows untouched."""
    out_path = OUT_DIR / f"{ba} hourly.parquet"
    existing = pd.read_parquet(out_path)
    fuel_cols = [c for c in existing.columns if c.startswith("NG: ")]

    new_rows = build_new_rows(ba, fuel_cols, years, halves)
    new_rows = new_rows[list(existing.columns)]

    combined = pd.concat([new_rows, existing], ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset="UTC time", keep="last")
    dropped = before - len(combined)
    combined = combined.sort_values("UTC time").reset_index(drop=True)

    added = len(combined) - len(existing)
    print(
        f"  {ba}: +{added} rows ({dropped} overlapping BALANCE hours deferred to "
        f"the existing extract), {combined['Local date'].min().date()}.."
        f"{combined['Local date'].max().date()}"
    )
    if not force:
        tmp = out_path.with_suffix(".parquet.new")
        combined.to_parquet(tmp, index=False)
        tmp.replace(out_path)
    else:
        combined.to_parquet(out_path, index=False)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", action="append", required=True, dest="bas")
    ap.add_argument(
        "--year",
        action="append",
        type=int,
        dest="years",
        help="repeatable; defaults to the original 2019-2021 backfill",
    )
    ap.add_argument(
        "--half",
        action="append",
        choices=("Jan_Jun", "Jul_Dec"),
        dest="halves",
        help="repeatable; defaults to both halves",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="unused placeholder for symmetry with sibling fetch scripts",
    )
    args = ap.parse_args()
    years = tuple(args.years) if args.years else _DEFAULT_EXTEND_YEARS
    halves = tuple(args.halves) if args.halves else _DEFAULT_HALVES
    for ba in args.bas:
        extend_ba(ba, args.force, years, halves)


if __name__ == "__main__":
    sys.exit(main())
