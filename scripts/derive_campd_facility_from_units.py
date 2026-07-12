"""Derive a CAMPD facility-level hourly parquet from the unit-level extract.

The ``data/raw/campd-facility-level/{ST}_{YEAR}.parquet`` files are the
facility aggregation of the CAMPD unit-level hourly emissions extracts. For
years where EPA's facility-level bulk file was fetched directly (2023-2025)
the two lineages are redundant: the unit-level extract sums to the facility
series exactly (the F6 TX-2023 parity audit in
``docs/out-of-sample-results-2026-07.md`` §1.1, re-proven per state/year by
``--prove`` below). For intaken holdout years where only the unit-level
extract was landed (NY/NJ 2022 — CLAUDE.md rule 22 intake), this script
derives the facility file from the committed unit file instead of re-fetching,
keeping a single physical source of truth.

Recipe (proven bit-for-bit against the committed 2023-2025 NY/NJ files by
``--prove``, modulo row order and float summation-order cleanup):

1. group the unit rows by ``(stateCode, facilityName, facilityId, date,
   hour)`` and sum ``grossLoad/steamLoad/so2Mass/co2Mass/noxMass/heatInput``
   NaN-preserving (``min_count=1`` — an hour where every unit reports NaN
   stays NaN, not 0);
2. drop rows where all six measures are NaN (the committed facility files
   carry only reported hours);
3. round each measure at 3 decimals — the CAMPD source's native decimal
   precision, so the rounded float sum IS the decimal sum EPA's own facility
   file carries (removes ~1e-13 float summation-order noise, nothing else);
4. join ``persefoniOrganizationName`` per ``facilityId`` from a committed
   sibling-year facility file (a facility-static registry attribute absent
   from the unit-level schema; facilities not present in the sibling year
   stay NaN, and are logged).

Rows are written sorted by (numeric facilityId, date, hour) — the EPA bulk
ordering convention; consumers (``market_sim.data.campd``) are row-order
agnostic.

Usage::

    # prove the recipe against every committed in-sample year first
    python scripts/derive_campd_facility_from_units.py --states NY NJ --prove

    # then derive the holdout year
    python scripts/derive_campd_facility_from_units.py --states NY NJ \
        --year 2022 --persefoni-sibling 2023
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

UNIT_DIR = paths.RAW_DATA_DIR / "campd-unit-level"
FACILITY_DIR = paths.RAW_DATA_DIR / "campd-facility-level"

KEYS = ["stateCode", "facilityName", "facilityId", "date", "hour"]
MEASURES = ["grossLoad", "steamLoad", "so2Mass", "co2Mass", "noxMass", "heatInput"]

#: Known EPA revision-vintage drift between the two committed lineages, found
#: by the 2026-07-12 NYISO intake proof run: Edgewood Energy (facilityId
#: 55786) resubmitted 53 Jan-2025 operating hours (so2/co2/nox mass and
#: heatInput all move, e.g. so2Mass uniformly x~0.938) between the unit-level
#: fetch and the facility-level fetch, so those cells cannot agree under ANY
#: recipe. Itemized here so the prove gate stays byte-strict everywhere else;
#: flagged to the NYISO calibration owner in
#: docs/holdout-data-equivalency-register-2026-07.md (in-sample data, not this
#: lane's to change).
KNOWN_VINTAGE_DRIFT: dict[tuple[str, int, str], dict] = {
    ("NY", 2025, v): {
        "facilityId": "55786",
        "max_cells": 53,
        "note": "Edgewood Energy Jan-2025 EPA resubmission between fetches",
    }
    for v in ("so2Mass", "co2Mass", "noxMass", "heatInput")
}
#: CAMPD publishes the mass/heat measures as <=3-decimal text; rounding the
#: float sum at this precision recovers the exact decimal sum.
SOURCE_DECIMALS = 3
PROVE_YEARS = (2023, 2024, 2025)


def derive(unit: pd.DataFrame, persefoni_map: dict[str, str]) -> pd.DataFrame:
    """Facility-level frame from a unit-level extract (recipe steps 1-4)."""
    g = unit.groupby(KEYS, as_index=False, sort=False)[MEASURES].sum(min_count=1)
    g = g[~g[MEASURES].isna().all(axis=1)].copy()
    g[MEASURES] = g[MEASURES].round(SOURCE_DECIMALS)
    g["persefoniOrganizationName"] = g["facilityId"].map(persefoni_map)
    g["_fid"] = pd.to_numeric(g["facilityId"], errors="coerce")
    g = g.sort_values(["_fid", "date", "hour"], kind="stable").drop(columns="_fid")
    return g.reset_index(drop=True)


def _persefoni_map(state: str, sibling_year: int) -> dict[str, str]:
    """facilityId -> persefoniOrganizationName from a committed sibling file."""
    sib = pd.read_parquet(FACILITY_DIR / f"{state}_{sibling_year}.parquet")
    return (
        sib.dropna(subset=["persefoniOrganizationName"])
        .drop_duplicates("facilityId")
        .set_index("facilityId")["persefoniOrganizationName"]
        .to_dict()
    )


def prove(state: str, year: int) -> bool:
    """Recipe check: derived-from-units == committed facility file for
    ``state``/``year`` on every key and measure cell (row order free)."""
    unit = pd.read_parquet(UNIT_DIR / f"{state}_{year}.parquet")
    committed = pd.read_parquet(FACILITY_DIR / f"{state}_{year}.parquet")
    got = derive(unit, _persefoni_map(state, year))
    a = got.sort_values(KEYS, kind="stable").reset_index(drop=True)
    b = committed.sort_values(KEYS, kind="stable").reset_index(drop=True)
    if len(a) != len(b):
        print(f"  {state} {year}: FAIL row count {len(a)} vs committed {len(b)}")
        return False
    ok = bool((a[KEYS].astype(str).values == b[KEYS].astype(str).values).all())
    if not ok:
        print(f"  {state} {year}: FAIL key mismatch")
        return False
    exceptions: list[str] = []
    for v in MEASURES:
        x, y = a[v].to_numpy(float), b[v].to_numpy(float)
        mism = ~((np.isnan(x) & np.isnan(y)) | (x == y))
        if mism.any():
            drift = KNOWN_VINTAGE_DRIFT.get((state, year, v))
            only_drift_facility = bool(
                drift
                and (a.loc[mism, "facilityId"] == drift["facilityId"]).all()
                and int(mism.sum()) <= drift["max_cells"]
            )
            if only_drift_facility:
                exceptions.append(
                    f"{v}: {int(mism.sum())} cells under known vintage drift "
                    f"({drift['note']})"
                )
                continue
            print(f"  {state} {year}: FAIL {v} ({int(mism.sum())} cells differ)")
            return False
    pa = a["persefoniOrganizationName"].fillna("~")
    pb = b["persefoniOrganizationName"].fillna("~")
    if not bool((pa == pb).all()):
        print(f"  {state} {year}: FAIL persefoniOrganizationName mismatch")
        return False
    tail = " — EXCEPT " + "; ".join(exceptions) if exceptions else ", all cells exact"
    print(
        f"  {state} {year}: recipe reproduces the committed file "
        f"({len(a):,} rows{tail})"
    )
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--states", nargs="+", required=True, help="state codes, e.g. NY NJ"
    )
    ap.add_argument("--year", type=int, help="year to derive (omit with --prove)")
    ap.add_argument(
        "--persefoni-sibling",
        type=int,
        default=2023,
        help="committed facility year supplying the persefoni registry join",
    )
    ap.add_argument(
        "--prove",
        action="store_true",
        help="verify the recipe against every committed in-sample year and exit",
    )
    args = ap.parse_args()

    if args.prove:
        results = [prove(st, y) for st in args.states for y in PROVE_YEARS]
        if not all(results):
            sys.exit("recipe does NOT reproduce a committed file — do not derive")
        print("recipe proven on every committed state-year")
        return

    if args.year is None:
        ap.error("--year is required unless --prove")
    for st in args.states:
        out = FACILITY_DIR / f"{st}_{args.year}.parquet"
        unit = pd.read_parquet(UNIT_DIR / f"{st}_{args.year}.parquet")
        pmap = _persefoni_map(st, args.persefoni_sibling)
        got = derive(unit, pmap)
        unmapped = sorted(
            got.loc[got["persefoniOrganizationName"].isna(), "facilityId"].unique()
        )
        mapped = sorted(
            got.loc[got["persefoniOrganizationName"].notna(), "facilityId"].unique()
        )
        print(
            f"  {st} {args.year}: persefoni joined for {len(mapped)} facilities "
            f"(registry attribute is sparse in every committed year)"
        )
        if unmapped:
            print(
                f"  {st} {args.year}: facilityIds absent from the "
                f"{args.persefoni_sibling} persefoni registry (left NaN): "
                f"{unmapped}"
            )
        # Write on the committed sibling's arrow schema (plain string columns,
        # not pandas-3 large_string) so the holdout file byte-matches the
        # in-sample files' physical layout.
        import pyarrow as pa
        import pyarrow.parquet as pq

        sibling_schema = pq.read_schema(
            FACILITY_DIR / f"{st}_{args.persefoni_sibling}.parquet"
        )
        fields = [sibling_schema.field(n) for n in sibling_schema.names]
        table = pa.Table.from_pandas(got, preserve_index=False).select(
            sibling_schema.names
        )
        table = table.cast(pa.schema(fields))
        pq.write_table(table, out)
        print(
            f"wrote {out} ({len(got):,} rows, {got['facilityId'].nunique()} facilities)"
        )


if __name__ == "__main__":
    main()
