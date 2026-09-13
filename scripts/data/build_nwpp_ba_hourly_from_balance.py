#!/usr/bin/env python3
"""Create a NEW BA's wide ``<BA> hourly`` extract from the committed BALANCE archive.

``scripts/data/extend_eia930_hourly_from_balance.py`` folds extra years into an
extract that **already exists** (it reads the committed file to learn the target
column layout).  The 17 NWPP balancing authorities have no committed extract at
all, so this script is the *create* counterpart of that *extend*: it emits the
first ``data/raw/eia-930-hourly/<BA> hourly.parquet`` for a BA from
``data/raw/eia-930/EIA930_BALANCE_<year>_<half>.parquet``, which carries every
EIA-930 BA back to 2019 (docs/multi-iso/nwpp-addition-plan-2026-09.md §2.5).

**No network, no ``EIA_API_KEY``** — the load spine for these BAs is a DERIVE
from bytes already in the repo, not a fetch (plan §6 row 2).

Every value mapping is IMPORTED from ``extend_eia930_hourly_from_balance`` and
reused verbatim (rule 23 ``[R-FROZEN-DERIVE]``): this module adds only the
create path, the taxonomy split below, and the ``(Adjusted)`` region columns.

**The taxonomy split is load-bearing.**  ``build_new_rows`` detects EIA's
mid-2024 taxonomy revamp with ``any("Excluding Pumped Storage" in c)`` over the
*concatenated* frame, so a single call spanning the switch reads as
new-taxonomy for **all** rows and returns NaN for every legacy row's hydro,
coal, solar and wind.  Measured at this pin (BPAT 2023-01-01 01:00 local: real
``NG: WAT`` 5,324 MW arriving as NaN).  This script therefore calls
``build_new_rows`` **once per taxonomy era** and concatenates:

    legacy : 2023 Jan_Jun, 2023 Jul_Dec, 2024 Jan_Jun   (44-col files)
    new    : 2024 Jul_Dec onward                        (65-col files)

The era of each half is DETECTED from its own schema, never assumed.

**Schema.**  The 17 columns of the committed siblings (``SWPP hourly.parquet``)
in their exact order and dtypes, plus three APPENDED columns carrying the
source's own screened series:

    'Demand (Adjusted)', 'Net generation (Adjusted)', 'Total interchange (Adjusted)'

The plan's §2.5 defect screen (30 bad hours in 394,424, worst 810,948 MW) is
already carried by EIA's ``(Adjusted)`` family, and NWPP-10 owns the ruling on
which family every downstream NWPP series reads.  Until that ruling lands this
script emits **both**, complete and unchosen — all three region series are
carried so the ``D = NG - TI`` triple stays internally consistent whichever
family is selected.  Nothing is padded, screened, or interpolated here.

``NG: GEO`` is deliberately NOT a column: the siblings' 17-column layout has
none, the legacy taxonomy does not break geothermal out at all, and adding the
column would make the same energy jump from ``NG: OTH`` to ``NG: GEO`` at the
2024 H2 boundary.  Folding it into ``NG: OTH`` in both eras is
``extend_eia930_hourly_from_balance``'s own ``_NEW_OPTIONAL_MAP`` convention.
Measured footprint magnitude: IPCO only, 240,452 MWh over 2024H2-2025; every
other NWPP BA reports zero.

Usage:
    python scripts/data/build_nwpp_ba_hourly_from_balance.py --all-nwpp
    python scripts/data/build_nwpp_ba_hourly_from_balance.py --ba BPAT --ba NEVP
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))  # repo root: canonical scripts.data.* sibling import
sys.path.insert(0, str(REPO / "src"))

from scripts.data.extend_eia930_hourly_from_balance import (  # noqa: E402
    BALANCE_DIR,
    OUT_DIR,
    build_new_rows,
)

# The 17 NWPP balancing authorities (plan §2.1/§2.5). AVRN and GRID are
# generation-only BAs whose ``Demand (MW)`` is null in every hour — that is
# structure, not a defect, and this script writes it through as NaN.
NWPP_BAS: tuple[str, ...] = (
    "BPAT",
    "PACE",
    "PACW",
    "PGE",
    "PSEI",
    "AVA",
    "IPCO",
    "NWMT",
    "CHPD",
    "DOPD",
    "GCPD",
    "SCL",
    "TPWR",
    "AVRN",
    "GRID",
    "WAUW",
    "NEVP",
)

# The committed siblings' exact ``NG:`` family and order (SWPP/MISO/SOCO).
SIBLING_FUEL_COLS: tuple[str, ...] = (
    "NG: COL",
    "NG: NG",
    "NG: NUC",
    "NG: WAT",
    "NG: SUN",
    "NG: WND",
    "NG: OIL",
    "NG: BAT",
    "NG: OTH",
)
SIBLING_COLS: tuple[str, ...] = (
    "UTC time",
    "Local date",
    "Hour",
    "Local time",
    "Demand forecast",
    "Demand",
    "Net generation",
    "Total interchange",
    *SIBLING_FUEL_COLS,
)

# BALANCE ``(Adjusted)`` region column -> appended output column.
ADJUSTED_MAP: dict[str, str] = {
    "Demand (MW) (Adjusted)": "Demand (Adjusted)",
    "Net Generation (MW) (Adjusted)": "Net generation (Adjusted)",
    "Total Interchange (MW) (Adjusted)": "Total interchange (Adjusted)",
}

_HALVES: tuple[str, ...] = ("Jan_Jun", "Jul_Dec")


def available_halves(years: tuple[int, ...]) -> list[tuple[int, str]]:
    """Return the (year, half) BALANCE files present on disk, in time order."""
    return [
        (y, h)
        for y in years
        for h in _HALVES
        if (BALANCE_DIR / f"EIA930_BALANCE_{y}_{h}.parquet").exists()
    ]


def _is_new_taxonomy(year: int, half: str) -> bool:
    """Detect EIA's mid-2024 taxonomy from the file's OWN schema, never assumed."""
    names = pq.read_schema(BALANCE_DIR / f"EIA930_BALANCE_{year}_{half}.parquet").names
    return any("Excluding Pumped Storage" in c for c in names)


def _adjusted_frame(ba: str, halves: list[tuple[int, str]]) -> pd.DataFrame:
    """Return the ``(Adjusted)`` region series for ``ba``, keyed by UTC time.

    Read straight from the BALANCE files with no transform beyond the numeric
    cast and the float32 narrowing the sibling schema uses for region columns.
    """
    frames = []
    for year, half in halves:
        path = BALANCE_DIR / f"EIA930_BALANCE_{year}_{half}.parquet"
        df = pd.read_parquet(
            path,
            columns=["Balancing Authority", "UTC Time at End of Hour", *ADJUSTED_MAP],
        )
        frames.append(df[df["Balancing Authority"] == ba])
    raw = pd.concat(frames, ignore_index=True)
    out = pd.DataFrame(
        {
            "UTC time": pd.to_datetime(raw["UTC Time at End of Hour"]).astype(
                "datetime64[us]"
            )
        }
    )
    for src, name in ADJUSTED_MAP.items():
        out[name] = pd.to_numeric(raw[src], errors="coerce").astype("float32")
    return out.drop_duplicates(subset="UTC time").reset_index(drop=True)


def build_ba(ba: str, years: tuple[int, ...]) -> pd.DataFrame:
    """Build one BA's wide hourly frame across both EIA-930 taxonomy eras."""
    halves = available_halves(years)
    if not halves:
        raise SystemExit(f"no BALANCE files on disk for years {years}")
    legacy = [(y, h) for y, h in halves if not _is_new_taxonomy(y, h)]
    new = [(y, h) for y, h in halves if _is_new_taxonomy(y, h)]

    parts = []
    for era in (legacy, new):
        if not era:
            continue
        # ``build_new_rows`` takes (years, halves) as independent products, so
        # each era is passed one (year, half) pair at a time — the only call
        # shape that cannot mix taxonomies.
        for year, half in era:
            parts.append(build_new_rows(ba, list(SIBLING_FUEL_COLS), (year,), (half,)))
    wide = pd.concat(parts, ignore_index=True)
    wide = wide.drop_duplicates(subset="UTC time", keep="first")
    wide = wide.sort_values("UTC time").reset_index(drop=True)
    wide = wide[list(SIBLING_COLS)]

    adj = _adjusted_frame(ba, halves)
    out = wide.merge(adj, on="UTC time", how="left", validate="one_to_one")
    out = out[list(SIBLING_COLS) + list(ADJUSTED_MAP.values())]

    # A fuel code absent from the LEGACY taxonomy but present in the NEW one
    # (``NG: BAT``) arrives as ``pd.NA`` for the legacy half, which makes the
    # concatenated column object-dtype.  The siblings store every region and
    # ``NG:`` column as float32, so narrow explicitly — NaN, never a
    # fabricated 0 (rule 14 ``[R-ACCURATE]``).
    for col in out.columns:
        if col not in ("UTC time", "Local date", "Local time", "Hour"):
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("float32")
    return out.reset_index(drop=True)


def verify_schema(out_path: Path, reference: str = "SWPP") -> None:
    """Assert the written extract matches the sibling schema on its 17 columns.

    The three appended ``(Adjusted)`` columns are this lane's documented
    addition (see the module docstring) and are checked for presence and
    dtype, not against the sibling, which has none.
    """
    ref = pq.read_schema(OUT_DIR / f"{reference} hourly.parquet")
    got = pq.read_schema(out_path)
    ref_cols = list(zip(ref.names, (str(t) for t in ref.types)))
    got_cols = list(zip(got.names, (str(t) for t in got.types)))
    if got_cols[: len(ref_cols)] != ref_cols:
        raise AssertionError(
            f"{out_path.name}: schema mismatch vs {reference} hourly.parquet:\n"
            f"  ref: {ref_cols}\n  new: {got_cols[: len(ref_cols)]}"
        )
    extra = got_cols[len(ref_cols) :]
    want_extra = [(n, "float") for n in ADJUSTED_MAP.values()]
    if extra != want_extra:
        raise AssertionError(
            f"{out_path.name}: appended columns {extra} != {want_extra}"
        )


def reconcile(ba: str, frame: pd.DataFrame, years: tuple[int, ...]) -> list[dict]:
    """Reconcile the derived frame against its BALANCE source, to the MWh.

    The derive selects, renames and narrows to the sibling schema's float32 —
    it never transforms a value — so the gate is **element-wise exact
    identity**: for every hour, the derived cell must equal ``float32`` of the
    source cell, or both must be NaN.  ``mismatched_hours`` is that count and
    must be 0.

    ``residual_mwh`` compares the two annual sums taken over the SAME float32
    values (both accumulated in float64), so it is exactly 0.0 whenever the
    element-wise check passes.  It is reported separately from
    ``src_demand_mwh_f64``, the source's own float64 annual energy: the two
    differ by ~1 part in 3e7 purely because the sibling schema stores region
    columns as float32, which is a property of the committed schema this lane
    must match, not a defect in the derive.
    """
    src_frames = []
    for year, half in available_halves(years):
        path = BALANCE_DIR / f"EIA930_BALANCE_{year}_{half}.parquet"
        df = pd.read_parquet(
            path,
            columns=[
                "Balancing Authority",
                "UTC Time at End of Hour",
                "Data Date",
                "Demand (MW)",
                "Demand (MW) (Adjusted)",
            ],
        )
        src_frames.append(df[df["Balancing Authority"] == ba])
    src = pd.concat(src_frames, ignore_index=True)
    src["UTC time"] = pd.to_datetime(src["UTC Time at End of Hour"]).astype(
        "datetime64[us]"
    )
    src = src.drop_duplicates(subset="UTC time").reset_index(drop=True)
    src["yr"] = pd.to_datetime(src["Data Date"]).dt.year

    merged = frame.merge(
        src[["UTC time", "yr", "Demand (MW)", "Demand (MW) (Adjusted)"]],
        on="UTC time",
        how="outer",
        indicator=True,
        validate="one_to_one",
    )

    rows = []
    for year in years:
        m = merged[merged["yr"] == year]
        pairs = (
            ("Demand", "Demand (MW)"),
            ("Demand (Adjusted)", "Demand (MW) (Adjusted)"),
        )
        mism = 0
        sums: dict[str, float] = {}
        for got_col, want_col in pairs:
            got = m[got_col].to_numpy(dtype="float64")
            want = m[want_col].astype("float32").to_numpy(dtype="float64")
            both_nan = pd.isna(got) & pd.isna(want)
            mism += int((~(both_nan | (got == want))).sum())
            sums[got_col] = float(pd.Series(got).sum())
            sums[want_col] = float(pd.Series(want).sum())
        rows.append(
            {
                "ba": ba,
                "year": year,
                "hours": int((m["_merge"] != "right_only").sum()),
                "src_hours": int((m["_merge"] != "left_only").sum()),
                "unmatched_hours": int((m["_merge"] != "both").sum()),
                "mismatched_hours": mism,
                "demand_mwh": sums["Demand"],
                "src_demand_mwh": sums["Demand (MW)"],
                "residual_mwh": sums["Demand"] - sums["Demand (MW)"],
                "src_demand_mwh_f64": float(
                    pd.to_numeric(m["Demand (MW)"], errors="coerce").sum()
                ),
                "adj_demand_mwh": sums["Demand (Adjusted)"],
                "adj_residual_mwh": (
                    sums["Demand (Adjusted)"] - sums["Demand (MW) (Adjusted)"]
                ),
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", action="append", dest="bas", metavar="BA")
    ap.add_argument(
        "--all-nwpp", action="store_true", help=f"all 17 NWPP BAs: {' '.join(NWPP_BAS)}"
    )
    ap.add_argument("--year", action="append", type=int, dest="years", default=None)
    ap.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing extract (data/raw is otherwise immutable)",
    )
    ap.add_argument(
        "--reconcile-csv",
        type=Path,
        default=None,
        help="write the per-BA per-year reconciliation table here",
    )
    args = ap.parse_args()

    bas = list(NWPP_BAS) if args.all_nwpp else (args.bas or [])
    if not bas:
        ap.error("pass --ba <BA> (repeatable) or --all-nwpp")
    years = tuple(args.years) if args.years else (2023, 2024, 2025)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: list[dict] = []
    for ba in bas:
        out_path = OUT_DIR / f"{ba} hourly.parquet"
        if out_path.exists() and not args.force:
            print(f"  {out_path.name} exists; skipping (--force to rebuild)")
            continue
        frame = build_ba(ba, years)
        rows = reconcile(ba, frame, years)
        bad = [
            r
            for r in rows
            if r["mismatched_hours"]
            or r["unmatched_hours"]
            or r["residual_mwh"] != 0.0
            or r["adj_residual_mwh"] != 0.0
        ]
        if bad:
            raise SystemExit(
                f"{ba}: reconciliation residual is NOT zero — STOP, do not "
                f"adjust: {bad}"
            )
        frame.to_parquet(out_path, index=False)
        verify_schema(out_path)
        report.extend(rows)
        span = f"{frame['Local date'].min().date()}..{frame['Local date'].max().date()}"
        print(
            f"  OK {out_path.name}: {len(frame):,} rows ({span}), "
            + ", ".join(
                f"{r['year']} {r['demand_mwh'] / 1e6:,.3f} TWh / {r['hours']} h "
                f"(resid {r['residual_mwh']:+.6f})"
                for r in rows
            )
        )
    if args.reconcile_csv and report:
        args.reconcile_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(report).to_csv(args.reconcile_csv, index=False)
        print(f"wrote {args.reconcile_csv}")


if __name__ == "__main__":
    sys.exit(main())
