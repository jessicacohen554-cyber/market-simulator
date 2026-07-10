#!/usr/bin/env python3
"""Fetch EPA CAMPD bulk hourly unit-level emissions and land the per-state
``data/raw/campd-unit-level/<ST>_<YEAR>.parquet`` files.

Makes the hand-run recipe of ``docs/multi-iso/miso-data-audit.md`` (Item 1)
reproducible. Source is the CAM-API bulk-files service:

    GET https://api.epa.gov/easey/bulk-files/emissions/hourly/state/
        emissions-hourly-<YEAR>-<st>.csv        (completed years, per state)
    GET .../emissions/hourly/quarter/emissions-hourly-<YEAR>-q<Q>.csv
        (in-progress year: national quarterly files, filtered to --states)

``x-api-key: DEMO_KEY`` is accepted; pass a registered key via ``EPA_API_KEY``
if rate-limited. The human-readable bulk CSV columns are mapped to the EASEY
camelCase schema of the existing siblings (e.g. ``TX_2024.parquet``) and the
output arrow schema is verified equal to a sibling's before the file lands.
Raw data is immutable: existing ``<ST>_<YEAR>.parquet`` files are never
overwritten unless ``--force``.

Usage:
    # completed year, per-state bulk files:
    python scripts/fetch_campd_unit_level.py --year 2022 --states TX IL IN

    # in-progress year from the national quarterly file(s):
    python scripts/fetch_campd_unit_level.py --year 2026 --quarters 1 \
        --states TX IL IN

    # reuse already-downloaded CSVs instead of re-fetching:
    python scripts/fetch_campd_unit_level.py --year 2022 --states TX \
        --csv-dir /path/to/downloads
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "data" / "raw" / "campd-unit-level"
BULK_BASE = "https://api.epa.gov/easey/bulk-files"

# Holdout years (CLAUDE.md rule 22, amended 2026-07-06 per
# docs/handoffs/holdout-policy-memo-2026-07.md Option 2): SOLVE and SCORE stay
# fully quarantined until an ISO is declared calibration-complete, but DATA
# INTAKE for these years is allowed for any ISO, any time, under explicit,
# session-logged owner authorization — no calibration-complete marker
# required. Fetching still requires ``--holdout-intake <ISO>`` so an
# accidental/un-authorized holdout fetch doesn't slip through unnoticed.
QUARANTINED_YEARS: frozenset[int] = frozenset({2022, 2026})


def _enforce_quarantine(year: int, holdout_intake: str | None) -> None:
    """Refuse an un-authorized quarantined-year fetch (CLAUDE.md rule 22).

    Amended 2026-07-06 (Option 2, docs/handoffs/holdout-policy-memo-2026-07.md):
    data intake for a holdout year (2022, H1-2026) is permitted for any ISO,
    at any time, under explicit owner authorization — ``--holdout-intake
    <ISO>`` naming the target ISO is that authorization record. No
    ``calibration-complete`` marker is required for intake (that marker still
    gates *solve* and *score*, enforced elsewhere: ``run_calibration_full.py``'s
    ``enforce_holdout_year_gate`` and the CI ``quarantine-gates`` job). Raises
    if no ``--holdout-intake`` is passed, so an accidental holdout fetch is
    still blocked at the fetcher.
    """
    if year not in QUARANTINED_YEARS:
        return
    if not holdout_intake:
        raise SystemExit(
            f"refusing to fetch quarantined year {year}: CLAUDE.md rule 22 "
            "holds 2022 and H1-2026 solve/score under quarantine until the "
            "target ISO is calibration-complete, but data intake is allowed "
            "any time under explicit owner authorization (rule 22 amendment, "
            "docs/handoffs/holdout-policy-memo-2026-07.md Option 2). Pass "
            "--holdout-intake <ISO> to record that authorization for this run."
        )


# Bulk-CSV human-readable column -> EASEY camelCase parquet column, the exact
# 16-column schema of the existing siblings (docs/multi-iso/miso-data-audit.md
# Item 1 column map). Extra CSV columns (measure indicators, rates, controls,
# secondary fuel, stacks) are not part of the sibling schema and are dropped.
_COLUMN_MAP: dict[str, str] = {
    "State": "stateCode",
    "Facility Name": "facilityName",
    "Facility ID": "facilityId",
    "Unit ID": "unitId",
    "Date": "date",
    "Hour": "hour",
    "Operating Time": "opTime",
    "Gross Load (MW)": "grossLoad",
    "Steam Load (1000 lb/hr)": "steamLoad",
    "SO2 Mass (lbs)": "so2Mass",
    "CO2 Mass (short tons)": "co2Mass",
    "NOx Mass (lbs)": "noxMass",
    "Heat Input (mmBtu)": "heatInput",
    "Primary Fuel Type": "primaryFuelInfo",
    "Unit Type": "unitType",
    "Program Code": "programCodeInfo",
}

_STR_COLS = (
    "State",
    "Facility Name",
    "Facility ID",
    "Unit ID",
    "Primary Fuel Type",
    "Unit Type",
    "Program Code",
)
_FLOAT_COLS = (
    "Operating Time",
    "Gross Load (MW)",
    "Steam Load (1000 lb/hr)",
    "SO2 Mass (lbs)",
    "CO2 Mass (short tons)",
    "NOx Mass (lbs)",
    "Heat Input (mmBtu)",
)

_CHUNK_ROWS = 1_000_000  # chunked CSV read keeps peak memory ~1 GB


def _api_key() -> str:
    """EPA CAM-API key: ``EPA_API_KEY`` env var, else the public DEMO_KEY."""
    return os.environ.get("EPA_API_KEY", "DEMO_KEY")


def _download(s3_path: str, dest: Path) -> Path:
    """Download one bulk file (with the API key header) unless already cached."""
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  using cached {dest}")
        return dest
    url = f"{BULK_BASE}/{s3_path}"
    print(f"  GET {url}")
    req = urllib.request.Request(url, headers={"x-api-key": _api_key()})
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=600) as resp, tmp.open("wb") as fh:
        while True:
            block = resp.read(1 << 22)
            if not block:
                break
            fh.write(block)
    tmp.rename(dest)
    return dest


def _read_bulk_csv(path: Path, states: set[str] | None = None) -> pd.DataFrame:
    """Read a bulk hourly CSV into the 16-column sibling schema (chunked)."""
    dtype = {c: "object" for c in _STR_COLS}
    dtype.update({c: "float64" for c in _FLOAT_COLS})
    dtype["Hour"] = "int64"
    frames = []
    for chunk in pd.read_csv(
        path,
        usecols=list(_COLUMN_MAP),
        dtype=dtype,
        parse_dates=["Date"],
        chunksize=_CHUNK_ROWS,
    ):
        if states is not None:
            chunk = chunk[chunk["State"].isin(states)]
        frames.append(chunk)
    df = pd.concat(frames, ignore_index=True)
    df = df[list(_COLUMN_MAP)].rename(columns=_COLUMN_MAP)
    # Siblings store the ids as strings (facilityId is unquoted int in the CSV)
    # in plain arrow ``string`` columns and the date as ``timestamp[ns]``; force
    # object-backed str and ns so the arrow schema matches byte-for-byte.
    df["facilityId"] = df["facilityId"].astype(str).astype(object)
    df["unitId"] = df["unitId"].astype(str).astype(object)
    df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
    return df


def _verify_against_sibling(df: pd.DataFrame, out_path: Path, year: int) -> None:
    """Assert the frame matches a sibling's arrow schema and sane coverage."""
    siblings = sorted(p for p in OUT_DIR.glob("*_*.parquet") if p != out_path)
    if not siblings:
        raise FileNotFoundError(f"no sibling parquet in {OUT_DIR} to verify against")
    # Prefer the same state's newest sibling; fall back to any.
    state = out_path.stem.split("_")[0]
    same_state = [p for p in siblings if p.stem.startswith(f"{state}_")]
    ref = (same_state or siblings)[-1]

    ref_schema = pq.read_schema(ref)
    df.to_parquet(out_path, index=False)
    new_schema = pq.read_schema(out_path)
    ref_cols = list(zip(ref_schema.names, (str(t) for t in ref_schema.types)))
    new_cols = list(zip(new_schema.names, (str(t) for t in new_schema.types)))
    if ref_cols != new_cols:
        out_path.unlink()
        raise AssertionError(
            f"{out_path.name}: schema mismatch vs {ref.name}:\n"
            f"  ref: {ref_cols}\n  new: {new_cols}"
        )
    years = df["date"].dt.year.unique()
    if list(years) != [year]:
        out_path.unlink()
        raise AssertionError(f"{out_path.name}: unexpected years {sorted(years)}")
    ref_rows = pq.read_metadata(ref).num_rows
    print(
        f"  OK {out_path.name}: {len(df):,} rows "
        f"(sibling {ref.name} {ref_rows:,}), "
        f"{df['facilityId'].nunique()} facilities / "
        f"{df.groupby(['facilityId', 'unitId']).ngroups} units, "
        f"{df['date'].min().date()}..{df['date'].max().date()}, "
        f"schema == sibling"
    )


def land_states(
    year: int,
    states: list[str],
    csv_dir: Path,
    quarters: list[int] | None,
    force: bool,
) -> None:
    """Fetch + convert + verify + land ``<ST>_<year>.parquet`` for each state."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    todo = []
    for st in states:
        out = OUT_DIR / f"{st}_{year}.parquet"
        if out.exists() and not force:
            print(f"  {out.name} already exists; skipping (--force to rebuild)")
            continue
        todo.append(st)
    if not todo:
        return

    if quarters:
        # In-progress year: national quarterly file(s), filtered per state.
        parts = []
        for q in quarters:
            name = f"emissions-hourly-{year}-q{q}.csv"
            path = _download(f"emissions/hourly/quarter/{name}", csv_dir / name)
            parts.append(_read_bulk_csv(path, states=set(todo)))
        allq = pd.concat(parts, ignore_index=True)
        for st in todo:
            sub = allq[allq["stateCode"] == st].reset_index(drop=True)
            if sub.empty:
                print(f"  {st}_{year}: no rows in quarter file(s); NOT landed")
                continue
            _verify_against_sibling(sub, OUT_DIR / f"{st}_{year}.parquet", year)
    else:
        for st in todo:
            name = f"emissions-hourly-{year}-{st.lower()}.csv"
            path = _download(f"emissions/hourly/state/{name}", csv_dir / name)
            df = _read_bulk_csv(path)
            _verify_against_sibling(df, OUT_DIR / f"{st}_{year}.parquet", year)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--states", nargs="+", required=True, metavar="ST")
    ap.add_argument(
        "--quarters",
        nargs="+",
        type=int,
        default=None,
        help="use the national quarterly file(s) (in-progress year) instead "
        "of per-state files",
    )
    ap.add_argument(
        "--csv-dir",
        type=Path,
        default=Path("/tmp") / "campd-bulk",
        help="download/cache dir for the bulk CSVs (not committed)",
    )
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--holdout-intake",
        default=None,
        metavar="ISO",
        help="record explicit owner authorization to intake quarantined-year "
        "(2022/2026) data for this ISO (no calibration-complete marker "
        "required for intake; CLAUDE.md rule 22, amended 2026-07-06)",
    )
    args = ap.parse_args()

    _enforce_quarantine(args.year, args.holdout_intake)

    land_states(
        args.year,
        [s.upper() for s in args.states],
        args.csv_dir,
        args.quarters,
        args.force,
    )
    print("done.")


if __name__ == "__main__":
    sys.exit(main())
