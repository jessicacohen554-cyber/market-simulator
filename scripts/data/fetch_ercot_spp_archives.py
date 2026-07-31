#!/usr/bin/env python3
"""Fetch ERCOT annual Load-Zone/Hub settlement-point-price (SPP) archives.

Lands the two annual bundles the LMP scoring bench is built from into
``data/raw/lmp-data/ERCOT/``:

* ``DAMLZHBSPP_<year>.zip`` — MIS report **NP4-180-ER** "Historical DAM Load
  Zone and Hub Prices" (``reportTypeId=13060``): one hourly Day-Ahead Market
  settlement-point price row per settlement point per delivery hour.
* ``RTMLZHBSPP_<year>.zip`` — MIS report **NP6-785-ER** "Historical RTM Load
  Zone and Hub Prices" (``reportTypeId=13061``): the 15-minute Real-Time
  Market equivalent.

Both are *annual* postings (one zip per calendar year, republished as the year
fills), which is why they are reachable for the full 2010→current span —
unlike the daily ``60_Day_DAM_Disclosure`` bundles (``reportTypeId=13051``),
whose free ``IceDocListJsonWS`` doc list is a **rolling ~2.3-year retention
window** and therefore cannot reach 2018–2022 at all (see
``scripts/data/fetch_ercot_as_reports.py`` §retention caveat, and
``docs/holdout-data-equivalency-register-2026-07.md`` §ERCOT).

Same free, unauthenticated legacy MIS endpoints as
``scripts/data/fetch_ercot_as_reports.py`` and
``scripts/data/fetch_ercot_60day_gen_resource.py``:

    doc list :  https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=<ID>
    download :  https://www.ercot.com/misdownload/servlets/mirDownload?doclookupId=<docId>

**On-disk naming.** Files are written under the plain, year-keyed names
``{DAM,RTM}LZHBSPP_<year>.zip`` matching the five hand-downloaded 2023–2025
archives already committed at the ``data/raw/lmp-data/`` top level, so the
consumers' ``*DAMLZHBSPP_<year>*.zip`` globs resolve either layout. ERCOT's own
``ConstructedName``, ``DocID`` and publish timestamp are not discarded — they
are recorded per file in the sidecar manifest
``data/raw/lmp-data/ERCOT/spp-archive-provenance.json`` so every landed byte
traces back to its exact MIS posting.

**Immutability (repo rule: ``data/raw/`` is never modified in place).** An
existing on-disk archive is never overwritten: the default is to skip it and
report ``present``. ``--verify`` re-downloads to a temp buffer and compares
the sha256 instead of writing, which is how the byte-freeze on the committed
2023–2025 archives is proven.

Usage::

    # the 2026-07-31 out-of-training intake (rule 22, data-intake channel)
    python scripts/data/fetch_ercot_spp_archives.py --years 2018 2019 2020 2021 2022 2026

    # prove the committed in-sample archives are byte-identical to MIS
    python scripts/data/fetch_ercot_spp_archives.py --years 2023 2024 2025 --verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import LMP_DATA_DIR  # noqa: E402

DOC_LIST_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
DOWNLOAD_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"

# reportTypeId → on-disk file stem. NP4-180-ER / NP6-785-ER; verified against
# the doc lists (17 annual postings each, 2010..2026) on 2026-07-31.
REPORTS: dict[str, int] = {"DAMLZHBSPP": 13060, "RTMLZHBSPP": 13061}

DEFAULT_OUT_DIR = LMP_DATA_DIR / "ERCOT"
PROVENANCE_NAME = "spp-archive-provenance.json"
_TIMEOUT_S = 600


def _doc_list(report_type_id: int) -> list[dict]:
    """Return the MIS document list for one reportTypeId."""
    resp = requests.get(
        DOC_LIST_URL, params={"reportTypeId": report_type_id}, timeout=_TIMEOUT_S
    )
    resp.raise_for_status()
    payload = resp.json().get("ListDocsByRptTypeRes", {}).get("DocumentList", [])
    return [entry["Document"] for entry in payload if "Document" in entry]


def _index_by_year(docs: list[dict], stem: str) -> dict[int, dict]:
    """Map delivery year → newest document whose name ends ``<stem>_<year>.zip``.

    The annual archives are republished as a year fills (and occasionally
    re-posted after a settlement correction), so several documents can carry
    the same year; the newest publish date wins.
    """
    pattern = re.compile(rf"{stem}_(\d{{4}})\.zip$")
    best: dict[int, dict] = {}
    for doc in docs:
        name = doc.get("ConstructedName") or doc.get("FriendlyName") or ""
        match = pattern.search(name)
        if not match:
            continue
        year = int(match.group(1))
        if year not in best or doc.get("PublishDate", "") > best[year].get(
            "PublishDate", ""
        ):
            best[year] = doc
    return best


def _download_bytes(doc: dict) -> bytes:
    """Download one MIS document by DocID."""
    resp = requests.get(
        DOWNLOAD_URL, params={"doclookupId": doc["DocID"]}, timeout=_TIMEOUT_S
    )
    resp.raise_for_status()
    return resp.content


def fetch_archives(years: list[int], out_dir: Path, verify: bool = False) -> list[dict]:
    """Fetch (or verify) every ``{stem}_<year>.zip`` archive for ``years``.

    Returns one record per (stem, year) describing what happened: ``fetched``,
    ``present`` (already on disk, untouched), ``verified`` / ``MISMATCH``
    under ``--verify``, or ``absent`` when MIS has no posting for that year.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for stem, report_type_id in REPORTS.items():
        by_year = _index_by_year(_doc_list(report_type_id), stem)
        print(
            f"[{stem}] reportTypeId={report_type_id}: "
            f"{len(by_year)} annual postings, {min(by_year, default='-')}"
            f"..{max(by_year, default='-')}"
        )
        for year in years:
            doc = by_year.get(year)
            target = out_dir / f"{stem}_{year}.zip"
            if doc is None:
                print(f"  {stem}_{year}: ABSENT from MIS doc list")
                records.append({"stem": stem, "year": year, "status": "absent"})
                continue
            if target.exists() and not verify:
                print(f"  {stem}_{year}: present, left untouched")
                records.append({"stem": stem, "year": year, "status": "present"})
                continue
            blob = _download_bytes(doc)
            digest = hashlib.sha256(blob).hexdigest()
            record = {
                "stem": stem,
                "year": year,
                "constructed_name": doc.get("ConstructedName"),
                "doc_id": doc.get("DocID"),
                "publish_date": doc.get("PublishDate"),
                "bytes": len(blob),
                "sha256": digest,
                "report_type_id": report_type_id,
            }
            if verify and target.exists():
                local = hashlib.sha256(target.read_bytes()).hexdigest()
                record["status"] = "verified" if local == digest else "MISMATCH"
                record["local_sha256"] = local
                print(
                    f"  {stem}_{year}: {record['status']} "
                    f"({len(blob):,} B remote, {target.stat().st_size:,} B local)"
                )
            else:
                target.write_bytes(blob)
                record["status"] = "fetched"
                print(f"  {stem}_{year}: fetched {len(blob):,} B → {target}")
            records.append(record)
    return records


def _write_provenance(records: list[dict], out_dir: Path) -> None:
    """Merge this run's fetch records into the sidecar provenance manifest."""
    path = out_dir / PROVENANCE_NAME
    existing = json.loads(path.read_text()) if path.exists() else {}
    for record in records:
        if record["status"] not in {"fetched", "verified"}:
            continue
        existing[f"{record['stem']}_{record['year']}"] = {
            k: v for k, v in record.items() if k not in {"stem", "year"}
        }
    path.write_text(json.dumps(existing, indent=1, sort_keys=True) + "\n")
    print(f"provenance → {path} ({len(existing)} archives)")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", required=True)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="re-download and sha256-compare instead of writing (byte-freeze proof)",
    )
    args = parser.parse_args()

    records = fetch_archives(sorted(args.years), args.out_dir, verify=args.verify)
    _write_provenance(records, args.out_dir)
    mismatched = [r for r in records if r["status"] == "MISMATCH"]
    if mismatched:
        print(f"FAIL: {len(mismatched)} archive(s) differ from MIS", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
