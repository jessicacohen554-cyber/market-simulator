#!/usr/bin/env python3
"""Prepend pre-2022 years to a BA's wide hourly extract from the BALANCE bulk archive.

``data/raw/eia-930-hourly/<BA> hourly.parquet`` (read by
``market_sim.data.eia_loader._eia_hourly_frame``) was built for CISO/PJM/MISO
from the EIA API v2 long-format extracts, which only reach back to ~2022 on
disk and require ``api.eia.gov`` (blocked in this sandbox) to pull further
history. The six-month BALANCE bulk archive
(``data/raw/eia-930/EIA930_BALANCE_<year>_<half>.parquet``, fetched via
``fetch_eia930_balance.py`` from the unblocked ``www.eia.gov`` host) carries
the same demand + fuel-type series for every BA and reaches back to 2019.

This script rebuilds the wide row set for one BA from the BALANCE bulk files
and prepends any UTC hour not already present in the committed hourly extract
-- existing rows are never altered (``keep="last"`` on a UTC-time dedup always
favors the already-committed row).

Fidelity caveat: the BALANCE bulk archive's legacy (pre-mid-2024) taxonomy
does not break out geothermal or battery storage as their own fuel columns,
and reports hydro + pumped storage as one combined figure. Rows sourced from
this script therefore fold "NG: GEO" and "NG: BAT" into "NG: OTH" (NaN, not
zero, in the target column when the target extract carries one) -- real
missing granularity, not a fabricated split. ``NG: WAT`` already means
"hydro + pumped storage" in the existing CISO/PJM/MISO extracts (they have no
separate ``NG: PS`` column either), so that mapping is unchanged.

Usage:
    python scripts/extend_eia930_hourly_from_balance.py --ba CISO
    python scripts/extend_eia930_hourly_from_balance.py --ba PJM --ba MISO
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

# Years the BALANCE bulk archive was extended to cover in this pass; only
# these are prepended regardless of what precedes them in the archive.
_EXTEND_YEARS: tuple[int, ...] = (2019, 2020, 2021)
_HALVES: tuple[str, ...] = ("Jan_Jun", "Jul_Dec")

_REGION_MAP: dict[str, str] = {
    "Demand Forecast (MW)": "Demand forecast",
    "Demand (MW)": "Demand",
    "Net Generation (MW)": "Net generation",
    "Total Interchange (MW)": "Total interchange",
}

# BALANCE bulk fuel column -> ``NG: <code>``. Geothermal/battery are not
# broken out in the legacy taxonomy -- see the module docstring.
_FUEL_MAP: dict[str, str] = {
    "Net Generation (MW) from Coal": "COL",
    "Net Generation (MW) from Natural Gas": "NG",
    "Net Generation (MW) from Nuclear": "NUC",
    "Net Generation (MW) from All Petroleum Products": "OIL",
    "Net Generation (MW) from Hydropower and Pumped Storage": "WAT",
    "Net Generation (MW) from Solar": "SUN",
    "Net Generation (MW) from Wind": "WND",
}
_OTHER_COLS: tuple[str, ...] = (
    "Net Generation (MW) from Other Fuel Sources",
    "Net Generation (MW) from Unknown Fuel Sources",
)


def _load_balance_rows(ba: str) -> pd.DataFrame:
    """Concatenate one BA's rows across every extended-year BALANCE file."""
    frames = []
    for year in _EXTEND_YEARS:
        for half in _HALVES:
            path = BALANCE_DIR / f"EIA930_BALANCE_{year}_{half}.parquet"
            df = pd.read_parquet(path)
            frames.append(df[df["Balancing Authority"] == ba])
    if not frames or sum(len(f) for f in frames) == 0:
        raise ValueError(f"no BALANCE rows found for BA {ba!r}")
    return pd.concat(frames, ignore_index=True)


def build_new_rows(ba: str, target_fuel_cols: list[str]) -> pd.DataFrame:
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
    raw = _load_balance_rows(ba)

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

    fuel = pd.DataFrame(index=raw.index)
    for col, code in _FUEL_MAP.items():
        fuel[code] = pd.to_numeric(raw[col], errors="coerce")
    fuel["OTH"] = sum(
        pd.to_numeric(raw[col], errors="coerce").fillna(0.0) for col in _OTHER_COLS
    )

    for name in target_fuel_cols:
        code = name[len("NG: ") :]
        out[name] = fuel[code].astype("float32") if code in fuel.columns else pd.NA

    return out.sort_values("UTC time").reset_index(drop=True)


def extend_ba(ba: str, force: bool) -> Path:
    """Prepend the extended years to ``<ba> hourly.parquet``, existing rows untouched."""
    out_path = OUT_DIR / f"{ba} hourly.parquet"
    existing = pd.read_parquet(out_path)
    fuel_cols = [c for c in existing.columns if c.startswith("NG: ")]

    new_rows = build_new_rows(ba, fuel_cols)
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
        "--force",
        action="store_true",
        help="unused placeholder for symmetry with sibling fetch scripts",
    )
    args = ap.parse_args()
    for ba in args.bas:
        extend_ba(ba, args.force)


if __name__ == "__main__":
    sys.exit(main())
