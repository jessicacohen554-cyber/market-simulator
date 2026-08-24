"""caiso-219 Phase-0: census CAISO's published sub-zonal deliverability record.

Surveys the ONE object class caiso-218 §D left open as the §F.3a
gen-pocket prerequisite — a citable Kern/Tehachapi collector EXPORT limit —
by parsing CAISO's annual "Transmission Capability Estimates" Attachment A
(the IRP input worksheet) into a normalized per-constraint census.

The census answers the rule-14 alignment question the fence requires:
each row carries the constraint's name, the affected resource locations, the
ON-PEAK / OFF-PEAK condition flag under which it binds, and the published
FCDS / EODS capability in MW. The verdict written from it
(FINDING-caiso219 §B/§C) is that these MW are an *accreditation headroom*
in a resource-weighted currency, never a flow rating — see the module's
`ALIGNMENT_NOTES`.

NO LP, no solve, nothing armed. Survey instrument only (rule 1 [R-STRUCT]
Phase-0; rule 13 [R-MEASURED] admissibility test applied in the FINDING).

Usage:
    python3 scripts/probes/_caiso219_deliverability_census.py \
        --out results/calibration/_caiso219_deliverability_census.json
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any

# CAISO library: "Transmission capability estimate inputs for CPUC integrated
# resource plan - Aug 29, 2024". Attachment A is the machine-readable table;
# the white paper is its methodology (output factors reproduced below).
ATTACHMENT_A_URL = (
    "https://www.caiso.com/documents/"
    "attachment-a-transmission-capability-estimates-for-use-in-the-cpuc-irp-process-v2024.xlsx"
)
WHITE_PAPER_URL = "https://www.caiso.com/documents/transmission-capability-estimates-white-paper-2024.pdf"

# White paper Table 3.1-1 / 3.1-2 — the resource output factors in which the
# capability MW below are denominated. THIS is the units misalignment: a
# capability MW is a resource-weighted accreditation quantity, not a flow MW.
ON_PEAK_OUTPUT_FACTORS = {"solar": {"PGE": 0.15, "SCE": 0.13, "SDGE": 0.06, "VEA": 0.08},
                          "wind": {"PGE": 0.50, "SCE": 0.48, "SDGE": 0.35, "VEA": 0.48}}
OFF_PEAK_OUTPUT_FACTORS = {"solar": {"SDGE": 0.79, "SCE": 0.79, "PGE": 0.77},
                           "wind": {"SDGE": 0.69, "SCE": 0.64, "PGE": 0.63},
                           "thermal": {"ALL": 0.0}}

ALIGNMENT_NOTES = [
    "CURRENCY: capability MW are denominated in the deliverability study's "
    "resource output factors (SCE solar 13% on-peak, 79% off-peak of nameplate), "
    "not in flow MW. A midday belly flow is ~nameplate; the on-peak number is ~6x off.",
    "SCOPE: the tables are headroom for ADDITIONAL queued generation. The existing "
    "operational fleet's already-banked deliverability is excluded by construction "
    "(2024 white paper: OTC generation deliverability was NOT added back), so a "
    "pocket EXPORT LIMIT (= existing deliverable output + headroom) cannot be "
    "recovered from the published number.",
    "NESTING: one resource location sits behind several overlapping constraints "
    "with different capabilities (Tehachapi: Antelope-Vincent 6149.1, Vincent-Lugo "
    "6733.2, Windhub 1333.6). The white paper warns capability is limited by two or "
    "more constraints crossing a zone and that nested zones share budgets, so no "
    "row maps onto a single model link.",
    "VINTAGE: the estimates include ISO-APPROVED-but-unbuilt upgrades and are an "
    "IRP planning input for forward portfolios - they do not describe the "
    "as-operated 2023-2025 grid the backcast solves.",
]

_HEADER_ROWS = 3  # title + two-tier header


def fetch(url: str, cache: Path) -> Path:
    """Download ``url`` into ``cache`` unless already present; return the path."""
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / url.rsplit("/", 1)[-1]
    if not dest.exists():
        with urllib.request.urlopen(url, timeout=120) as fh:  # noqa: S310
            dest.write_bytes(fh.read())
    return dest


def _num(value: Any) -> float | None:
    """Coerce a sheet cell to float, mapping 'N/A'/blank/text to None."""
    if isinstance(value, (int, float)):
        return round(float(value), 1)
    return None


def parse_census(xlsx: Path) -> list[dict[str, Any]]:
    """Parse Attachment A into one normalized record per named constraint.

    Section banner rows (an interconnection-area title with no data) become the
    ``area`` carried onto the constraint rows beneath them.
    """
    import openpyxl

    ws = openpyxl.load_workbook(xlsx, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(min_row=_HEADER_ROWS + 1, values_only=True))
    out: list[dict[str, Any]] = []
    area = ""
    for raw in rows:
        cells = ["" if c is None else c for c in raw]
        if not cells or not str(cells[0]).strip():
            continue
        name = str(cells[0]).strip()
        # A banner row names an interconnection area and carries no condition.
        if not str(cells[2] if len(cells) > 2 else "").strip():
            area = name
            continue
        condition = str(cells[2]).strip()
        out.append(
            {
                "area": area,
                "constraint": name,
                "affected_resource_location": " ".join(str(cells[1]).split()),
                "condition": condition,
                "binds_off_peak": "off-peak" in condition.lower(),
                "fcds_transmission_plan_capability_mw": _num(cells[3]),
                "fcds_incremental_adnu_mw": _num(cells[4]),
                "eods_transmission_plan_capability_mw": _num(cells[7]) if len(cells) > 7 else None,
                "eods_incremental_aopnu_mw": _num(cells[8]) if len(cells) > 8 else None,
                "wind_solar_area_designation": str(cells[11]).strip() if len(cells) > 11 else "",
            }
        )
    return out


def summarize(census: list[dict[str, Any]]) -> dict[str, Any]:
    """Roll the census up to the question §F.3a actually asks: which pockets bind off-peak."""
    by_area: dict[str, dict[str, Any]] = {}
    for row in census:
        stats = by_area.setdefault(row["area"], {"constraints": 0, "off_peak": 0, "off_peak_names": []})
        stats["constraints"] += 1
        if row["binds_off_peak"]:
            stats["off_peak"] += 1
            stats["off_peak_names"].append(row["constraint"])
    tehachapi = [r for r in census if "tehachapi" in r["affected_resource_location"].lower()]
    return {
        "by_area": by_area,
        "n_constraints": len(census),
        "n_off_peak": sum(1 for r in census if r["binds_off_peak"]),
        "tehachapi_constraints": [
            {"constraint": r["constraint"], "condition": r["condition"],
             "fcds_mw": r["fcds_transmission_plan_capability_mw"],
             "eods_mw": r["eods_transmission_plan_capability_mw"]}
            for r in tehachapi
        ],
        "tehachapi_any_off_peak": any(r["binds_off_peak"] for r in tehachapi),
    }


def main() -> None:
    """Fetch Attachment A, emit the census + off-peak rollup + alignment notes."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cache-dir", type=Path, default=Path("/tmp/caiso219-cache"))
    args = ap.parse_args()

    census = parse_census(fetch(ATTACHMENT_A_URL, args.cache_dir))
    payload = {
        "probe": "caiso-219 sub-zonal deliverability census (Phase-0 survey)",
        "sources": {"attachment_a": ATTACHMENT_A_URL, "white_paper": WHITE_PAPER_URL},
        "verdict": "NO gen-pocket EXPORT LIMIT is published; capability MW is "
                   "accreditation headroom, not a flow rating (see alignment_notes)",
        "alignment_notes": ALIGNMENT_NOTES,
        "on_peak_output_factors": ON_PEAK_OUTPUT_FACTORS,
        "off_peak_output_factors": OFF_PEAK_OUTPUT_FACTORS,
        "summary": summarize(census),
        "census": census,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    s = payload["summary"]
    print(f"constraints={s['n_constraints']} off_peak={s['n_off_peak']} -> {args.out}")
    print(f"tehachapi rows={len(s['tehachapi_constraints'])} any_off_peak={s['tehachapi_any_off_peak']}")
    for area, st in s["by_area"].items():
        print(f"  {area[:52]:52s} {st['off_peak']:2d}/{st['constraints']:2d} off-peak")


if __name__ == "__main__":
    main()
