#!/usr/bin/env python3
"""Fetch the Helms (FERC P-2735) FLA Appendix B1 hydrology xlsx snapshot.

Retrieves the PUBLIC hourly Helms pumped-storage operations record — FERC
eLibrary accession 20240418-5301, transmittal file
``02_Helms FLA_P-2735_PUBLIC_Vol I_App B1 Hydrology.xlsx`` — into
``data/raw/ps-water-state/caiso/`` and writes a ``_snapshot.json`` manifest
recording the endpoint, request, retrieval timestamp, byte count and SHA-256.

The eLibrary SPA's ``filedownload`` URL serves the app shell, not the file;
the working public route is the web API the SPA itself calls:
``POST /eLibrarywebapi/api/File/DownloadP8File`` with
``{"fileidLst": [<fileId>], "Islegacy": false}``. The fileId below was
resolved from the ``Search/AdvancedSearch`` API for the accession's
transmittal list (see ``data/raw/ps-water-state/README.md``).

A FERC filing is immutable once posted, so a re-fetch should reproduce the
committed snapshot byte-identically; the manifest SHA-256 is the check.

Usage:
    python scripts/data/fetch_helms_ps_water_state.py [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.request
from pathlib import Path

from scripts.lib import ps_water_state as ps
from scripts.lib.clean_io import paths
from scripts.lib.ps_water_state.caiso import (
    ELIBRARY_DOWNLOAD_URL,
    HELMS_FLA_ACCESSION,
)

#: eLibrary fileId of the App B1 hydrology xlsx within accession 20240418-5301.
HELMS_APPB1_FILE_ID = "CFF7C81B-5BBF-CE68-8A75-8EF75D300000"

#: The committed snapshot's size is ~15.4 MB; anything this small is an error
#: page or an empty API reply, never the workbook.
MIN_WORKBOOK_BYTES = 1_000_000

#: xlsx files are ZIP containers and always start with this magic.
ZIP_MAGIC = b"PK"


def _download(file_id: str) -> bytes:
    """POST the eLibrary download API for one fileId and return the bytes."""
    request = urllib.request.Request(
        ELIBRARY_DOWNLOAD_URL,
        data=json.dumps({"fileidLst": [file_id], "Islegacy": False}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return response.read()


def fetch(out_dir: Path | None = None) -> Path:
    """Retrieve the snapshot and write the manifest; returns the xlsx path."""
    target = (
        Path(out_dir) if out_dir is not None else ps.raw_dir_for("CAISO", paths.RAW_DIR)
    )
    target.mkdir(parents=True, exist_ok=True)
    payload = _download(HELMS_APPB1_FILE_ID)
    if len(payload) < MIN_WORKBOOK_BYTES or not payload.startswith(ZIP_MAGIC):
        raise RuntimeError(
            f"eLibrary returned {len(payload)} bytes that are not an xlsx; "
            "refusing to overwrite the snapshot with a probable error page"
        )
    filename = "helms_fla_appb1_hydrology.xlsx"
    path = target / filename
    path.write_bytes(payload)
    manifest = {
        filename: {
            "url": ELIBRARY_DOWNLOAD_URL,
            "request_body": {"fileidLst": [HELMS_APPB1_FILE_ID], "Islegacy": False},
            "accession": HELMS_FLA_ACCESSION,
            "original_filename": (
                "02_Helms FLA_P-2735_PUBLIC_Vol I_App B1 Hydrology.xlsx"
            ),
            "plant": "HELMS",
            "retrieved_utc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    }
    (target / "_snapshot.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {path}  ({len(payload):,} bytes)")
    print(f"wrote {target / '_snapshot.json'}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="target directory (default: data/raw/ps-water-state/caiso)",
    )
    args = parser.parse_args(argv)
    fetch(out_dir=args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
