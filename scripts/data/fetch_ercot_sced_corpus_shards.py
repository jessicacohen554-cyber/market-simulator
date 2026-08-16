#!/usr/bin/env python3
"""Fetch NP3-965 publication-month corpus shards (the ercot-183 2024/2025 re-upload).

Rebuilds the delivery-2024/2025 windows of the ERCOT **60-Day SCED Disclosure
Gen Resource Data** (NP3-965-ER, ``reportTypeId=13052``) full-year corpus under
``data/raw/ercot/SCED/`` in the EXISTING shard convention established by the
2026-07-21 owner upload and the 2026-08-03 delivery-2023 re-upload
(``docs/handoffs/ercot-sced-fullyear-intake-2026-07.md``):

* ``YYYY-MM.partNNNN.parquet`` keyed by the MIS **publication month** (delivery
  = publication − 60 days ≈ filename − 2 months);
* one part per publication day (= one delivery day), parts numbered in
  publication-day order, CONTINUING an on-disk month's existing numbering
  (``2024-03.part0009`` follows the re-upload's ``part0000-0008``);
* the raw 187-column all-string schema — the CSV member copied verbatim
  (``dtype=str, keep_default_na=False``: unused curve steps stay empty
  strings), parquet zstd. NO column slimming: the corpus's ``Submitted TPO-*``
  columns are live instrument inputs (``scripts/lib/sced_corpus_instruments``).

Source: the same unauthenticated legacy MIS endpoints as
``fetch_ercot_60day_sced_gen_resource.py`` (this module imports its verified
constants and zip/member helpers rather than re-declaring them). The free doc
list reaches back ~2.3 years — publication 2024-03-24 today — so deliveries
2024-01-10..23 (publications 2024-03-10..23) are UNREACHABLE on this path and
are reported, never fabricated (deliveries 2024-01-01..09 already sit on disk
as the delivery-2023 re-upload's bleed parts).

Supplemental documents (e.g. the 245 MB 2024-10-04 catch-up bundle carrying 32
displaced delivery days at lags 9–39) are opened after the ordinary pass and
harvested for Gen members whose delivery days are still uncovered; every
member's delivery day is read from its own ``SCED Time Stamp`` values, never
from a filename (the stamp-vs-name gotcha verified 2026-08-04). A delivery day
is written exactly once — a repost or supplemental duplicate of a covered day
is skipped and logged, so derives that stream every shard never double-weight
a day.

Provenance / admissibility: raw-copy intake of an ex-ante market-design
disclosure (CLAUDE.md rule 13 ``[R-MEASURED]``); data intake needs no holdout
marker (rule 22 — preparing inputs is unrestricted; the gates quarantine
*looking at answers*). ``--max-delivery-date`` (default 2025-12-31) still
refuses any member carrying a locked-test-year delivery day so no 2026 row
enters the corpus through a supplemental's irregular lag. Rule 23
``[R-FROZEN-DERIVE]``: this intake IS a SCED source-data update — the frozen
derived artifacts re-derive only under their own authorization, never here.

Usage (the ercot-183 re-upload)::

    python scripts/data/fetch_ercot_sced_corpus_shards.py \
        --pub-start 2024-03-24 --pub-end 2026-03-01 \
        --manifest <scratch>/sced_intake_manifest.json

Resume: pass the same ``--manifest`` — delivery days it records (plus any day
already covered by an on-disk shard's stamps listed there) are skipped.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))  # repo root: canonical scripts.data.* sibling imports on direct run
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import ERCOT_MIS_DIR  # noqa: E402

from scripts.data.fetch_ercot_60day_sced_gen_resource import (  # noqa: E402
    DOWNLOAD_URL,
    PUBLICATION_LAG_DAYS,
    _gen_member_names,
    _get_with_retries,
    _list_docs,
    _member_delivery_days,
    _read_member,
)

#: The corpus home (the 2026-08-03 re-upload location; `_sced_source_files`
#: scans it alongside the legacy top level, subdirectory copy winning).
DEFAULT_OUT_DIR = ERCOT_MIS_DIR / "SCED"

#: Days past --pub-end to scan for supplemental catch-up bundles: a displaced
#: delivery day can surface at an irregular (longer) lag, e.g. the 2026-02/03/04
#: supplementals carrying late-2025 deliveries.
SUPPLEMENTAL_SCAN_EXTRA_DAYS = 60


def _pub_day(doc: dict) -> date:
    """Publication day of an MIS document record."""
    return datetime.strptime(doc["PublishDate"][:10], "%Y-%m-%d").date()


def _doc_name(doc: dict) -> str:
    """Best-available document name (for the supplemental marker test)."""
    return doc.get("ConstructedName") or doc.get("FriendlyName") or ""


def _next_part_index(out_dir: Path, month: str) -> int:
    """Next free ``partNNNN`` index for a publication month, scanning disk."""
    existing = [
        int(p.name.split(".part")[1].split(".")[0])
        for p in out_dir.glob(f"{month}.part*.parquet")
    ]
    return max(existing, default=-1) + 1


def _write_part(df: pd.DataFrame, out_dir: Path, month: str) -> Path:
    """Write one member frame as the month's next part (raw string schema)."""
    part = _next_part_index(out_dir, month)
    path = out_dir / f"{month}.part{part:04d}.parquet"
    df.to_parquet(path, index=False, compression="zstd")
    return path


def _download_zip(doc: dict, tries: int = 3) -> bytes | None:
    """Download a document, re-requesting when the body is not a zip.

    The MIS occasionally serves an HTML error page with HTTP 200, which
    surfaces as ``BadZipFile`` only when the archive is opened — one bad body
    must not kill a multi-hour publication sweep. Returns ``None`` after
    ``tries`` bad bodies so the caller can record the document and continue.
    """
    import time
    import zipfile

    for attempt in range(tries):
        content = _get_with_retries(DOWNLOAD_URL, {"doclookupId": doc["DocID"]}).content
        try:
            _gen_member_names(content)
            return content
        except zipfile.BadZipFile:
            wait = 5 * (attempt + 1)
            print(
                f"    doc {doc['DocID']}: body is not a zip "
                f"({len(content)} bytes); retry in {wait}s",
                flush=True,
            )
            time.sleep(wait)
    return None


def fetch_corpus(
    pub_start: date,
    pub_end: date,
    out_dir: Path,
    manifest_path: Path,
    max_delivery: date,
) -> None:
    """Fetch the publication window into month shards, resumably.

    Ordinary documents are processed in publication-day order (latest publish
    wins a reposted day); supplementals afterwards, harvesting only Gen members
    for still-uncovered delivery days within the training window. The manifest
    records every written part (doc id, publication day, delivery day, rows,
    path) and is the resume index and the handoff's provenance table.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"parts": [], "skipped": [], "unreachable": []}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    covered: set[str] = {p["delivery_day"] for p in manifest["parts"]}

    def _save() -> None:
        manifest_path.write_text(json.dumps(manifest, indent=0))

    docs = _list_docs()
    ordinary: dict[date, dict] = {}
    supplemental: list[tuple[date, dict]] = []
    scan_hi = pub_end + timedelta(days=SUPPLEMENTAL_SCAN_EXTRA_DAYS)
    for doc in docs:
        pub = _pub_day(doc)
        if not (pub_start <= pub <= scan_hi):
            continue
        if "supplemental" in _doc_name(doc).lower():
            supplemental.append((pub, doc))
        elif pub <= pub_end:
            prior = ordinary.get(pub)
            if prior is None or doc["PublishDate"] > prior["PublishDate"]:
                ordinary[pub] = doc

    n_days = (pub_end - pub_start).days + 1
    listed = sorted(ordinary)
    print(
        f"{len(listed)}/{n_days} ordinary publication days listed in "
        f"[{pub_start}..{pub_end}]; {len(supplemental)} supplemental docs in "
        f"[{pub_start}..{scan_hi}]",
        flush=True,
    )
    missing_pubs = [
        pub_start + timedelta(days=i)
        for i in range(n_days)
        if (pub_start + timedelta(days=i)) not in ordinary
    ]
    for pub in missing_pubs:
        nominal = (pub - timedelta(days=PUBLICATION_LAG_DAYS)).isoformat()
        if nominal not in {u["nominal_delivery"] for u in manifest["unreachable"]}:
            manifest["unreachable"].append(
                {"publication": pub.isoformat(), "nominal_delivery": nominal}
            )

    def _harvest(pub: date, doc: dict, zip_bytes: bytes | None = None) -> None:
        """Write each wanted Gen member of one document as a month part."""
        if zip_bytes is None:
            zip_bytes = _download_zip(doc)
        if zip_bytes is None:
            manifest["skipped"].append(
                {
                    "doc": doc["DocID"],
                    "member": None,
                    "delivery": None,
                    "why": f"pub {pub}: persistently non-zip body (MIS error page)",
                }
            )
            print(f"  pub {pub}: SKIP doc {doc['DocID']} — persistently non-zip")
            _save()
            return
        names = _gen_member_names(zip_bytes)
        month = f"{pub.year:04d}-{pub.month:02d}"
        for name in sorted(names):
            days = _member_delivery_days(zip_bytes, name)
            key = ",".join(d.isoformat() for d in days)
            if any(d > max_delivery for d in days):
                manifest["skipped"].append(
                    {
                        "doc": doc["DocID"],
                        "member": name,
                        "delivery": key,
                        "why": f"delivery beyond --max-delivery-date {max_delivery}",
                    }
                )
                print(f"  pub {pub} {name}: SKIP (delivery {key} beyond window)")
                continue
            if all(d.isoformat() in covered for d in days):
                manifest["skipped"].append(
                    {
                        "doc": doc["DocID"],
                        "member": name,
                        "delivery": key,
                        "why": "delivery day(s) already covered",
                    }
                )
                continue
            df = _read_member(zip_bytes, name)
            path = _write_part(df, out_dir, month)
            covered.update(d.isoformat() for d in days)
            manifest["parts"].append(
                {
                    "path": path.name,
                    "doc": doc["DocID"],
                    "publication": pub.isoformat(),
                    "member": name,
                    "delivery_day": days[0].isoformat() if len(days) == 1 else key,
                    "rows": int(len(df)),
                    "bytes": path.stat().st_size,
                }
            )
            print(
                f"  pub {pub}: {len(df):,} rows (delivery {key}) -> {path.name}",
                flush=True,
            )
            _save()  # per member: a 32-member supplemental resumes mid-bundle
        _save()

    for pub in listed:
        nominal = pub - timedelta(days=PUBLICATION_LAG_DAYS)
        if nominal.isoformat() in covered:
            continue
        _harvest(pub, ordinary[pub])

    for pub, doc in sorted(supplemental, key=lambda t: t[0]):
        if any(s.get("doc") == doc["DocID"] for s in manifest["skipped"]):
            continue  # resumed run: this bundle already adjudicated memberless
        zip_bytes = _download_zip(doc)
        if zip_bytes is None:
            manifest["skipped"].append(
                {
                    "doc": doc["DocID"],
                    "member": None,
                    "delivery": None,
                    "why": f"supplemental pub {pub}: persistently non-zip body",
                }
            )
            _save()
            continue
        names = _gen_member_names(zip_bytes)
        if not names:
            manifest["skipped"].append(
                {
                    "doc": doc["DocID"],
                    "member": None,
                    "delivery": None,
                    "why": "supplemental carries no Gen Resource member",
                }
            )
            _save()
            continue
        print(f"supplemental pub {pub}: {len(names)} Gen member(s)", flush=True)
        _harvest(pub, doc, zip_bytes=zip_bytes)

    got = len(manifest["parts"])
    print(
        f"\n{got} part(s) on manifest; {len(manifest['skipped'])} member(s) "
        f"skipped; {len(manifest['unreachable'])} unlisted publication day(s)"
    )
    _save()


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pub-start", required=True, help="first publication day, YYYY-MM-DD"
    )
    ap.add_argument("--pub-end", required=True, help="last publication day, YYYY-MM-DD")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument(
        "--manifest",
        required=True,
        help="resume/provenance manifest JSON (kept OUTSIDE data/raw)",
    )
    ap.add_argument(
        "--max-delivery-date",
        default="2025-12-31",
        help="refuse members carrying deliveries beyond this date (rule 22 "
        "hygiene at the locked-test boundary)",
    )
    args = ap.parse_args()
    fetch_corpus(
        datetime.strptime(args.pub_start, "%Y-%m-%d").date(),
        datetime.strptime(args.pub_end, "%Y-%m-%d").date(),
        Path(args.out_dir),
        Path(args.manifest),
        datetime.strptime(args.max_delivery_date, "%Y-%m-%d").date(),
    )


if __name__ == "__main__":
    main()
