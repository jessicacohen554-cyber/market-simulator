"""Fold raw NYISO OASIS ancillary-services price zips into per-year CSVs.

Companion to the NYISO load processor (:mod:`scripts.process_nyiso_zonal_load`).
The raw downloads under ``data/raw/NYISO-AS/raw/`` are monthly zips of
*daily* CSVs — real-time 5-minute (``<YYYYMM01>rtasp_csv.zip``) and day-ahead
hourly (``<YYYYMM01>damasp_csv.zip``) — each row carrying a zone's reserve and
regulation clearing prices:

    Time Stamp, Time Zone, Name, PTID,
    10 Min Spinning Reserve ($/MWHr),
    10 Min Non-Synchronous Reserve ($/MWHr),
    30 Min Operating Reserve ($/MWHr),
    NYCA Regulation Capacity ($/MWHr)
    [, NYCA Regulation Movement ($/MW)  -- real-time only]

These are the empirical realization of the NYISO Reserve Constraint Penalty
Factors: the per-zone reserve clearing prices that flow into the LBMP during
scarcity (see ``docs/nyiso-rcpf-overlay.md``). The prices are zonal, so the
locational structure (downstate East/SENY/NYC/LI reserves clearing far above
upstate) is preserved — the validation target for the RCPF overlay and the
ground truth for the locational reserve products.

This aggregates each zone's prices to the hour-beginning mean and writes one
compact CSV per market and year:

* ``data/raw/NYISO-AS/NYISO_as_rt_{year}.csv`` (real-time)
* ``data/raw/NYISO-AS/NYISO_as_da_{year}.csv`` (day-ahead)

columns ``Time Stamp`` (Eastern wall-clock, hour-beginning), ``Name`` (NYISO
zone), ``spin_10``, ``nonsync_10``, ``op_30``, ``reg_cap`` (all $/MWh).

Duplicate downloads (``... (1).zip``) are skipped in favour of the canonical
file for that date. Run:
``python scripts/process_nyiso_as.py [--years 2023 2024 2025] [--market rt da]``
"""

from __future__ import annotations

import argparse
import io
import re
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
AS_DIR = REPO / "data" / "raw" / "NYISO-AS"
RAW_DIR = AS_DIR / "raw"
# RAW_DIR (gitignored) is normally populated directly by
# scripts/fetch_nyiso_as.py, one monthly rtasp/damasp zip per file — that is
# the primary, working path. OUTER_ZIP is a legacy fallback for a
# hand-supplied zip-of-zips bundle (never observed to exist in this repo);
# kept only so a manually-assembled bundle would still work if one ever
# shows up.
OUTER_ZIP = AS_DIR / "NYISO-AS-Data.zip"


def _ensure_raw() -> None:
    """Populate RAW_DIR from the outer zip, if needed and available.

    No-op when RAW_DIR is already populated (the expected case:
    ``scripts/fetch_nyiso_as.py`` writes the monthly zips straight there) or
    when neither RAW_DIR nor OUTER_ZIP has anything to offer (the caller's
    ``process()`` then reports "no zips" per market/year, same as before).
    """
    if RAW_DIR.exists() and any(RAW_DIR.glob("*asp_csv*.zip")):
        return
    if not OUTER_ZIP.exists():
        return
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"extracting {OUTER_ZIP.name} -> {RAW_DIR}")
    with zipfile.ZipFile(OUTER_ZIP) as zf:
        zf.extractall(RAW_DIR)


NYISO_ZONES = frozenset(
    {
        "WEST",
        "GENESE",
        "CENTRL",
        "NORTH",
        "MHK VL",
        "CAPITL",
        "HUD VL",
        "MILLWD",
        "DUNWOD",
        "N.Y.C.",
        "LONGIL",
    }
)

# Source column (case-insensitive substring) -> tidy output name.
_PRICE_COLS = {
    "10 min spinning reserve": "spin_10",
    "10 min non-synchronous reserve": "nonsync_10",
    "30 min operating reserve": "op_30",
    "nyca regulation capacity": "reg_cap",
}

_DATE_RE = re.compile(r"^(\d{8})")

# CLI market token -> NYISO MIS filename infix (real-time "rtasp",
# day-ahead-market "damasp").
_MARKET_TOKEN = {"rt": "rt", "da": "dam"}


def _canonical_zips(market: str, year: int) -> list[Path]:
    """Monthly zips for a market/year, one per date (drop ``(1)`` dupes)."""
    token = _MARKET_TOKEN[market]
    by_date: dict[str, Path] = {}
    for p in sorted(RAW_DIR.glob(f"{year}*{token}asp_csv*.zip")):
        m = _DATE_RE.match(p.name)
        if not m:
            continue
        # Prefer the name without a " (1)" duplicate marker.
        if m.group(1) not in by_date or "(1)" not in p.name:
            by_date.setdefault(m.group(1), p)
            if "(1)" not in p.name:
                by_date[m.group(1)] = p
    return [by_date[k] for k in sorted(by_date)]


def _read_zip(path: Path) -> pd.DataFrame:
    """Read every daily ASP CSV inside one monthly zip into one frame."""
    frames = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with zf.open(name) as fh:
                frames.append(pd.read_csv(io.BytesIO(fh.read())))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def process(market: str, year: int) -> Path | None:
    """Aggregate one market/year to the hour-beginning per-zone price CSV."""
    zips = _canonical_zips(market, year)
    if not zips:
        print(f"  {market} {year}: no zips under {RAW_DIR} — skipping")
        return None

    df = pd.concat([_read_zip(z) for z in zips], ignore_index=True)
    df.columns = [str(c).strip() for c in df.columns]
    name_col = next(c for c in df.columns if c.lower() == "name")
    ts_col = next(c for c in df.columns if c.lower().startswith("time stamp"))
    # Resolve each tidy price column from its source header.
    rename: dict[str, str] = {}
    for src in df.columns:
        key = src.lower()
        for needle, tidy in _PRICE_COLS.items():
            if needle in key:
                rename[src] = tidy
    df = df.rename(columns=rename)

    df[name_col] = df[name_col].astype(str).str.strip()
    df = df[df[name_col].isin(NYISO_ZONES)].copy()
    ts = pd.to_datetime(df[ts_col], errors="coerce")
    df = df[ts.notna()].copy()
    df["Time Stamp"] = ts[ts.notna()].dt.floor("h")
    out_cols = [v for v in _PRICE_COLS.values() if v in df.columns]
    for c in out_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    hourly = (
        df.groupby(["Time Stamp", name_col], observed=True)[out_cols]
        .mean()
        .reset_index()
        .rename(columns={name_col: "Name"})
        .sort_values(["Time Stamp", "Name"])
    )
    out_path = AS_DIR / f"NYISO_as_{market}_{year}.csv"
    hourly.to_csv(out_path, index=False)

    n_hours = hourly["Time Stamp"].nunique()
    # NYCA-max 30-min reserve price (the scarcity signal) across zones/hour.
    op30_by_hour = hourly.groupby("Time Stamp")["op_30"].max()
    print(
        f"  {market} {year}: {len(zips)} zips -> {len(hourly):,} rows "
        f"({hourly['Name'].nunique()} zones x {n_hours:,} h); "
        f"30-min reserve $>0 in {int((op30_by_hour > 0).sum()):,} h, "
        f"$>50 in {int((op30_by_hour > 50).sum()):,} h, "
        f"max ${op30_by_hour.max():,.0f} -> {out_path.name}"
    )
    return out_path


_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = list(
    __import__("numpy").cumsum([0] + [d * 24 for d in _DAYS_IN_MONTH])
)

# NYISO zones whose stacked reserve price tracks each model series: WEST
# carries only the NYCA-wide requirement (the system-wide component every
# zone shares); N.Y.C. carries the full downstate cascade (NYCA + East +
# SENY + NYC locational), the highest reserve price in the state.
_REF_ZONES = {"nyca_reserve_adder": "WEST", "nyc_reserve_adder": "N.Y.C."}

# Representative NYISO settlement zone for each MODEL zone's stacked RT reserve
# price (the locational cascade tier the model zone carries): A-E share the
# NYCA tier, F adds East, G-K add SENY, J adds NYC. These columns let the RCPF
# overlay validate every model zone's adder against measured data without
# re-reading the per-zone CSV. Keyed ``reserve_<model_zone>``; the legacy
# nyca/nyc aliases above are kept for backward compatibility.
_MODEL_ZONE_REF = {
    "reserve_Upstate_West": "WEST",
    "reserve_Capital_Hudson": "CAPITL",
    "reserve_Lower_Hudson": "DUNWOD",
    "reserve_NYC": "N.Y.C.",
    "reserve_Long_Island": "LONGIL",
}

CAL_DIR = REPO / "data" / "raw" / "_validation-source"


def build_reference(years: list[int]) -> Path | None:
    """Write the compact measured RT reserve-adder calibration reference.

    ``data/raw/_validation-source/actual_as_reserve_NYISO.parquet`` — per (year, hour)
    on the model's non-leap 8760 clock. Two legacy series:
    ``nyca_reserve_adder`` (the WEST stacked RT reserve price, the system-wide
    NYCA component) and ``nyc_reserve_adder`` (the N.Y.C. stacked RT reserve
    price, the full downstate cascade); plus one ``reserve_<model_zone>``
    column per model zone (the stacked RT reserve price of the settlement zone
    whose cascade tier it carries, ``_MODEL_ZONE_REF``), so the RCPF overlay
    validates every model zone's adder against measured data — the measured
    analogue of ``actual_lmp_hourly_NYISO.parquet``.
    """
    import numpy as np

    columns = {**_REF_ZONES, **_MODEL_ZONE_REF}
    frames = []
    for year in years:
        path = AS_DIR / f"NYISO_as_rt_{year}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df["stack"] = df[["spin_10", "nonsync_10", "op_30"]].sum(axis=1)
        ts = pd.to_datetime(df["Time Stamp"])
        keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
        df, ts = df[keep], ts[keep]
        hoy = (
            np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
            + (ts.dt.day.to_numpy() - 1) * 24
            + ts.dt.hour.to_numpy()
        )
        df = df.assign(hour=hoy)
        out = {"year": np.int16(year), "hour": np.arange(8760, dtype=np.int32)}
        # One groupby per settlement zone reused across its column aliases.
        for zone in set(columns.values()):
            s = (
                df[df["Name"] == zone]
                .groupby("hour")["stack"]
                .max()
                .reindex(range(8760))
                .to_numpy(dtype=np.float32)
            )
            for col, z in columns.items():
                if z == zone:
                    out[col] = s
        frames.append(pd.DataFrame(out))
    if not frames:
        return None
    ref = pd.concat(frames, ignore_index=True)
    out_path = CAL_DIR / "actual_as_reserve_NYISO.parquet"
    ref.to_parquet(out_path, index=False)
    print(
        f"  reference: {out_path.name} — per-(year,hour) stacked RT reserve "
        f"for {len(_MODEL_ZONE_REF)} model zones + NYCA/NYC aliases:"
    )
    for col in ("nyca_reserve_adder", *_MODEL_ZONE_REF):
        s = ref[col]
        print(
            f"    {col:28s} >$0 in {int((s > 0).sum()):,} h, "
            f"mean ${np.nanmean(s):.2f}, max ${np.nanmax(s):,.0f}"
        )
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--market", nargs="+", default=["rt", "da"], choices=["rt", "da"])
    ap.add_argument(
        "--no-reference",
        action="store_true",
        help="skip the calibration-reference parquet",
    )
    args = ap.parse_args()
    _ensure_raw()
    print(f"processing NYISO ancillary-service prices from {RAW_DIR}")
    for market in args.market:
        for year in args.years:
            process(market, year)
    if not args.no_reference and "rt" in args.market:
        build_reference(args.years)


if __name__ == "__main__":
    main()
