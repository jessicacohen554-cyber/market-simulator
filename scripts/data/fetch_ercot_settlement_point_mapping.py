#!/usr/bin/env python3
"""Fetch ERCOT's Settlement Points List and Electrical Buses Mapping (NP4-160-SG).

ERCOT MIS report **NP4-160-SG** (``reportTypeId=10008``, found in ERCOT's own
unauthenticated product catalog ``all-emil-items-search.json`` — the same
catalog ``scripts/data/fetch_ercot_as_reports.py`` verifies its report-type IDs
against). One small zip per network-model version carrying the **structural**
network crosswalks ERCOT publishes:

* ``Settlement_Points_*.csv`` — the station→area crosswalk. One row per
  electrical bus with ``SUBSTATION``, ``SETTLEMENT_LOAD_ZONE``,
  ``RESOURCE_NODE``, ``HUB``, ``VOLTAGE_LEVEL``, ``PSSE_BUS_NAME/NUMBER``.
* ``Resource_Node_to_Unit_*.csv`` — ``RESOURCE_NODE`` →
  ``UNIT_SUBSTATION`` + ``UNIT_NAME``, the generator-side spine.
* ``NOIE_Mapping_*.csv`` — physical load → NOIE → substation → electrical bus.
* ``CCP_Resource_Names_*.csv``, ``Hub_Name_AND_DC_Ties_*.csv`` — combined-cycle
  logical resource names, and the hub / DC-tie name list.

Why it is here (ERCOT-160): the ERCOT lever queue's item 7 (WP-B nodal
curtailment layer) is blocked on a *station→area crosswalk that does not exist
in-repo*, and item 8 part (c) wants a CT resource→plant crosswalk. This report
is ERCOT's own published answer to the ERCOT half of both — it resolves a
resource node to a substation and a substation to a load zone, leaving only
substation→EIA-plant as a judgement step.

**Vintage limit, stated because it constrains what may be concluded from this
file.** MIS retention for NP4-160-SG is ~31 days (``misDisplayDuration_i``:
31), so the free path serves only the CURRENT network-model version — there is
no 2023/2024/2025 vintage to fetch. Substation→zone assignments are structural
and change slowly, but a resource node commissioned or retired between the
backcast years and the fetched vintage will not line up, so any consumer must
report its own match rate against the target year rather than assume full
coverage. The fetched version stamp is preserved in the output filenames and
in ``VERSION.json``.

Run:
    python scripts/data/fetch_ercot_settlement_point_mapping.py
    python scripts/data/fetch_ercot_settlement_point_mapping.py --out-dir data/raw/ercot-network-model
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

DEFAULT_OUT_DIR = RAW_DATA_DIR / "ercot-network-model"

# Same unauthenticated legacy MIS endpoints as the other ERCOT fetchers.
DOC_LIST_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
DOWNLOAD_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"
REPORT_TYPE_ID = 10008  # NP4-160-SG
_TIMEOUT_S = 300


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


def list_versions() -> list[dict]:
    """Every NP4-160-SG document the MIS currently lists, newest first."""
    resp = _get_with_retries(DOC_LIST_URL, {"reportTypeId": REPORT_TYPE_ID})
    docs = [d["Document"] for d in resp.json()["ListDocsByRptTypeRes"]["DocumentList"]]
    docs.sort(key=lambda d: d["PublishDate"], reverse=True)
    return docs


def fetch_latest(out_dir: Path) -> list[Path]:
    """Fetch the newest listed version and write each member as CSV + a stamp."""
    docs = list_versions()
    if not docs:
        raise SystemExit("MIS listed no NP4-160-SG document — nothing to fetch")
    doc = docs[0]
    name = doc.get("ConstructedName") or doc.get("FriendlyName") or ""
    print(f"newest version: {doc['PublishDate']}  {name}")
    if len(docs) > 1:
        print(f"  ({len(docs)} versions listed; MIS retention is ~31 days)")

    resp = _get_with_retries(DOWNLOAD_URL, {"doclookupId": doc["DocID"]})
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    members: dict[str, dict] = {}
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".csv"):
                continue
            # Write the member's EXACT published bytes. ERCOT's Terms of Use
            # §5 permits redistribution "provided that the contents are not
            # modified" (docs/data-licensing.md §3), so this must not be a
            # pandas round-trip — parsing happens separately, for the stamp.
            raw = zf.read(member)
            leaf = Path(member).name
            path = out_dir / leaf
            path.write_bytes(raw)
            written.append(path)
            df = pd.read_csv(io.BytesIO(raw), dtype=str)
            members[leaf] = {
                "rows": int(len(df)),
                "columns": list(df.columns),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
            print(f"  wrote {leaf}  ({len(df):,} rows, {len(df.columns)} cols)")

    stamp = out_dir / "VERSION.json"
    stamp.write_text(
        json.dumps(
            {
                "report": "NP4-160-SG Settlement Points List and Electrical Buses Mapping",
                "reportTypeId": REPORT_TYPE_ID,
                "docId": doc["DocID"],
                "publishDate": doc["PublishDate"],
                "constructedName": name,
                "members": members,
                "retention_note": (
                    "MIS retention ~31 days: only the CURRENT network-model "
                    "version is reachable on the free path. No 2023-2025 "
                    "vintage exists to fetch; consumers must report their own "
                    "match rate against the target year."
                ),
            },
            indent=2,
        )
        + "\n"
    )
    written.append(stamp)
    print(f"  wrote {stamp.name}")
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument(
        "--list-only",
        action="store_true",
        help="print the listed versions and exit without downloading",
    )
    args = ap.parse_args()

    if args.list_only:
        for doc in list_versions():
            print(
                doc["PublishDate"],
                doc.get("ConstructedName") or doc.get("FriendlyName"),
                f"{int(doc['ContentSize']) / 1e6:.3f} MB",
            )
        return
    fetch_latest(Path(args.out_dir))


if __name__ == "__main__":
    main()
