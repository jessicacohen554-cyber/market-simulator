#!/usr/bin/env python3
"""Fetch ERCOT 60-Day SCED Disclosure Gen Resource Data for named delivery days.

The RT-side sibling of ``scripts/fetch_ercot_60day_gen_resource.py`` (NP3-966
DAM family): ERCOT MIS report **NP3-965-ER "60-Day SCED Disclosure Reports"**
(``reportTypeId=13052`` — verified in ``scripts/fetch_ercot_as_reports.py`` by
catalog + product-page cross-check), one ~10 MB zip per publication day whose
``60d_SCED_Gen_Resource_Data-DD-MMM-YY.csv`` member carries, per resource per
~5-minute SCED interval, the TELEMETERED REAL-TIME ENERGY OFFER CURVES the
actual SCED dispatch ran on:

* ``SCED1 Curve-MW1..35 / -Price1..35`` and ``SCED2 Curve-MW1..35 /
  -Price1..35`` — the two-step SCED energy offer curves (Step 1 mitigated /
  Step 2; kept BOTH so a derivation can measure which step reproduces the
  observed system lambda rather than assuming);
* ``Submitted TPO-MW1..10 / -Price1..10`` — the QSE's submitted three-part
  offer curve points;
* telemetry: ``Telemetered Resource Status``, ``Output Schedule``, ``HSL`` /
  ``HASL`` / ``HDL`` / ``LSL`` / ``LASL`` / ``LDL``, ``Base Point``,
  ``Telemetered Net Output``, per-service AS responsibilities.

This is the direct ex-ante measurement of RT price formation — the same
market-design measurement family as the DAM disclosure offer curves behind
``ercot_offer_surface_conditional`` / the ERCOT-72 cleared-share wall (rule 13
admissible: QSEs regenerate these offers every day from forward drivers).

**Scoped intake (the ERCOT-74 pattern):** NP3-965 files are 5-minute-grain and
LARGE (~90 MB CSV per delivery day), so this script fetches an explicit list
of DELIVERY DAYS (``--delivery-days``), not blanket publication windows —
scope the intake to the anatomy's target hour-clusters' days. An optional
``--hod-start/--hod-end`` (CST, inclusive) keeps only the day's relevant
hour window to hold the committed parquet at a reviewable size; the window is
recorded per row group by construction (every kept interval's stamp is in the
parquet) so the scoping is self-documenting.

Publication→delivery mapping: publication day P carries exactly delivery day
P − 60 days (same lag as NP3-966, verified live 2026-07-16: the doc published
2024-06-15 carries SCED stamps 2024-04-16). Rolling retention: the free MIS
doc list reaches back ~2.3 years (earliest listed publication 2024-03-24 on
2026-07-16 → earliest reachable delivery ~2024-01-24); earlier deliveries are
permanently unreachable on the free path (the credentialed data.ercot.com
archive is owner-declined — ``docs/handoffs/ercot-as-coopt-plan-2026-07.md``
§WS-E). The script reports, never fabricates, out-of-window days.

Holdout hygiene (CLAUDE.md rule 22): ``--max-delivery-date`` (default
2025-12-31) refuses delivery days beyond the training window.

Timestamps: the CSV's ``SCED Time Stamp`` is Central Prevailing Time with a
``Repeated Hour Flag`` for the fall-back hour — rows are kept as published
(raw copy); consumers convert CPT→CST via
``build_ercot_hsl._prevailing_to_standard`` exactly as
``scripts/fetch_ercot_ordc_reserves.py`` does for NP6-905.

Run (the ERCOT-74 leg-1 intake — 2024 RT-tail cluster days, evening window):
    python scripts/fetch_ercot_60day_sced_gen_resource.py \
        --delivery-days 2024-03-04 2024-04-16 ... \
        --hod-start 11 --hod-end 22 --window-label 2024_ercot74_tail_days
"""

from __future__ import annotations

import argparse
import io
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
# NP3-965-ER "60-Day SCED Disclosure Reports" — reportTypeId verified in
# scripts/fetch_ercot_as_reports.py (EMIL catalog + product page agree).
REPORT_TYPE_ID = 13052
MEMBER_PREFIX = "60d_SCED_Gen_Resource_Data-"
# NP3-965 publishes each delivery day exactly 60 days later (same lag family
# as NP3-966; verified live against the 2024-06-15 publication).
PUBLICATION_LAG_DAYS = 60
_TIMEOUT_S = 300

# Non-numeric columns of the 60d_SCED_Gen_Resource_Data CSV; everything else
# is coerced float64 (curve points, telemetry MW, AS responsibilities).
_STRING_COLS = (
    "SCED Time Stamp",
    "Repeated Hour Flag",
    "QSE",
    "DME",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "Bid_Type",
    "Proxy Extension",
)


def _get_with_retries(url: str, params: dict, tries: int = 4) -> requests.Response:
    """GET with exponential backoff (2/4/8 s) — MIS drops long pulls sometimes."""
    import time

    for attempt in range(tries):
        try:
            resp = requests.get(url, params=params, timeout=_TIMEOUT_S)
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout) as err:
            if attempt == tries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"    transient fetch error ({err}); retrying in {wait}s", flush=True)
            time.sleep(wait)
    raise AssertionError("unreachable")


def _list_docs() -> list[dict]:
    """Return every NP3-965-ER document currently listed by the MIS."""
    resp = _get_with_retries(DOC_LIST_URL, {"reportTypeId": REPORT_TYPE_ID})
    return [d["Document"] for d in resp.json()["ListDocsByRptTypeRes"]["DocumentList"]]


def _read_gen_csv(zip_bytes: bytes) -> pd.DataFrame:
    """Extract the Gen Resource Data member of a daily bundle as strings."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        members = [n for n in zf.namelist() if n.startswith(MEMBER_PREFIX)]
        if len(members) != 1:
            raise ValueError(
                f"expected exactly one {MEMBER_PREFIX}* member, got {members}"
            )
        with zf.open(members[0]) as fh:
            return pd.read_csv(fh, dtype=str, keep_default_na=False)


def _coerce_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce the all-string CSV frame: identity strings, numeric float64."""
    out = {}
    for col in df.columns:
        s = df[col].replace("", pd.NA)
        if col.strip() in _STRING_COLS or col in _STRING_COLS:
            out[col] = s.astype("string")
        else:
            out[col] = pd.to_numeric(s, errors="raise").astype("float64")
    return pd.DataFrame(out)


def fetch_days(
    delivery_days: list[date],
    window_label: str,
    out_dir: Path,
    max_delivery_date: date,
    hod_start: int = 0,
    hod_end: int = 23,
    zip_cache: Path | None = None,
) -> Path:
    """Fetch each delivery day's publication zip, keep the hod window, write parquet."""
    bad = [d for d in delivery_days if d > max_delivery_date]
    if bad:
        raise SystemExit(
            f"delivery days {bad} beyond --max-delivery-date {max_delivery_date} "
            "(holdout hygiene, CLAUDE.md rule 22)"
        )
    docs = _list_docs()
    by_pub_day: dict[str, list[dict]] = {}
    for doc in docs:
        by_pub_day.setdefault(doc["PublishDate"][:10], []).append(doc)

    frames = []
    unreachable = []
    for dd in sorted(delivery_days):
        pub = dd + timedelta(days=PUBLICATION_LAG_DAYS)
        cands = by_pub_day.get(pub.isoformat(), [])
        if not cands:
            unreachable.append((dd, pub))
            print(f"  {dd} (pub {pub}): NOT LISTED — outside the MIS retention window")
            continue
        # If ERCOT reposts a publication day, the most recent publish wins.
        cands.sort(key=lambda d: d["PublishDate"], reverse=True)
        doc = cands[0]
        cached = zip_cache / f"{doc['DocID']}.zip" if zip_cache else None
        if cached is not None and cached.exists():
            zip_bytes = cached.read_bytes()
        else:
            resp = _get_with_retries(DOWNLOAD_URL, {"doclookupId": doc["DocID"]})
            zip_bytes = resp.content
            if cached is not None:
                zip_cache.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(zip_bytes)
        df = _read_gen_csv(zip_bytes)
        # CPT hour-of-day filter on the raw stamp (MM/DD/YYYY HH:MM:SS): a
        # coarse, self-documenting window scope — consumers still convert
        # CPT->CST for placement. hod 0..23 keeps the whole day.
        if (hod_start, hod_end) != (0, 23):
            hod = pd.to_datetime(
                df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S"
            ).dt.hour
            df = df[(hod >= hod_start) & (hod <= hod_end)]
        # Coerce PER DAY: a whole multi-day window of all-string frames is
        # ~60 bytes/cell and OOM-kills a 15 GB container at the final concat
        # (observed live on the 25-day ERCOT-74 intake); the coerced float64
        # day is ~10x smaller.
        frames.append(_coerce_schema(df))
        print(
            f"  {dd} (pub {pub}, doc {doc['DocID']}): kept {len(df):,} rows "
            f"(hod {hod_start}..{hod_end})",
            flush=True,
        )
    if not frames:
        raise SystemExit("no requested delivery day is reachable — nothing to write")

    merged = pd.concat(frames, ignore_index=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = (
        out_dir
        / f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{window_label}.parquet"
    )
    merged.to_parquet(out, index=False)
    print(
        f"wrote {out} ({len(merged):,} rows, {out.stat().st_size / 1e6:.1f} MB); "
        f"unreachable days: {[str(d) for d, _ in unreachable] or 'none'}"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--delivery-days",
        nargs="+",
        required=True,
        help="delivery days to fetch, YYYY-MM-DD (publication = day + 60)",
    )
    ap.add_argument("--window-label", required=True)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument(
        "--max-delivery-date",
        default="2025-12-31",
        help="refuse deliveries beyond this date (holdout hygiene, rule 22)",
    )
    ap.add_argument("--hod-start", type=int, default=0)
    ap.add_argument("--hod-end", type=int, default=23)
    ap.add_argument(
        "--zip-cache",
        default=None,
        help="directory caching the downloaded daily zips (resumable re-runs)",
    )
    args = ap.parse_args()

    days = [datetime.strptime(d, "%Y-%m-%d").date() for d in args.delivery_days]
    fetch_days(
        days,
        args.window_label,
        Path(args.out_dir),
        datetime.strptime(args.max_delivery_date, "%Y-%m-%d").date(),
        hod_start=args.hod_start,
        hod_end=args.hod_end,
        zip_cache=Path(args.zip_cache) if args.zip_cache else None,
    )


if __name__ == "__main__":
    main()
