"""Slim the ERCOT 60-Day disclosure raw parquets to consumer-needed columns.

Owner-ordered storage optimization (ERCOT-96 session, 2026-07-22): the raw
DAM/SCED disclosure parquets carry every published column at SNAPPY
compression, but the repo's consumers read a fixed subset. This script
rewrites each file IN PLACE (same filename, so every glob/consumer keeps
working) with (a) only the union of columns any consumer reads and (b)
zstd-15 + dictionary encoding. Values are untouched — this is a column
projection + recompression, never a row filter or edit. The dropped columns
are re-fetchable from ERCOT's public archive (fetch_ercot_60day_*.py) if a
future lane ever needs one; add it to the KEEP set and re-fetch.

Consumer audit (2026-07-22, this file is the registry — update it when a new
consumer reads a new column):

* DAM ``Gen_Resource_Data`` + ``ESR_Data`` (same 48-col layout) — KEEP 38:
  - derive_ercot_thermal_dam_availability (+ hourly grain): Delivery Date,
    Hour Ending, Resource Name, Resource Type, HSL, Resource Status
  - derive_ercot_nuclear_availability: same minus Hour Ending
  - derive_ercot_dam_cleared_share: + Awarded Quantity
  - parse_ercot_dam_offers / derive_dam_offer_hrmults (DAM offer walls):
    + LSL, QSE, Settlement Point Name, Energy Settlement Point Price,
    QSE submitted Curve-MW1..10 + Curve-Price1..10
  - build_ercot_as_by_restype_from_60day / derive_ercot_storage_capability
    (PWRSTR/ESR): + RegUp/RegDown/RRSPFR/RRSFFR/RRSUFR/NonSpin/ECRSSD Awarded
  - ERCOT-97 crosswalk lane: Settlement Point Name, QSE (already kept)
  DROPPED (no consumer): DME, Start Up Hot/Inter/Cold, Min Gen Cost,
  RegUp/RegDown/RRS/NonSpin/ECRS MCPC.

* SCED ``Gen_Resource_Data`` (``data/raw/ercot/SCED/`` + the monthly
  ``ercot/YYYY-MM.partNNNN.parquet`` corpus, same schema) — KEEP 79:
  - derive_ercot_sced_offer_wall(+_steam) / shoulder_online_span: SCED Time
    Stamp, Resource Name, Resource Type, Telemetered Resource Status,
    Base Point, HASL, HDL, HSL, LSL, SCED2 Curve-MW1..35 + Curve-Price1..35
  - ERCOT-97 RUC-conduct lane: Telemetered Resource Status (kept)
  (The 2026-02.part0001-0009 files lack HASL — the known corpus defect; the
  projection keeps whatever KEEP columns exist and warns on the gap.)

No-consumer DAM members (``--list-unconsumed`` / ``--delete-unconsumed``):
EnergyBids, EnergyBidAwards, EnergyOnlyOffers, EnergyOnlyOfferAwards,
PTPObligationBids, PTPObligationBidAwards, PTP_Obligation_Option,
Load_Resource_ASOffers, QSE_Self_Arranged_AS — zero references anywhere in
scripts/, src/, tests/ (audited 2026-07-22). Deleting them removes ~181 MB
with nothing to re-point.

NOTE: rewriting/deleting files in the WORKING TREE shrinks the checkout and
future clones only after the commit lands; the old blobs remain in git
history until the owner runs a history rewrite (git filter-repo / BFG) —
that part is deliberately out of scope here.

Usage::

    python scripts/data/slim_ercot_dam_disclosure.py [--dry-run] [--sced]
        [--list-unconsumed | --delete-unconsumed]
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
DAM_DIR = REPO / "data" / "raw" / "ercot"
SCED_DIR = DAM_DIR / "SCED"

DAM_KEEP: list[str] = (
    [
        "Delivery Date",
        "Hour Ending",
        "QSE",
        "Resource Name",
        "Resource Type",
        "HSL",
        "LSL",
        "Resource Status",
        "Settlement Point Name",
        "Awarded Quantity",
        "Energy Settlement Point Price",
    ]
    + [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
    + [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]
    + [
        "RegUp Awarded",
        "RegDown Awarded",
        "RRSPFR Awarded",
        "RRSFFR Awarded",
        "RRSUFR Awarded",
        "NonSpin Awarded",
        "ECRSSD Awarded",
    ]
)

SCED_KEEP: list[str] = (
    [
        "SCED Time Stamp",
        "Resource Name",
        "Resource Type",
        "Telemetered Resource Status",
        "Base Point",
        "HASL",
        "HDL",
        "HSL",
        "LSL",
    ]
    + [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
    + [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
)

UNCONSUMED_MARKERS = (
    "EnergyBids_",
    "EnergyBidAwards_",
    "EnergyOnlyOffers_",
    "EnergyOnlyOfferAwards_",
    "PTPObligationBids_",
    "PTPObligationBidAwards_",
    "PTP_Obligation_Option_",
    "Load_Resource_ASOffers_",
    "QSE_Self_Arranged_AS_",
)


def slim_file(path: Path, keep: list[str], dry: bool) -> tuple[int, int]:
    """Rewrite ``path`` with only ``keep`` columns at zstd-15. Returns (before, after) bytes."""
    before = path.stat().st_size
    pf = pq.ParquetFile(path)
    present = [c for c in keep if c in pf.schema_arrow.names]
    missing = [c for c in keep if c not in pf.schema_arrow.names]
    already = set(pf.schema_arrow.names) == set(present)
    if missing:
        print(f"    (schema gap — {len(missing)} KEEP col(s) absent: {missing[:4]}{'…' if len(missing) > 4 else ''})")
    if dry:
        return before, before
    table = pq.read_table(path, columns=present)
    tmp = path.with_suffix(".slim.tmp")
    pq.write_table(
        table,
        tmp,
        compression="zstd",
        compression_level=15,
        use_dictionary=True,
        row_group_size=2_000_000,
    )
    # paranoia: row count must survive the projection exactly
    if pq.ParquetFile(tmp).metadata.num_rows != pf.metadata.num_rows:
        tmp.unlink()
        raise SystemExit(f"row-count mismatch rewriting {path} — aborted, original untouched")
    del pf
    os.replace(tmp, path)
    return before, path.stat().st_size


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sced", action="store_true", help="also slim the SCED corpus (SCED/ + monthly parts)")
    ap.add_argument("--list-unconsumed", action="store_true")
    ap.add_argument("--delete-unconsumed", action="store_true")
    args = ap.parse_args()

    total_b = total_a = 0
    targets: list[tuple[Path, list[str]]] = []
    for p in sorted(DAM_DIR.glob("*60d_DAM_Gen_Resource_Data_*.parquet")):
        targets.append((p, DAM_KEEP))
    for p in sorted(DAM_DIR.glob("*60d_DAM_ESR_Data_*.parquet")):
        targets.append((p, DAM_KEEP))
    if args.sced:
        for p in sorted(SCED_DIR.glob("*.parquet")):
            targets.append((p, SCED_KEEP))
        for p in sorted(DAM_DIR.glob("2[0-9][0-9][0-9]-[0-9][0-9].part*.parquet")):
            targets.append((p, SCED_KEEP))

    for p, keep in targets:
        b, a = slim_file(p, keep, args.dry_run)
        total_b += b
        total_a += a
        print(f"{b/1048576:7.1f} -> {a/1048576:7.1f} MB  {p.name}")
    if targets:
        print(
            f"TOTAL {total_b/1048576:.1f} -> {total_a/1048576:.1f} MB "
            f"({(1 - total_a/max(total_b, 1)) * 100:.0f}% saved"
            f"{', DRY RUN — nothing written' if args.dry_run else ''})"
        )

    if args.list_unconsumed or args.delete_unconsumed:
        print("\nno-consumer disclosure members (zero references in scripts/src/tests):")
        for p in sorted(DAM_DIR.glob("*.parquet")):
            if any(m in p.name for m in UNCONSUMED_MARKERS):
                print(f"{p.stat().st_size/1048576:7.1f} MB  {p.name}")
                if args.delete_unconsumed:
                    p.unlink()
                    print("         deleted")


if __name__ == "__main__":
    main()
