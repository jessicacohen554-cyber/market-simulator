"""Fetch + sha256-pin the transmission-expansion registry's primary sources.

Re-downloads the pinned planning documents behind
``data/raw/transmission-expansion/*.csv`` into
``data/raw/transmission-expansion/md/`` and writes the verification table
``md/README-SOURCES.md`` (filename, sha256, size, status). PDFs are also
converted to page-marked markdown alongside (``--to-markdown``, pdfplumber) so
every transcribed number can be read back from a committed conversion — the
capacity-cost-grounding QA protocol
(``docs/handoffs/capacity-cost-grounding-2026-07.md`` §3).

Sources that the sandbox proxy bot-walls (or that require a browser) are
recorded as ``MANUAL DOWNLOAD NEEDED`` rows instead of being guessed — the
registry rows citing them remain valid (their numbers were transcribed from
the fetched-at-research-time pages listed per row in ``source_url``), but the
local pinned copy is outstanding until a browser-access session lands it.

Usage::

    PYTHONPATH=. python scripts/data/fetch_transmission_expansion_sources.py
    PYTHONPATH=. python scripts/data/fetch_transmission_expansion_sources.py --to-markdown
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = _ROOT / "data" / "raw" / "transmission-expansion"
MD_DIR = RAW_DIR / "md"

# (slug, url, what it grounds). Every APPLIED (nonzero-delta) registry row's
# primary document is listed; 0-delta documentation rows list their heaviest
# instrument. sha256 is computed at fetch time and recorded in
# md/README-SOURCES.md (re-running verifies drift).
SOURCES: tuple[tuple[str, str, str], ...] = (
    (
        "miso-lrtp-tranche1-report.pdf",
        "https://cdn.misoenergy.org/MTEP21%20Addendum-LRTP%20Tranche%201%20Report625790.pdf",
        "MISO Tranche 1 per-LRZ CIL deltas (Table 7-3) — grounds all lrtp-t1 rows",
    ),
    (
        "miso-lrtp-tranche21-factsheet.pdf",
        "https://cdn.misoenergy.org/LRTP%20Tranche%202.1%20Fact%20Sheet666573.pdf",
        "MISO Tranche 2.1 portfolio approval — grounds lrtp-t21 row",
    ),
    (
        "ercot-25rpg025-eastern-backbone.pdf",
        "https://www.ercot.com/files/docs/2025/12/01/14.1-25RPG025-Recommendation-765-kV-STEP-Eastern-Backbone-Project.pdf",
        "ERCOT 765 kV STEP Eastern Backbone board item — grounds step-backbone rows",
    ),
    (
        "ercot-25rpg022-western-loop.pdf",
        "https://www.ercot.com/files/docs/2025/12/01/14.2-25RPG022-Recommendation-Drill-Hole-to-Sand-Lake-to-Solstice-765-kV-Line-Project.pdf",
        "ERCOT 765 kV Western Loop board item",
    ),
    (
        "caiso-swip-north-decision-dec2023.pdf",
        "https://www.caiso.com/documents/decisiononsouthwestintertieprojectnorth-presentation-dec2023.pdf",
        "CAISO SWIP-North board decision (1,117.5 MW ISO entitlement) — grounds swip-north row",
    ),
    (
        "caiso-2025-2026-transmission-plan-decision.pdf",
        "https://www.caiso.com/documents/decision-on-iso-2025-2026-transmission-plan-presentation-may-2026.pdf",
        "CAISO 2025-26 TPP decision (Gates-Los Banos No. 3 series comp; Serrano-Del Amo-Mesa cancellation)",
    ),
    (
        "caiso-2023-2024-transmission-plan-decision.pdf",
        "https://www.caiso.com/documents/decisionon2023-2024transmissionplan-presentation-may2024.pdf",
        "CAISO 2023-24 TPP decision (Humboldt OSW package)",
    ),
    (
        "pjm-board-whitepaper-dec2023.ashx",
        "https://www.pjm.com/-/media/DotCom/committees-groups/committees/teac/2023/20231205/20231205-pjm-teac-board-whitepaper-december-2023.ashx",
        "PJM 2022 RTEP Window 3 approval (b3800) — grounds rtep-w3 rows",
    ),
    (
        "pjm-board-whitepaper-feb2025.pdf",
        "https://www.pjm.com/-/media/DotCom/committees-groups/committees/teac/2025/20250204/20250204-pjm-board-whitepaper-february-2025.pdf",
        "PJM 2024 RTEP Window 1 approval (b4000 Valley Link)",
    ),
    (
        "pjm-board-whitepaper-feb2026.pdf",
        "https://www.pjm.com/-/media/DotCom/committees-groups/committees/teac/2026/20260203/20260203-pjm-board-whitepaper-february-2026.pdf",
        "PJM 2025 RTEP Window 1 approval (Kammer-Juniata, Greentown-Teddy)",
    ),
    (
        "ercot-pbrp-study-jul2024.pdf",
        "https://www.rtoinsider.com/wp-content/uploads/2025/01/ERCOT-PB-Plan-Jul-24.pdf",
        "ERCOT Permian Basin Reliability Plan Study (2,105 MW import figure, Tables E.1/7.5/7.6) — mirror copy; primary lives on PUCT interchange 55718",
    ),
)


def _sha256(path: Path) -> str:
    """Hex sha256 of a file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _to_markdown(pdf_path: Path) -> Path | None:
    """Convert a PDF to page-marked markdown next to it (best effort)."""
    try:
        import pdfplumber
    except ModuleNotFoundError:
        print("  [skip md] pdfplumber not installed")
        return None
    out = pdf_path.with_suffix(".md")
    try:
        parts: list[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                parts.append(f"\n\n---\n\n## [page {i}]\n\n{page.extract_text() or ''}")
        out.write_text(
            f"# Converted from {pdf_path.name} (pdfplumber; verify numbers "
            f"against the pinned PDF)\n" + "".join(parts)
        )
        return out
    except Exception as exc:  # noqa: BLE001 — a bad PDF is a MANUAL row, not a crash
        print(f"  [md failed] {pdf_path.name}: {exc}")
        return None


def fetch(to_markdown: bool = False) -> int:
    """Download every source, pin sha256, write md/README-SOURCES.md."""
    MD_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[str] = []
    failures = 0
    for slug, url, grounds in SOURCES:
        dest = MD_DIR / slug
        status = "ok"
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            body = resp.content
            if len(body) < 10_000 and b"<html" in body[:2000].lower():
                raise RuntimeError("HTML challenge page, not the document")
            dest.write_bytes(body)
        except Exception as exc:  # noqa: BLE001 — record, never guess
            status = f"MANUAL DOWNLOAD NEEDED ({type(exc).__name__})"
            failures += 1
            print(f"[manual] {slug}: {exc}")
        if dest.is_file() and status == "ok":
            digest = _sha256(dest)
            size = dest.stat().st_size
            print(f"[ok] {slug}  {size:,} B  sha256={digest[:16]}…")
            if to_markdown and dest.suffix.lower() in (".pdf", ".ashx"):
                _to_markdown(dest)
        else:
            digest, size = "-", 0
        rows.append(
            f"| `{slug}` | {status} | {size:,} | `{digest}` | {grounds} | {url} |"
        )

    table = (
        "# transmission-expansion pinned sources\n\n"
        "Generated by `scripts/data/fetch_transmission_expansion_sources.py` — "
        "re-run to verify drift; `MANUAL DOWNLOAD NEEDED` rows are outstanding "
        "primaries (proxy/bot-walled), never transcribed from memory.\n\n"
        "| file | status | bytes | sha256 | grounds | url |\n"
        "|------|--------|-------|--------|---------|-----|\n" + "\n".join(rows) + "\n"
    )
    (MD_DIR / "README-SOURCES.md").write_text(table)
    print(f"\nwrote {MD_DIR / 'README-SOURCES.md'} ({failures} manual row(s))")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--to-markdown",
        action="store_true",
        help="also convert fetched PDFs to page-marked markdown (pdfplumber)",
    )
    args = ap.parse_args(argv)
    return fetch(to_markdown=args.to_markdown)


if __name__ == "__main__":
    sys.exit(main())
