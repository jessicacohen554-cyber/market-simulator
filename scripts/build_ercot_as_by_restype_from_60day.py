"""Build ERCOT hourly up-AS awarded MW by resource class from 60-Day Disclosure.

Reconstructs ``ercot_<year>_as_by_restype_hourly.parquet`` — the per-resource
60-Day DAM AS awards aggregated by ERCOT Resource Type — directly from the
``60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet`` files in
``data/raw/ercot/``. Each per-resource row carries the cleared DAM awards
(``RegUp Awarded``, ``RRSPFR/FFR/UFR Awarded``, ``ECRSSD Awarded`` once ECRS
went live 2023-06-10, ``NonSpin Awarded``); we sum the upward products per
resource, map the ERCOT ``Resource Type`` code to the model's plant class, and
total by class on the fixed non-leap 8760-hour clock.

This is **measured** data — it replaces the intensity-transfer ESTIMATE in
``build_ercot_storage_as_2023_estimate.py`` for 2023. Crucially, the 60-Day
files are named by *disclosure* date (~60 days after delivery), so a delivery
year is spread across several files and the year's tail spills into the next
year's files; we therefore load ALL files and filter on the actual
``Delivery Date``, not the filename.

Known repo gap: the Oct-2023 (2023-10-02 .. 2023-11-01) Gen Resource Data
disclosure file is not present, so those hours zero-fill (the deliberate
"don't fabricate reserve across a multi-month hole" convention in
``_to_model_clock``). Drop that disclosure file in to close it. 2023 storage
otherwise covers 335/365 delivery-days.

Coverage / validation: rebuilding 2024 from these files reproduces the existing
committed series at corr 0.88-0.93 with matching monthly means in every
well-covered month; the only large divergences are months the *old* committed
file left short because they had not yet been disclosed when it was built (e.g.
Dec-2024), which this rebuild fills.

Scope of the columns written:
* ``storage`` (PWRSTR) is MEASURED from the Gen Resource Data awards — the one
  column the keeper consumes (the storage-AS reserve credit).
* The thermal classes (``gas_cc``/``gas_ct``/``gas_st``/``coal``) are written
  only under ``--with-thermal``; by default they are zero. The measured thermal
  awards (~3.3 GW) are physically reasonable but run ~4-5x the committed
  2024/2025 ``thermal_total`` convention, which is not reproducible from the
  repo, so they are withheld until reconciled (the keeper runs
  ``as_reserve_withholding`` off, so it does not read them).
* ``load`` is left zero: the model reads it from nowhere (the load-resource
  RRS-UFR credit reads ``ercot_<year>_as_up_mw.parquet`` instead), and the
  60-Day *Load* Resource **awards** file (``60d_DAM_Load_Resource_Data``) is
  not in the repo — only the offers file is. Build it here if/when that lands.
* ``thermal_total`` = gas_cc + gas_ct + gas_st + coal.

Run:
    python scripts/build_ercot_as_by_restype_from_60day.py            # 2023 (storage)
    python scripts/build_ercot_as_by_restype_from_60day.py --year 2023
    python scripts/build_ercot_as_by_restype_from_60day.py --validate # vs committed
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Reuse the canonical clock mapping (non-leap 8760 on fixed CST, the sources'
# Central-Prevailing sequential-HE labels converted CPT->CST before placement)
# so this series sits on the same clock as the rest of the fleet inputs.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_ercot_as_withholding import (  # noqa: E402
    HOURS_PER_YEAR,
    _to_model_clock,
    prevailing_he_to_cst,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = REPO_ROOT / "data" / "raw" / "ercot"
OUT_DIR = REPO_ROOT / "data" / "raw" / "ercot-AS"

# Upward AS award columns (Reg-Down excluded — it withholds no upward energy).
# ECRS columns only exist from the 2023-06-10 launch; absent ones are skipped.
_UP_AWARD_COLS: tuple[str, ...] = (
    "RegUp Awarded",
    "RRSPFR Awarded",
    "RRSFFR Awarded",
    "RRSUFR Awarded",
    "ECRSSD Awarded",
    "NonSpin Awarded",
)

# ERCOT 60-Day DAM Resource Type code -> model plant class column. Wind/solar/
# hydro/nuclear/DSL carry negligible cleared up-AS and are not thermal-withheld,
# so they are intentionally unmapped (dropped from the thermal/storage totals).
_RESTYPE_TO_CLASS: dict[str, str] = {
    "CCGT90": "gas_cc",
    "CCLE90": "gas_cc",
    "SCGT90": "gas_ct",
    "SCLE90": "gas_ct",
    "GSREH": "gas_st",
    "GSSUP": "gas_st",
    "GSNONR": "gas_st",
    "CLLIG": "coal",
    "PWRSTR": "storage",
}
_CLASSES: tuple[str, ...] = ("gas_cc", "gas_ct", "gas_st", "coal", "storage", "load")


def _load_gen_awards() -> pd.DataFrame:
    """Load all Gen Resource Data rows with their summed upward-AS award MW."""
    files = sorted(glob.glob(str(GEN_DIR / "*Gen_Resource_Data_*.parquet")))
    if not files:
        raise SystemExit(f"no Gen Resource Data parquets under {GEN_DIR}")
    parts: list[pd.DataFrame] = []
    for f in files:
        avail = set(pq.ParquetFile(f).schema.names)
        up = [c for c in _UP_AWARD_COLS if c in avail]
        df = pd.read_parquet(
            f, columns=["Delivery Date", "Hour Ending", "Resource Type", *up]
        )
        df = df[df["Resource Type"].isin(_RESTYPE_TO_CLASS)].copy()
        df["mw"] = df[up].apply(pd.to_numeric, errors="coerce").fillna(0.0).sum(axis=1)
        df["cls"] = df["Resource Type"].map(_RESTYPE_TO_CLASS)
        parts.append(df[["Delivery Date", "Hour Ending", "cls", "mw"]])
    big = pd.concat(parts, ignore_index=True)
    big["dd"] = pd.to_datetime(big["Delivery Date"])
    big["he"] = big["Hour Ending"].astype(int)
    return big


def build_year(
    big: pd.DataFrame, year: int, with_thermal: bool = False
) -> pd.DataFrame | None:
    """Aggregate one delivery year to the (8760,) per-class clock.

    ``storage`` is always measured. The thermal classes are written only when
    ``with_thermal`` is set: the measured thermal awards here (~3.3 GW) are
    physically reasonable but run ~4-5x the committed 2024/2025 ``thermal_total``
    convention, which is not reproducible from the repo, so by default the
    thermal/load columns are left zero (matching the prior 2023 file and
    preserving model behaviour — the keeper runs ``as_reserve_withholding`` off).
    """
    sub = big[big["dd"].dt.year == year]
    if sub.empty:
        print(f"  {year}: no delivery rows — skipping.")
        return None
    days = sub["dd"].dt.normalize().nunique()
    # Prevailing sequential-HE labels (1-24; 25 on the fall-back day) -> CST.
    ts = prevailing_he_to_cst(sub["dd"], sub["he"])
    frame = pd.DataFrame({"hour": np.arange(HOURS_PER_YEAR, dtype="int64")})
    for cls in _CLASSES:
        measured = cls != "load" and (cls == "storage" or with_thermal)
        if not measured:  # load-resource awards not in repo; thermal opt-in only
            frame[cls] = 0.0
            continue
        rows = pd.DataFrame({"ts": ts, "mw": sub["mw"].where(sub["cls"] == cls, 0.0)})
        rows = rows.groupby("ts", as_index=False)["mw"].sum()
        frame[cls] = _to_model_clock(rows, year)
    frame["thermal_total"] = frame[["gas_cc", "gas_ct", "gas_st", "coal"]].sum(axis=1)
    gap = 365 - days
    note = f"  ({gap} delivery-days absent -> zero-filled)" if gap else ""
    print(
        f"  {year}: {days} delivery-days | storage mean {frame['storage'].mean():6.0f} "
        f"MW peak {frame['storage'].max():5.0f} | thermal mean "
        f"{frame['thermal_total'].mean():6.0f} MW{note}"
    )
    return frame


def _write(frame: pd.DataFrame, year: int) -> None:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata(
        {
            "source": "ERCOT 60-Day DAM Disclosure (NP3-966-ER), "
            "60d_DAM_Gen_Resource_Data; measured per-resource DAM awards.",
            "description": f"ERCOT {year} hourly UP-AS awarded MW by resource class "
            "(RegUp + RRSPFR/FFR/UFR + ECRSSD + online NonSpin), summed per "
            "resource then by ERCOT Resource Type. 'load' is 0 (load-resource "
            "awards file not in repo).",
            "units": "MW (hour-beginning)",
            "year": str(year),
            "clock": "Model 8760 non-leap ERCOT-local STANDARD time (CST, "
            "UTC-6); Feb29 dropped, the source's Central-Prevailing "
            "sequential-HE labels (HE 1-25 on the fall-back day) converted "
            "CPT->CST before placement",
        }
    )
    out = OUT_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
    pq.write_table(table, out)
    print(f"  wrote {out.relative_to(REPO_ROOT)}")


def surgical_storage_fix(big: pd.DataFrame, year: int) -> None:
    """Replace ONLY the ``storage`` column of a committed by-restype parquet.

    The committed 2024/2025 files were built from the 60-Day Gen **and Load**
    Resource Data; the Load awards file is not in the repo, so a full rebuild
    here would change the data vintage of columns this script cannot
    reproduce. The ``storage`` (PWRSTR) column — the one column the keeper
    consumes (the storage-AS reserve credit) — is measured entirely from the
    in-repo Gen Resource Data: rebuild it on the corrected CST clock
    (CPT->CST, the 2026-07-07 placement-defect fix) and leave every other
    column untouched. ``thermal_total`` is NOT recomputed (it is the
    committed Load+Gen build's convention, not this script's).
    """
    path = OUT_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
    if not path.exists():
        print(f"  {year}: no committed by-restype parquet — nothing to fix.")
        return
    frame = build_year(big, year, with_thermal=False)
    if frame is None:
        return
    existing = pq.read_table(path)
    meta = {
        (k.decode() if isinstance(k, bytes) else k): (
            v.decode() if isinstance(v, bytes) else v
        )
        for k, v in (existing.schema.metadata or {}).items()
    }
    out = existing.to_pandas()
    out["storage"] = frame["storage"].to_numpy(dtype=float)
    meta["storage_clock_fix"] = (
        "storage column rebuilt 2026-07-07 from the in-repo 60d Gen Resource "
        "Data PWRSTR awards with the Central-Prevailing sequential-HE labels "
        "converted CPT->CST before placement (the HSL-round placement-defect "
        "class, docs/handoffs/ercot-g22-demand-side-design-2026-07.md §7); "
        "all other columns are the original Gen+Load build (Load awards "
        "source not in repo) and keep its clock."
    )
    table = pa.Table.from_pandas(out, preserve_index=False)
    table = table.replace_schema_metadata(meta)
    pq.write_table(table, path)
    print(f"  wrote {path.relative_to(REPO_ROOT)} (storage column replaced)")


def validate(big: pd.DataFrame) -> None:
    """Compare a rebuild against the committed series, by month, for 2024/2025."""
    for year in (2024, 2025):
        frame = build_year(big, year, with_thermal=True)
        existp = OUT_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
        if frame is None or not existp.exists():
            continue
        ex = pd.read_parquet(existp)
        idx = pd.date_range(f"{year}-01-01", periods=HOURS_PER_YEAR, freq="h")
        for col in ("storage", "thermal_total"):
            if col not in ex.columns:
                continue
            a = pd.Series(frame[col].to_numpy(), index=idx)
            b = pd.Series(ex[col].to_numpy(), index=idx)
            mc = (
                pd.DataFrame({"a": a, "b": b})
                .groupby(idx.month)
                .apply(
                    lambda x: (
                        np.corrcoef(x.a, x.b)[0, 1]
                        if x.a.std() and x.b.std()
                        else np.nan
                    )
                )
            )
            print(
                f"  {year} {col:13s} monthly corr "
                f"min {mc.min():.2f} median {mc.median():.2f}  "
                f"mean ratio {a.mean() / b.mean():.3f}"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument(
        "--surgical-storage",
        action="store_true",
        help="replace ONLY the storage column of the committed parquet for "
        "--year with the clock-corrected Gen-Resource-Data rebuild, keeping "
        "the other (Load+Gen-sourced, not in-repo-reproducible) columns "
        "byte-identical — see surgical_storage_fix",
    )
    ap.add_argument(
        "--with-thermal",
        action="store_true",
        help="also write measured thermal classes (unreconciled vs committed "
        "convention — see build_year docstring); default writes storage only",
    )
    args = ap.parse_args()
    big = _load_gen_awards()
    print(
        f"loaded {len(big):,} gen-award rows, delivery "
        f"{big['dd'].min().date()} -> {big['dd'].max().date()}"
    )
    if args.validate:
        validate(big)
        return
    if args.surgical_storage:
        surgical_storage_fix(big, args.year or 2024)
        return
    years = [args.year] if args.year else [2023]
    for year in years:
        frame = build_year(big, year, with_thermal=args.with_thermal)
        if frame is not None:
            _write(frame, year)


if __name__ == "__main__":
    main()
