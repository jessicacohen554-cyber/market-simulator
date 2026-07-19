#!/usr/bin/env python3
"""Fetch the new-build cost benchmark source documents (PDF, sha256-pinned).

Re-downloads the third-party cost reports behind
``data/raw/new-build-cost-benchmarks/benchmarks_2026.csv`` (see that datatype's
README for the full provenance table) and verifies each byte stream against the
sha256 recorded at the 2026-07-19 intake, so the transcribed benchmark rows stay
auditable against the exact documents they were read from. The PDFs are NOT
committed (binary, several MB each); this script is the reproducibility path
(CLAUDE.md rule 13 — a forward-regenerating source).

Optionally (``--to-markdown``, requires ``pdfplumber``) regenerates the full
page-marked markdown conversions the intake QA was performed against; the
committed ``md/`` copies are the QA'd artifacts (full text for the EMM/Lazard/
LCOE-report documents, key-table extracts for the 183-page S&L and 112-page
Brattle reports).

Sources that could NOT be fetched from this environment at intake
(``liftoff.energy.gov`` DNS-unreachable, ``pnnl.gov`` PDF endpoint bot-walled)
are intentionally absent here; their benchmark rows carry ``verified=0``.

Usage:
    python scripts/data/fetch_cost_benchmark_sources.py [--out-dir DIR]
    python scripts/data/fetch_cost_benchmark_sources.py --to-markdown
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT = REPO / "data" / "raw" / "new-build-cost-benchmarks" / "pdf"

# (filename, url, sha256-at-intake). A hash mismatch means the publisher
# replaced the document — record the new hash in a NEW intake commit alongside
# re-QA'd benchmark rows, never by silently editing benchmarks_2026.csv.
SOURCES: list[tuple[str, str, str]] = [
    (
        "capital_cost_AEO2025.pdf",
        "https://www.eia.gov/analysis/studies/powerplants/capitalcost/pdf/capital_cost_AEO2025.pdf",
        "ad9127130fece93d3c2d9e203fc0176fcfc5e4d4dccc61d6576107f2d2df96ec",
    ),
    (
        "EMM_Assumptions_AEO2026.pdf",
        "https://www.eia.gov/outlooks/aeo/assumptions/pdf/EMM_Assumptions.pdf",
        "ae21fcea7110c6efac978fa9bf28670998392e72959077f7a07d5aa3045e00bb",
    ),
    (
        "AEO2025_LCOE_report.pdf",
        "https://www.eia.gov/outlooks/aeo/electricity_generation/pdf/AEO2025_LCOE_report.pdf",
        "4a5651e1b1392541ffc648364d4afbbdef0e0049eed164b87b1bdacc3c51e68c",
    ),
    (
        "lazards-lcoeplus-june-2025.pdf",
        "https://www.lazard.com/media/uounhon4/lazards-lcoeplus-june-2025.pdf",
        "63a3376ad437bb2311be3384f568a8be6d3f4790c26771584b29e2e561376360",
    ),
    (
        "brattle-pjm-cone-2025.pdf",
        "https://www.pjm.com/-/media/DotCom/committees-groups/committees/mic/2025/20250411-special/item-1-02-revised-cone-report-final.pdf",
        "cf0e1805f81aa0691cef9fba8db7f7b0c082e090b21e3a77b3b34f4d02725588",
    ),
]

_UA = "Mozilla/5.0 (X11; Linux x86_64)"  # some hosts (lazard.com) bot-wall bare urllib


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


def to_markdown(pdf: Path, out_md: Path) -> None:
    """Regenerate the page-marked markdown conversion (QA convention)."""
    import pdfplumber  # optional dependency, only for --to-markdown

    with pdfplumber.open(pdf) as doc, open(out_md, "w") as fh:
        fh.write(f"# {pdf.stem} — full text extraction\n\n")
        fh.write(
            "Converted from PDF via pdfplumber for QA/QC. "
            "Page markers preserve source pagination.\n\n"
        )
        for i, page in enumerate(doc.pages, 1):
            fh.write(f"\n---\n\n## [page {i}]\n\n{page.extract_text() or ''}\n")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: download, verify, optionally re-convert."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--to-markdown", action="store_true")
    args = ap.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for name, url, expected in SOURCES:
        dest = args.out_dir / name
        print(f"fetching {name} ...")
        try:
            fetch(url, dest)
        except OSError as exc:
            print(f"  DOWNLOAD FAILED: {exc}")
            failures += 1
            continue
        got = sha256(dest)
        status = "OK" if got == expected else "SHA256 MISMATCH (document replaced?)"
        if got != expected:
            failures += 1
        print(f"  {dest.stat().st_size / 1e6:.1f} MB  sha256={got[:16]}…  {status}")
        if args.to_markdown and got == expected:
            md = args.out_dir / f"{dest.stem}.full.md"
            to_markdown(dest, md)
            print(f"  wrote {md}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
