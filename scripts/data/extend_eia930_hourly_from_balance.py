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
    python scripts/data/extend_eia930_hourly_from_balance.py --ba CISO
    python scripts/data/extend_eia930_hourly_from_balance.py --ba PJM --ba MISO
    python scripts/data/extend_eia930_hourly_from_balance.py --ba PJM --ba CISO \
        --ba MISO --year 2018
    python scripts/data/extend_eia930_hourly_from_balance.py --ba CISO --ba MISO \
        --year 2026
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import EIA_930_DIR, EIA_HOURLY_DIR  # noqa: E402

BALANCE_DIR = EIA_930_DIR
OUT_DIR = EIA_HOURLY_DIR

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
    # A fuel column the source taxonomy lacks arrives all-``pd.NA`` (object);
    # left as-is, the concat below upcasts that column of the COMMITTED rows
    # float32 -> float64. Cast every new column to the extract's own dtype so
    # the existing rows stay byte-identical (I-SOCO, 2026-09-24).
    for col, dtype in existing.dtypes.items():
        if new_rows[col].dtype != dtype:
            new_rows[col] = pd.to_numeric(new_rows[col]).astype(dtype)

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


# ---------------------------------------------------------------------------
# PJM fueltype input-clock repair (DEBUG-B, 2026-08;
# docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md §1/§3, chartered
# under owner decision D-5).  The ``NG:`` fuel-type family of the committed
# ``PJM hourly.parquet`` ran one hour EARLY at the EIA-930 source (fixed
# upstream ~Feb-2025), so the 2023 and 2024 blocks sit one slot ahead of the
# UTC hour they measure.  The repair is *value-preserving*: each affected cell
# keeps its measured value and only moves to the UTC hour it actually belongs
# to -- no re-pull, no interpolation, no tuning (rules 13/14).
#
# Measured on main @ c447199 with the repo's own instruments, both unchanged:
#
#   scripts/probes/_pjm2025_phase_drift.py
#     * B. July ``NG: SUN`` generation-weighted centroid (astronomically fixed
#       at ~11.9, gate [11.5, 12.3]):  2023 = 10.91, 2024 = 10.94, 2025 = 12.03
#     * C. ``Demand`` vs PJM ``hrl_load_metered``: best lag 0 in every year and
#       season -- the REGION family is already healed and is NOT touched here.
#   scripts/probes/_pjm2025_wind_anchor.py (vs the PJM UTC-stamped feed)
#     * WIND/SOLAR/GAS diff-series best lag: 2023 +1, 2024 +1, 2025 0.
#
# This supersedes the archived 2026-07 M-1 transform
# (``patches/archive/pjm-m1-code.patch``, see
# ``patches/archive/ARCHIVED-2026-08-14-pjm-m1.md``), whose *2023 region -1 h*
# leg would now double-shift a correct family and whose *2023 fueltype kept*
# leg would leave the defect in place: the parquet was replaced after the
# 2026-07 diagnosis (last touch PR #3852's lane), healing the region family and
# thereby exposing the source's 1 h-early fueltype clock in 2023 that the
# offsetting construction error had been masking.
#
# 2025 is left untouched (the source was correct from ~Feb-2025); January-2025
# straddles the upstream switch (centroid 11.15) and stays as measured --
# correcting a sub-month straddle would require fabricating a switch hour
# (rule 14), so it is documented, not shifted.
#
# 2018-2022 EXTENSION (owner-signed charter, 2026-08-16 DEBUG-manager reissue
# sitting; FINDING-debug-b-pjm-input-clock-2026-08-15.md section 6 filed the
# inconsistency, audit third-party-audit-2026-08.md section 8 row O3 routed
# it): the 1 h-early source clock is a property of EIA-930 until ~Feb-2025,
# so the same value-preserving +1 h re-placement applies to every earlier
# year in the extract (2022 July NG: SUN centroid read 10.73 pre-fix against
# the astronomical ~11.9).  Data repair only -- no <=2022 year is solved,
# scored or registered by the charter; the holdout tiers and the spend
# freeze are untouched (rule 22: what is held out is the SCORE, never the
# data).  The first local-2018 hour's source instant (2018-01-01 05:00Z)
# precedes the extract, so that one row's NG:* cells become NaN rather than
# fabricated (rule 14).
#
# THIS TABLE IS THE FULL DECLARED RECORD of shifts embodied in the committed
# extract -- it is documentation plus a one-shot migration input, NOT an
# idempotent transform.  Because ``rebuild_pjm_input_clock`` reads the
# COMMITTED extract, re-applying an entry already embodied in it would
# double-shift that block (the archived patch README's "a second run
# double-shifts" warning).  ``--rebuild-pjm-input-clock`` therefore requires
# an explicit ``--apply-years`` naming ONLY the not-yet-embodied entries:
# 2023+2024 were applied by DEBUG-B (merged 2026-08-15); 2018-2022 by the
# extension charter run.
_PJM_INPUT_CLOCK_SHIFTS: tuple[tuple[int, str, int], ...] = (
    # (local-date year, family, hours to move the CONTENT: +1 = later)
    (2018, "fueltype", +1),
    (2019, "fueltype", +1),
    (2020, "fueltype", +1),
    (2021, "fueltype", +1),
    (2022, "fueltype", +1),
    (2023, "fueltype", +1),
    (2024, "fueltype", +1),
)


def _replace_family_by_utc_shift(
    df: pd.DataFrame,
    source: pd.DataFrame,
    year: int,
    cols: list[str],
    content_shift_h: int,
) -> pd.DataFrame:
    """Move ``cols`` for local-year ``year`` rows by ``content_shift_h`` hours.

    Value-preserving: the new value at a row whose UTC hour is ``T`` is the
    value ``source`` holds at ``T - content_shift_h`` (so a ``+1`` shift pulls
    each cell's content one hour LATER onto its row, correcting a series that
    was stamped one hour early).  ``source`` spans 2018-2026 contiguously, so a
    year-boundary row reads its immediate UTC neighbour and no NaN is
    introduced inside ``year``.  The row grid, the time columns, and every cell
    outside (``year``, ``cols``) are untouched.

    ``source`` is read separately from ``df`` (the accumulating output) so that
    every block is re-placed against the **pristine** committed values.  When
    two shifted year-blocks are adjacent -- as 2023 and 2024 are -- sourcing
    from the accumulating frame would make the second block's first row read a
    slot the first block had already moved, double-shifting exactly that
    boundary hour (the archived patch README's "a second run double-shifts"
    warning, in a within-run form).

    Args:
        df: The accumulating output frame (UTC-unique, UTC-sorted).
        source: The pristine committed extract every block is sourced from.
        year: Local-date calendar year whose ``cols`` are re-placed.
        cols: Value columns to move (the ``NG:`` fuel-type family list).
        content_shift_h: Signed hours to move the content (+1 later / -1 earlier).

    Returns:
        A copy of ``df`` with only the (``year``, ``cols``) block re-placed.
    """
    out = df.sort_values("UTC time").reset_index(drop=True).copy()
    utc = pd.DatetimeIndex(out["UTC time"])
    by_utc = source.sort_values("UTC time").set_index("UTC time")
    # Row T takes the pristine committed value at UTC (T - content_shift_h).
    src_utc = utc - pd.Timedelta(hours=content_shift_h)
    src = by_utc[cols].reindex(src_utc).reset_index(drop=True)
    mask = (out["Local date"].dt.year == year).to_numpy()
    for col in cols:
        arr = out[col].to_numpy().copy()
        arr[mask] = src[col].to_numpy()[mask]
        out[col] = arr.astype(df[col].dtype)
    return out


def rebuild_pjm_input_clock(force: bool, apply_years: list[int]) -> Path:
    """Apply the PJM fueltype input-clock re-placement to ``PJM hourly.parquet``.

    Reads the committed wide extract and applies the
    :data:`_PJM_INPUT_CLOCK_SHIFTS` entries whose year is in ``apply_years``
    as value-preserving UTC-time re-placements, writing the corrected extract
    back in the identical schema.  ``apply_years`` is REQUIRED and must name
    only entries not already embodied in the committed file: the source of
    every block is the committed extract itself, so re-applying an
    already-applied entry double-shifts that block (see the table's
    module-level notes).  DEBUG-B applied 2023+2024 (charter
    ``docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md`` §3); the
    owner-signed 2026-08-16 extension applied 2018-2022.
    """
    unknown = [
        y for y in apply_years if y not in {y_ for y_, _, _ in _PJM_INPUT_CLOCK_SHIFTS}
    ]
    if unknown:
        raise SystemExit(
            f"--apply-years {unknown} not declared in _PJM_INPUT_CLOCK_SHIFTS; "
            "declare the shift (with its charter citation) before applying it"
        )
    out_path = OUT_DIR / "PJM hourly.parquet"
    df = pd.read_parquet(out_path)
    original_cols = list(df.columns)
    fuel_cols = [c for c in df.columns if c.startswith("NG: ")]
    # Every block is sourced from this pristine frame, never from the
    # accumulating output -- see _replace_family_by_utc_shift on why adjacent
    # shifted years would otherwise double-shift their shared boundary hour.
    pristine = df.copy()
    for year, family, shift in _PJM_INPUT_CLOCK_SHIFTS:
        if year not in apply_years:
            continue
        if family != "fueltype":
            raise ValueError(f"unsupported family {family!r}")
        df = _replace_family_by_utc_shift(df, pristine, year, fuel_cols, shift)
        print(
            f"  PJM {year} {family} family: content shifted {shift:+d} h "
            f"({len(fuel_cols)} cols)"
        )
    df = df[original_cols]
    if not force:
        tmp = out_path.with_suffix(".parquet.new")
        df.to_parquet(tmp, index=False)
        tmp.replace(out_path)
    else:
        df.to_parquet(out_path, index=False)
    print(f"  -> wrote {out_path}")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rebuild-pjm-input-clock",
        action="store_true",
        help="Apply the PJM fueltype clock re-placement to the committed "
        "PJM hourly.parquet for the years named by --apply-years, and exit; "
        "value-preserving one-shot migration (never idempotent -- see the "
        "_PJM_INPUT_CLOCK_SHIFTS notes). DEBUG-B applied 2023 2024; the "
        "owner-signed 2026-08-16 extension applied 2018-2022.",
    )
    ap.add_argument(
        "--apply-years",
        type=int,
        nargs="+",
        help="REQUIRED with --rebuild-pjm-input-clock: the declared shift "
        "entries to apply now. Name ONLY years not already embodied in the "
        "committed extract -- re-applying an applied entry double-shifts it.",
    )
    ap.add_argument("--ba", action="append", dest="bas")
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
    if args.rebuild_pjm_input_clock:
        if not args.apply_years:
            ap.error(
                "--rebuild-pjm-input-clock requires --apply-years (the "
                "not-yet-embodied shift entries; see _PJM_INPUT_CLOCK_SHIFTS)"
            )
        rebuild_pjm_input_clock(args.force, args.apply_years)
        return
    if not args.bas:
        ap.error("--ba is required unless --rebuild-pjm-input-clock is given")
    years = tuple(args.years) if args.years else _DEFAULT_EXTEND_YEARS
    halves = tuple(args.halves) if args.halves else _DEFAULT_HALVES
    for ba in args.bas:
        extend_ba(ba, args.force, years, halves)


if __name__ == "__main__":
    sys.exit(main())
