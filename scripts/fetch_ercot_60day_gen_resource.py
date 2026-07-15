#!/usr/bin/env python3
"""Fetch ERCOT 60-Day DAM Disclosure Gen Resource Data and consolidate to parquet.

Extends the ``data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_
<pubwindow>.parquet`` family — the per-resource, per-delivery-hour DAM
disclosure rows (offers, awards, HSL/LSL, ``Resource Status``) consumed by
``scripts/parse_ercot_dam_offers.py``, ``scripts/build_ercot_as_by_restype_
from_60day.py``, ``scripts/derive_ercot_thermal_dam_availability.py`` and
``scripts/derive_ercot_storage_capability.py``.

Source: ERCOT MIS report NP3-966-ER "60-Day DAM Disclosure Reports"
(reportTypeId 13051), one ~7-9 MB zip per publication day, each carrying
thirteen+ CSVs of which this script keeps only the requested family
(default ``60d_DAM_Gen_Resource_Data-DD-MMM-YY.csv``; ``--family ESR_Data``
selects ``60d_DAM_ESR_Data-*.csv``, the Energy Storage Resource file ERCOT
ADDED to the daily bundle at the RTC+B go-live — from delivery day
2025-12-06 storage no longer appears as PWRSTR Gen resources but as combined
``ESR`` resources with a negative-LSL charge/discharge envelope, same
48-column layout). Fetched through the same free,
unauthenticated legacy MIS endpoints as ``scripts/fetch_ercot_as_reports.py``
(see that script's module docstring for how the reportTypeId was verified and
for the rolling-retention-window caveat: the doc list reaches back only ~2.3
years from "today", so e.g. the missing Dec-2023 publication — deliveries
2023-10-02..2023-11-01 — is permanently unreachable on the free path; the
credentialed data.ercot.com archive was declined by the repo owner,
docs/handoffs/ercot-as-coopt-plan-2026-07.md §WS-E).

Publication→delivery mapping (verified against every committed parquet):
publication day D carries exactly the delivery day D − 60 days, so a
publication window [P0, P1] covers deliveries [P0−60d, P1−60d].

Naming convention (matches the committed family): the parquet is named for the
*publication* months it consolidates, e.g. ``..._2026_Jan-Mar.parquet`` for
publications 2026-01-01..2026-03-01 (deliveries 2025-11-02..2025-12-31).

Holdout hygiene: ``--max-delivery-date`` drops any delivery rows after the
given date before writing (default 2025-12-31 — H1-2026 is a locked test
window, CLAUDE.md rule 22; the training years end at 2025).

Run (the ERCOT-66 intake — deliveries 2025-11-02..2025-12-31):
    python scripts/fetch_ercot_60day_gen_resource.py \
        --pub-start 2026-01-01 --pub-end 2026-03-01 --window-label 2026_Jan-Mar
    python scripts/fetch_ercot_60day_gen_resource.py --family ESR_Data \
        --pub-start 2026-02-01 --pub-end 2026-03-01 --window-label 2026_Jan-Mar
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "raw" / "ercot"

# Same unauthenticated legacy MIS endpoints as scripts/fetch_ercot_as_reports.py.
DOC_LIST_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
DOWNLOAD_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"
# NP3-966-ER "60-Day DAM Disclosure Reports" — verified in
# scripts/fetch_ercot_as_reports.py (catalog + product-page cross-check).
REPORT_TYPE_ID = 13051
# CSV families this script can keep from each daily bundle. ESR_Data exists
# only from the RTC+B go-live (delivery 2025-12-06 / publication ~2026-02-04);
# earlier bundles simply have no such member and contribute nothing.
CSV_FAMILIES = ("Gen_Resource_Data", "ESR_Data")
# NP3-966 publishes each delivery day exactly 60 days later (verified against
# the delivery ranges of every committed Gen_Resource_Data parquet).
PUBLICATION_LAG_DAYS = 60
_TIMEOUT_S = 300

# Column dtypes of the committed parquet family (2025_Dec reference file):
# everything float64 except these four string + one int64 columns.
_STRING_COLS = (
    "Delivery Date",
    "QSE",
    "DME",
    "Resource Name",
    "Resource Type",
    "Resource Status",
    "Settlement Point Name",
)
_INT_COLS = ("Hour Ending",)


def _list_docs() -> list[dict]:
    """Return every NP3-966-ER document currently listed by the MIS."""
    resp = requests.get(
        DOC_LIST_URL, params={"reportTypeId": REPORT_TYPE_ID}, timeout=_TIMEOUT_S
    )
    resp.raise_for_status()
    return [d["Document"] for d in resp.json()["ListDocsByRptTypeRes"]["DocumentList"]]


def _read_family_csv(
    zip_bytes: bytes, member_prefix: str, allow_missing: bool
) -> pd.DataFrame | None:
    """Extract one family's CSV from a daily bundle as a DataFrame.

    ``allow_missing=True`` returns ``None`` when the bundle has no such member
    (the ESR_Data file does not exist before the RTC+B go-live publication).
    """
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        members = [n for n in zf.namelist() if n.startswith(member_prefix)]
        if not members and allow_missing:
            return None
        if len(members) != 1:
            raise ValueError(
                f"expected exactly one {member_prefix}* member, got {members}"
            )
        with zf.open(members[0]) as fh:
            return pd.read_csv(fh, dtype=str, keep_default_na=False)


def _coerce_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce the all-string CSV frame onto the committed parquet dtypes."""
    out = {}
    for col in df.columns:
        s = df[col].replace("", pd.NA)
        if col in _STRING_COLS:
            out[col] = s.astype("string")
        elif col in _INT_COLS:
            out[col] = s.astype("int64")
        else:
            out[col] = pd.to_numeric(s, errors="raise").astype("float64")
    return pd.DataFrame(out)


def fetch_window(
    pub_start: date,
    pub_end: date,
    window_label: str,
    out_dir: Path,
    max_delivery_date: date,
    family: str = "Gen_Resource_Data",
) -> Path:
    """Fetch publications [pub_start, pub_end], keep one family's rows, write parquet."""
    docs = _list_docs()
    picked = []
    for doc in docs:
        pub = datetime.fromisoformat(doc["PublishDate"]).date()
        if pub_start <= pub <= pub_end:
            picked.append((pub, doc))
    picked.sort(key=lambda t: t[0])
    n_days = (pub_end - pub_start).days + 1
    print(
        f"MIS lists {len(picked)} publication docs in {pub_start}..{pub_end} "
        f"({n_days} calendar days); deliveries expected "
        f"{pub_start - timedelta(days=PUBLICATION_LAG_DAYS)}.."
        f"{pub_end - timedelta(days=PUBLICATION_LAG_DAYS)}"
    )
    if not picked:
        raise SystemExit(
            "no documents listed in the requested publication window — outside "
            "ERCOT's rolling MIS retention (see module docstring)?"
        )

    member_prefix = f"60d_DAM_{family}-"
    # ESR_Data appears mid-window (RTC+B go-live) — a bundle without the
    # member is expected, not an error.
    allow_missing = family == "ESR_Data"
    frames = []
    for pub, doc in picked:
        resp = requests.get(
            DOWNLOAD_URL, params={"doclookupId": doc["DocID"]}, timeout=_TIMEOUT_S
        )
        resp.raise_for_status()
        df = _read_family_csv(resp.content, member_prefix, allow_missing)
        if df is None:
            print(f"  {pub} doc {doc['DocID']}: no {member_prefix}* member (pre-RTC+B)")
            continue
        frames.append(df)
        print(
            f"  {pub} doc {doc['DocID']}: {len(df):,} rows "
            f"(delivery {df['Delivery Date'].iloc[0]})"
        )
    if not frames:
        raise SystemExit(f"no {member_prefix}* members found in the whole window")

    merged = pd.concat(frames, ignore_index=True)
    merged = _coerce_schema(merged)
    delivery = pd.to_datetime(merged["Delivery Date"], format="%m/%d/%Y")
    n_dropped = int((delivery.dt.date > max_delivery_date).sum())
    if n_dropped:
        print(
            f"dropping {n_dropped:,} delivery rows after {max_delivery_date} "
            f"(holdout hygiene, CLAUDE.md rule 22)"
        )
        merged = merged[delivery.dt.date <= max_delivery_date].reset_index(drop=True)
        delivery = delivery[delivery.dt.date <= max_delivery_date]

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"60_DAY_DAM_DISCLOSURE_60d_DAM_{family}_{window_label}.parquet"
    merged.to_parquet(out, index=False)
    print(
        f"wrote {out.relative_to(REPO_ROOT)}: {len(merged):,} rows, deliveries "
        f"{delivery.min().date()}..{delivery.max().date()} "
        f"({out.stat().st_size:,} bytes)"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--pub-start",
        type=date.fromisoformat,
        required=True,
        help="first publication date (inclusive)",
    )
    ap.add_argument(
        "--pub-end",
        type=date.fromisoformat,
        required=True,
        help="last publication date (inclusive)",
    )
    ap.add_argument(
        "--window-label",
        required=True,
        help="publication-window label for the output filename, "
        "e.g. 2026_Jan-Mar (matches the committed family naming)",
    )
    ap.add_argument(
        "--family",
        choices=CSV_FAMILIES,
        default="Gen_Resource_Data",
        help="which CSV family to keep from each daily bundle (ESR_Data is the "
        "post-RTC+B storage file, present only from publication ~2026-02-04)",
    )
    ap.add_argument(
        "--max-delivery-date",
        type=date.fromisoformat,
        default=date(2025, 12, 31),
        help="drop delivery rows after this date (default "
        "%(default)s — training years end 2025; H1-2026 is a "
        "locked test window, CLAUDE.md rule 22)",
    )
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)
    fetch_window(
        args.pub_start,
        args.pub_end,
        args.window_label,
        args.out_dir,
        args.max_delivery_date,
        family=args.family,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
