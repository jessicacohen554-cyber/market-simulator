#!/usr/bin/env python3
"""Fetch ERCOT 60-Day SCED Disclosure Gen Resource Data for named delivery days.

The RT-side sibling of ``scripts/data/fetch_ercot_60day_gen_resource.py`` (NP3-966
DAM family): ERCOT MIS report **NP3-965-ER "60-Day SCED Disclosure Reports"**
(``reportTypeId=13052`` — verified in ``scripts/data/fetch_ercot_as_reports.py`` by
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
``scripts/data/fetch_ercot_ordc_reserves.py`` does for NP6-905.

Run (the ERCOT-74 leg-1 intake — 2024 RT-tail cluster days, evening window):
    python scripts/data/fetch_ercot_60day_sced_gen_resource.py \
        --delivery-days 2024-03-04 2024-04-16 ... \
        --hod-start 11 --hod-end 22 --window-label 2024_ercot74_tail_days

Run (the ERCOT item-8 part-(a) intake — CT fleet, FULL SPAN, all hours): the
day-list scope above is what the ERCOT-147 §4 reopen condition asked to be
lifted, so that the CT daily conduct object can be *measured* rather than
sampled on 82 selected days. ``--resource-types SCLE90 SCGT90`` cuts the day
to ~15 % of its rows (~0.5 MB of parquet), which is what makes a ~700-day
span affordable; ``--shard-by-month`` bounds resident memory to one month and
``--skip-existing`` makes the span resumable after an interruption:
    python scripts/data/fetch_ercot_60day_sced_gen_resource.py \
        --delivery-range 2024-01-10 2025-12-31 \
        --resource-types SCLE90 SCGT90 \
        --shard-by-month --skip-existing \
        --window-label ct_fullspan --out-dir data/raw/ercot/SCED-CT
"""

from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from datetime import date, datetime, timedelta
import sys
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import ERCOT_MIS_DIR  # noqa: E402

DEFAULT_OUT_DIR = ERCOT_MIS_DIR

# Same unauthenticated legacy MIS endpoints as scripts/data/fetch_ercot_as_reports.py.
DOC_LIST_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
DOWNLOAD_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"
# NP3-965-ER "60-Day SCED Disclosure Reports" — reportTypeId verified in
# scripts/data/fetch_ercot_as_reports.py (EMIL catalog + product page agree).
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


_MONTH_ABBR = {
    m: i
    for i, m in enumerate(
        "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), start=1
    )
}
# 60d_SCED_Gen_Resource_Data-DD-MMM-YY.csv. VERIFIED 2026-08-04: that date is
# the PUBLICATION stamp, NOT the delivery day — the member named -04-OCT-24 in
# the 2024-10-04 publication carries SCED stamps of 08/05/2024, i.e. delivery
# = publication - 60. So the name is a HINT and never the answer; the delivery
# day is read from the file's own SCED Time Stamp.
_MEMBER_STAMP_RE = re.compile(
    re.escape(MEMBER_PREFIX) + r"(\d{2})-([A-Za-z]{3})-(\d{2})\.csv$"
)


def _member_stamp_day(name: str) -> date | None:
    """Publication day encoded in a Gen Resource Data member name, or None."""
    match = _MEMBER_STAMP_RE.search(name)
    if not match:
        return None
    day, mon, year = match.groups()
    month = _MONTH_ABBR.get(mon.upper())
    if month is None:
        return None
    return date(2000 + int(year), month, int(day))


def _gen_member_names(zip_bytes: bytes) -> list[str]:
    """Every Gen Resource Data member in a publication zip.

    ERCOT usually posts one per publication, but NOT always: the 2024-10-04
    publication day carries TWO documents — the ordinary 10 MB daily one, and a
    245 MB ``Supplemental_60_Day_SCED_Disclosure`` holding 32 members. A
    reader that assumes one member, or that assumes one document per
    publication day, breaks on those.
    """
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        return [n for n in zf.namelist() if n.startswith(MEMBER_PREFIX)]


def _member_delivery_days(zip_bytes: bytes, member: str) -> list[date]:
    """Delivery day(s) a member actually contains, read from its own stamps."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open(member) as fh:
            stamps = pd.read_csv(
                fh, dtype=str, usecols=["SCED Time Stamp"], keep_default_na=False
            )["SCED Time Stamp"]
    days = pd.to_datetime(stamps.str.slice(0, 10), format="%m/%d/%Y").dt.date
    return sorted(set(days))


def _read_member(zip_bytes: bytes, member: str) -> pd.DataFrame:
    """Read one named Gen Resource Data member as strings."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open(member) as fh:
            return pd.read_csv(fh, dtype=str, keep_default_na=False)


def _read_gen_csv(zip_bytes: bytes) -> pd.DataFrame:
    """Extract the Gen Resource Data member of a single-day publication zip."""
    members = _gen_member_names(zip_bytes)
    if len(members) != 1:
        raise ValueError(
            f"expected exactly one {MEMBER_PREFIX}* member, got {sorted(members)}"
        )
    return _read_member(zip_bytes, members[0])


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


def fetch_span(
    delivery_start: date,
    delivery_end: date,
    window_label: str,
    out_dir: Path,
    max_delivery_date: date,
    hod_start: int = 0,
    hod_end: int = 23,
    resource_types: tuple[str, ...] | None = None,
    skip_existing: bool = True,
) -> list[Path]:
    """Fetch a full delivery-day span by scanning PUBLICATIONS, one file per day.

    Why publication-driven rather than delivery-driven: ERCOT's nominal
    publication = delivery + 60 does not always hold. The 2024-10-04
    publication is a catch-up BUNDLE carrying 32 delivery days at lags 9-39,
    and the days it displaced are not in the zip their nominal lag points at —
    a delivery-driven loop simply cannot find them. Scanning publications and
    harvesting whatever delivery days each zip declares is the only complete
    method, and it downloads each zip exactly once either way.

    One parquet per DELIVERY day, so a day that never turns up anywhere is
    visible as a missing file rather than silently absent from a month shard.
    ``skip_existing`` then resumes at day granularity, and a per-doc index
    (``_processed_docs.json``) lets a resume skip publications already mined.

    Holdout hygiene (rule 22): a harvested member is kept ONLY if its delivery
    day is inside [delivery_start, delivery_end] and <= max_delivery_date, so a
    bundle spilling into a quarantined year cannot smuggle a day in.
    """
    if delivery_end > max_delivery_date:
        raise SystemExit(
            f"--delivery-range end {delivery_end} beyond --max-delivery-date "
            f"{max_delivery_date} (holdout hygiene, CLAUDE.md rule 22)"
        )
    wanted = {
        delivery_start + timedelta(days=i)
        for i in range((delivery_end - delivery_start).days + 1)
    }
    out_dir.mkdir(parents=True, exist_ok=True)

    def _day_path(day: date) -> Path:
        return (
            out_dir / "60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_"
            f"{window_label}_{day.isoformat()}.parquet"
        )

    index_path = out_dir / "_processed_docs.json"
    processed: set[str] = set()
    if skip_existing and index_path.exists():
        processed = set(json.loads(index_path.read_text()).get("doc_ids", []))

    # A publication can only carry deliveries at a positive lag, so bound the
    # scan generously on both sides rather than assuming the nominal 60.
    pub_lo = delivery_start
    pub_hi = delivery_end + timedelta(days=PUBLICATION_LAG_DAYS + 15)
    docs = []
    for doc in _list_docs():
        pub = datetime.strptime(doc["PublishDate"][:10], "%Y-%m-%d").date()
        if pub_lo <= pub <= pub_hi:
            docs.append((pub, doc))
    docs.sort(key=lambda pd_: pd_[0])
    print(
        f"scanning {len(docs)} publications ({pub_lo}..{pub_hi}) for "
        f"{len(wanted)} delivery days",
        flush=True,
    )

    written: list[Path] = []
    have = {d for d in wanted if _day_path(d).exists()} if skip_existing else set()
    if have:
        print(f"  {len(have)} delivery day(s) already on disk — skipping", flush=True)

    for pub, doc in docs:
        if skip_existing and doc["DocID"] in processed:
            continue
        if not (wanted - have):
            break
        # Cheap pre-download skip. An ORDINARY publication obeys delivery =
        # publication - 60 (verified live), so one outside the wanted range
        # need not be downloaded at all. A SUPPLEMENTAL is exempt: its lag is
        # not the nominal one, so it is always opened and read.
        name = doc.get("ConstructedName") or doc.get("FriendlyName") or ""
        is_supplemental = "supplemental" in name.lower()
        nominal = pub - timedelta(days=PUBLICATION_LAG_DAYS)
        if not is_supplemental and nominal not in wanted:
            processed.add(doc["DocID"])
            continue
        resp = _get_with_retries(DOWNLOAD_URL, {"doclookupId": doc["DocID"]})
        names = _gen_member_names(resp.content)
        # Delivery day comes from the member's own SCED stamps, never its
        # filename (which is the publication stamp). For the ordinary
        # one-member document the nominal publication-60 is used first as a
        # cheap skip test, then VERIFIED against the content before writing.
        member_days: dict[date, str] = {}
        for name in names:
            stamp = _member_stamp_day(name)
            nominal = stamp - timedelta(days=PUBLICATION_LAG_DAYS) if stamp else None
            if len(names) == 1 and nominal is not None and nominal not in wanted:
                continue
            for day in _member_delivery_days(resp.content, name):
                member_days.setdefault(day, name)
        take = sorted((wanted - have) & set(member_days))
        if len(names) > 1:
            print(
                f"  pub {pub}: SUPPLEMENTAL bundle, {len(names)} members "
                f"covering delivery {min(member_days, default='-')}.."
                f"{max(member_days, default='-')}; {len(take)} wanted",
                flush=True,
            )
        for day in take:
            df = _read_member(resp.content, member_days[day])
            # A supplemental member can hold more than one delivery day; keep
            # only the day this file is being written for.
            stamp_day = pd.to_datetime(
                df["SCED Time Stamp"].str.slice(0, 10), format="%m/%d/%Y"
            ).dt.date
            df = df[stamp_day == day]
            if (hod_start, hod_end) != (0, 23):
                hod = pd.to_datetime(
                    df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S"
                ).dt.hour
                df = df[(hod >= hod_start) & (hod <= hod_end)]
            if resource_types is not None:
                present = sorted(set(df["Resource Type"].unique()))
                df = df[df["Resource Type"].isin(resource_types)]
                if df.empty:
                    print(
                        f"  {day}: 0 rows after resource scope "
                        f"{sorted(resource_types)} — day carried {present}",
                        flush=True,
                    )
                    continue
            path = _day_path(day)
            _coerce_schema(df).to_parquet(path, index=False)
            written.append(path)
            have.add(day)
            print(f"  {day} (pub {pub}): {len(df):,} rows -> {path.name}", flush=True)
        processed.add(doc["DocID"])
        index_path.write_text(json.dumps({"doc_ids": sorted(processed)}, indent=0))

    missing = sorted(wanted - have)
    print(
        f"\nwrote {len(written)} day file(s); {len(have)}/{len(wanted)} delivery "
        f"days present; {len(missing)} NOT FOUND in any listed publication"
    )
    if missing:
        runs = []
        start = prev = missing[0]
        for day in missing[1:]:
            if (day - prev).days == 1:
                prev = day
                continue
            runs.append((start, prev))
            start = prev = day
        runs.append((start, prev))
        for lo, hi in runs:
            span = (hi - lo).days + 1
            print(f"  MISSING {lo} .. {hi}  ({span} day{'s' if span > 1 else ''})")
    return written


def fetch_days(
    delivery_days: list[date],
    window_label: str,
    out_dir: Path,
    max_delivery_date: date,
    hod_start: int = 0,
    hod_end: int = 23,
    zip_cache: Path | None = None,
    resource_types: tuple[str, ...] | None = None,
    shard_by_month: bool = False,
    skip_existing: bool = False,
) -> list[Path]:
    """Fetch each delivery day's publication zip, keep the hod window, write parquet.

    ``resource_types`` restricts the kept rows to those ``Resource Type`` codes
    (e.g. ``("SCLE90", "SCGT90")`` for the CT fleet) — the scoping that makes a
    FULL-SPAN multi-year intake size-feasible where the unscoped day is ~90 MB
    of CSV. ``shard_by_month`` writes one parquet per DELIVERY month instead of
    a single merged file, which is what bounds memory on a multi-year span (a
    coerced day is ~30 MB resident; a whole 700-day span concatenated is not
    representable). ``skip_existing`` makes such a span resumable: an already
    written month shard is left alone and its days are never re-fetched.

    Returns every parquet written (one element unless ``shard_by_month``).
    """
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

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    frames: list[pd.DataFrame] = []
    unreachable: list[tuple[date, date]] = []
    skipped: list[date] = []
    current_month: str | None = None

    def _shard_path(month: str | None) -> Path:
        label = window_label if month is None else f"{window_label}_{month}"
        return (
            out_dir
            / f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{label}.parquet"
        )

    def _flush(month: str | None) -> None:
        """Write the buffered days out as one shard and release them."""
        if not frames:
            return
        merged = pd.concat(frames, ignore_index=True)
        frames.clear()
        out = _shard_path(month)
        merged.to_parquet(out, index=False)
        written.append(out)
        print(
            f"wrote {out.name} ({len(merged):,} rows, "
            f"{out.stat().st_size / 1e6:.1f} MB)",
            flush=True,
        )
        del merged

    for dd in sorted(delivery_days):
        if shard_by_month:
            month = dd.strftime("%Y-%m")
            if month != current_month:
                _flush(current_month)
                current_month = month
            if skip_existing and _shard_path(month).exists():
                skipped.append(dd)
                continue
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
        # Resource-type scope, applied on the raw published code so the filter
        # is auditable against the CSV itself (SCLE90/SCGT90 = the CT fleet).
        # An empty day after scoping is REPORTED, never silently dropped.
        if resource_types is not None:
            present = set(df["Resource Type"].unique())
            df = df[df["Resource Type"].isin(resource_types)]
            if df.empty:
                print(
                    f"  {dd} (pub {pub}): 0 rows after resource scope "
                    f"{sorted(resource_types)} — day carried {sorted(present)}",
                    flush=True,
                )
                continue
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
    _flush(current_month if shard_by_month else None)
    if not written and not skipped:
        raise SystemExit("no requested delivery day is reachable — nothing to write")

    print(
        f"wrote {len(written)} parquet(s) to {out_dir}; "
        f"{len(skipped)} day(s) already covered by an existing month shard; "
        f"unreachable days: {[str(d) for d, _ in unreachable] or 'none'}"
    )
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--delivery-days",
        nargs="+",
        help="delivery days to fetch, YYYY-MM-DD (publication = day + 60)",
    )
    ap.add_argument(
        "--delivery-range",
        nargs=2,
        metavar=("START", "END"),
        help="inclusive delivery-day range YYYY-MM-DD YYYY-MM-DD — the "
        "full-span alternative to --delivery-days (use with --resource-types "
        "and --shard-by-month; unreachable days are reported, never faked)",
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
    ap.add_argument(
        "--resource-types",
        nargs="+",
        default=None,
        help="keep only these published Resource Type codes (e.g. SCLE90 "
        "SCGT90 for the CT fleet) — the scope that makes a full-span intake "
        "size-feasible. Default: every resource, as before.",
    )
    ap.add_argument(
        "--shard-by-month",
        action="store_true",
        help="write one parquet per DELIVERY month instead of one merged file "
        "(bounds memory on a multi-year span, and makes it resumable)",
    )
    ap.add_argument(
        "--skip-existing",
        action="store_true",
        help="with --shard-by-month, leave already-written month shards alone "
        "and never re-fetch their days",
    )
    ap.add_argument(
        "--no-resume",
        action="store_true",
        help="with --delivery-range, re-fetch every day even if its parquet "
        "already exists (spans resume by default)",
    )
    args = ap.parse_args()

    if bool(args.delivery_days) == bool(args.delivery_range):
        ap.error("pass exactly one of --delivery-days / --delivery-range")
    if args.delivery_range:
        start, end = (
            datetime.strptime(d, "%Y-%m-%d").date() for d in args.delivery_range
        )
        if end < start:
            ap.error(f"--delivery-range END {end} precedes START {start}")
        # A span goes through the PUBLICATION-driven scanner: ERCOT's nominal
        # delivery+60 does not hold across its catch-up bundles, so a
        # delivery-driven loop cannot find the displaced days.
        fetch_span(
            start,
            end,
            args.window_label,
            Path(args.out_dir),
            datetime.strptime(args.max_delivery_date, "%Y-%m-%d").date(),
            hod_start=args.hod_start,
            hod_end=args.hod_end,
            resource_types=tuple(args.resource_types) if args.resource_types else None,
            skip_existing=args.skip_existing or not args.no_resume,
        )
        return

    days = [datetime.strptime(d, "%Y-%m-%d").date() for d in args.delivery_days]
    if args.skip_existing and not args.shard_by_month:
        ap.error("--skip-existing requires --shard-by-month")

    fetch_days(
        days,
        args.window_label,
        Path(args.out_dir),
        datetime.strptime(args.max_delivery_date, "%Y-%m-%d").date(),
        hod_start=args.hod_start,
        hod_end=args.hod_end,
        zip_cache=Path(args.zip_cache) if args.zip_cache else None,
        resource_types=tuple(args.resource_types) if args.resource_types else None,
        shard_by_month=args.shard_by_month,
        skip_existing=args.skip_existing,
    )


if __name__ == "__main__":
    main()
