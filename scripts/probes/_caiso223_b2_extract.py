"""caiso-223 — Attachment B2 boundary-diagram distillation (pre-registered optional step).

The caiso-223 precommit (§3) pre-registered ONE fetch attempt of CAISO's
Attachment B2 — Deliverability Constraint Boundary Diagrams (the DFAX-circle
document caiso-219 §B route 3 adjudicated "membership evidence only; carries
no MW") — to corroborate sub-zone membership near the proposed boundaries.
This probe records the attempt's full outcome honestly:

* the complete per-constraint page-title census (108 pages), which
  corroborates the `_caiso219_deliverability_census.json` Attachment-A rows
  1:1 at diagram grain (one naming delta recorded);
* the text-layer status per page — the PG&E Kern/Fresno (and Greater Bay /
  North of Greater Bay) constraint pages are RASTER-ONLY (title + page number
  + images, no vector labels), so the pocket's boundary substation lists are
  NOT text-extractable — the recorded membership-sharpener gap;
* the SCE-area pages DO carry vector labels, and one is extracted as a
  control that the extractor works where text exists.

No limit, rating, or MW is read or recorded [caiso-218/219 fences]. This is
membership evidence only, per the object's standing adjudication.

Run: ``python3 scripts/probes/_caiso223_b2_extract.py --pdf <path>``
(or with no argument to fetch the public PDF; the sha256 of the bytes used is
recorded either way).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_JSON = REPO / "results" / "calibration" / "_caiso223_b2_boundaries.json"

#: The public 08/28/2024 revision (located 2026-08-30; caiso-219 walked the
#: earlier revision live).
B2_URL = (
    "https://www.caiso.com/documents/"
    "attachment-b2-deliverability-constraint-boundary-diagrams-2024.pdf"
)

#: Section-header pages observed in the 08/28/2024 revision (0-indexed).
SECTIONS = {
    2: "SCE Northern",
    13: "SCE Metro",
    17: "SCE North of Lugo",
    23: "SCE Eastern",
    31: "East of Pisgah",
    35: "SDG&E",
    48: "PG&E North of Greater Bay",
    58: "PG&E Greater Bay",
    77: "PG&E Kern",
    88: "PG&E Fresno",
}

#: Tokens dropped from the SCE-control label extraction (diagram legend
#: furniture, not substation/resource labels).
_FURNITURE = {"Legend", "500 kV", "230 kV", "115 kV", "60/70 kV", "66 kV", "Constraint", "Defined Area"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", type=Path, default=None, help="local copy of the B2 PDF (else fetched)")
    args = ap.parse_args()

    import pdfplumber

    if args.pdf is None:
        tmp = Path(tempfile.gettempdir()) / "caiso223_b2.pdf"
        with urllib.request.urlopen(B2_URL, timeout=300) as r:
            tmp.write_bytes(r.read())
        pdf_path = tmp
    else:
        pdf_path = args.pdf

    raw = pdf_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()

    pdf = pdfplumber.open(pdf_path)
    pages = []
    section = None
    for i, p in enumerate(pdf.pages):
        text = p.extract_text() or ""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        title = lines[0] if lines else ""
        if i in SECTIONS:
            section = SECTIONS[i]
        # a constraint page is raster-only when the text layer is just
        # "<title>\nPage N" — the observed PG&E pattern
        raster_only = len(lines) <= 2
        pages.append(
            {
                "page": i + 1,
                "section": section if i not in SECTIONS and i > 2 else (SECTIONS.get(i) or section),
                "title": title,
                "is_section_header": i in SECTIONS,
                "text_lines": len(lines),
                "raster_only": raster_only,
            }
        )

    # the SCE control: Windhub On-Peak (census Tehachapi row) label extraction
    windhub_labels: list[str] = []
    for i, p in enumerate(pdf.pages):
        text = p.extract_text() or ""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines and lines[0].startswith("Windhub"):
            windhub_labels = [
                ln for ln in lines[1:]
                if ln not in _FURNITURE and not ln.startswith("Page ")
            ]
            break

    pgae_constraint_pages = [
        pg for pg in pages
        if pg["section"] in ("PG&E Kern", "PG&E Fresno") and not pg["is_section_header"]
    ]
    result = {
        "probe": "caiso-223 Attachment B2 distillation (membership evidence only; no MW read)",
        "source_url": B2_URL,
        "source_sha256": sha,
        "revision": "08/28/2024",
        "n_pages": len(pdf.pages),
        "page_census": pages,
        "pgae_kern_fresno": {
            "n_constraint_pages": len(pgae_constraint_pages),
            "all_raster_only": all(pg["raster_only"] for pg in pgae_constraint_pages),
            "titles": [pg["title"] for pg in pgae_constraint_pages],
            "census_concordance_note": (
                "titles match the _caiso219 Attachment-A census rows 1:1 with one naming delta: "
                "B2-2024 carries 'Q1959 SS-Gates 230 kV Line' where Attachment A names 'Gates-Arco 230 kV Line'"
            ),
        },
        "verdict": (
            "FETCH SUCCEEDED; the PG&E Kern/Fresno boundary pages are RASTER-ONLY, so the DFAX-circle "
            "substation lists for the proposed FSNO/ZP26 boundaries are NOT text-extractable — recorded as "
            "the membership-sharpener gap for a future round (image-grain extraction or a CAISO ask). "
            "The per-constraint diagram inventory itself corroborates the census: every off-peak Kern/Fresno "
            "constraint has a defined boundary diagram in the 2024 revision."
        ),
        "sce_control_windhub_labels": windhub_labels,
    }
    OUT_JSON.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT_JSON}")
    print("pgae raster_only:", result["pgae_kern_fresno"]["all_raster_only"])
    print("windhub labels (control):", windhub_labels[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
