#!/usr/bin/env python3
"""Fetch / re-query the NRC source pages behind the nuclear-license-status registry.

The registry (``data/raw/nuclear-license-status/<iso>.csv``) is hand-curated from
PRIMARY NRC sources — the per-reactor info-finder license pages, the Subsequent
License Renewal (SLR) status list, the approved power-uprate list, and the initial
license-renewal list — plus state/licensee instruments for restarts and state
operating ceilings. Each unit row carries its own ``source_url`` (the specific
NRC info-finder page it was read from) so the per-unit citation is auditable.

This script re-queries the CONSOLIDATED NRC pages (the ones a re-verification pass
would re-read fleet-wide) and prints each page's current sha256. Those pages are
LIVING documents (NRC updates SLR/uprate status as applications move), so the
committed, immutable audit artifacts are the markdown snapshots under
``data/raw/nuclear-license-status/md/`` (their sha256 IS pinned in the datatype
README's re-query table). A changed live-page sha is a signal to refresh the md/
snapshot in a NEW intake commit alongside re-verified CSV rows — never by silently
editing an <iso>.csv row (CLAUDE.md rule 13 — a forward-regenerating source).

The NRC per-reactor info-finder pages (~59 URLs, one per unit) are NOT pinned here
— each unit's row already cites its own page in ``source_url``; re-query them
per-unit when a specific license date needs re-confirming.

Usage:
    python scripts/data/fetch_nuclear_license_status.py            # re-query + sha
    python scripts/data/fetch_nuclear_license_status.py --out-dir DIR
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT = REPO / "data" / "raw" / "nuclear-license-status" / "_requery"

# Consolidated NRC re-query pages. (label, url). These are living pages — the
# pinned audit artifacts are the md/ snapshots (README re-query table). A NEW
# unit or a status change surfaces here first; the per-unit info-finder pages
# cited in each CSV row are the authoritative per-license source.
SOURCES: list[tuple[str, str]] = [
    (
        "nrc-list-power-reactor-units",
        "https://www.nrc.gov/reactors/operating/list-power-reactor-units.html",
    ),
    (
        "nrc-subsequent-license-renewal",
        "https://www.nrc.gov/reactors/operating/licensing/renewal/subsequent-license-renewal.html",
    ),
    (
        "nrc-initial-license-renewal-applications",
        "https://www.nrc.gov/reactors/operating/licensing/renewal/applications.html",
    ),
    (
        "nrc-approved-power-uprates",
        "https://www.nrc.gov/reactors/operating/licensing/power-uprates/status-power-apps/approved-applications.html",
    ),
]

# A well-formed per-reactor info-finder URL is
# https://www.nrc.gov/info-finder/reactors/<slug> where <slug> is a short plant
# abbreviation + unit number (e.g. byro1, byro2, diab1). Documented here so a
# re-query session can reconstruct the per-unit citation URLs.
INFO_FINDER_TEMPLATE = "https://www.nrc.gov/info-finder/reactors/{slug}"

_UA = "Mozilla/5.0 (X11; Linux x86_64)"  # nrc.gov may bot-wall bare urllib


def fetch(url: str, dest: Path) -> None:
    """Download ``url`` to ``dest`` (User-Agent set; streams to disk)."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)


def sha256(path: Path) -> str:
    """Return the hex sha256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: re-download each consolidated NRC page, print sha256."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for label, url in SOURCES:
        dest = args.out_dir / f"{label}.html"
        print(f"re-querying {label} ...")
        try:
            fetch(url, dest)
        except OSError as exc:
            print(
                f"  FETCH FAILED (bot-walled? use a browser — MANUAL DOWNLOAD): {exc}"
            )
            failures += 1
            continue
        print(
            f"  {dest.stat().st_size / 1e3:.1f} kB  sha256={sha256(dest)[:16]}…  "
            f"(compare to the md/ snapshot in the README re-query table)"
        )
    if failures:
        print(
            f"\n{failures} source(s) unfetchable from this environment — the "
            "committed md/ snapshots remain the audit artifacts; refresh them "
            "with browser access at the next intake vintage."
        )
    return 0  # re-query is advisory; never fails the pipeline


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
