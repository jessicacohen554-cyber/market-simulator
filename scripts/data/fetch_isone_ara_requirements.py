"""Fetch the ISO-NE ARA-cycle requirement set and derive the committed extract.

The capx-S4b intake (rule 23 ``[R-FROZEN-DERIVE]``: re-derive on publication,
never on a residual). Three published ISO-NE sources make up one same-cycle
requirement set for the Capacity Commitment Periods the model anchors on:

1. **The ARA ICR filing** — "Installed Capacity Requirement, Hydro Quebec
   Interconnection Capability Credits and Other Related Values for the
   2026-2027 and 2027-2028 Capacity Commitment Periods for use in Annual
   Reconfiguration Auctions", FERC filing of 2025-11-21:

       https://www.iso-ne.com/static-assets/documents/100029/icr_for_aras.pdf

   Carries ICR / HQICC / Net ICR and the 50/50 summer peak (net of BTM PV)
   for **ARA 3 of CCP 2026-27** and **ARA 2 of CCP 2027-28** (filing pp.
   12-16, "Proposed Values and Demand Curves"). Its peak values embed the
   Passive Demand Response reconstitution adjustments the filing itself
   sources to the CELT report's §6.3 (testimony pp. 10-11).

2. **The 2026 CELT report** (published 2026-05-01) — sheet
   ``4.1 Summary of CSOs``: the demand-resource and import Capacity Supply
   Obligation totals per CCP at labelled auction vintages. Its CCP 2026/27
   column is labelled "Includes ARA 3 Results" — the same-cycle CSO
   companion of the filing's ARA-3 requirement values:

       https://www.iso-ne.com/static-assets/documents/100035/2026_celt.xlsx

3. **The 2025 CELT report** (published 2025-05-01) — the immediately prior
   vintage of the same sheet (CCP 2026/27 "Includes ARA 1 Results"), kept in
   the extract so the vintage ladder FCA-17 -> ARA 1 -> ARA 3 is on the
   committed record:

       https://www.iso-ne.com/static-assets/documents/100023/2025_celt.xlsx

Deliverable (committed): ``data/raw/capacity-market/icr-ara/neiso/
ara_requirement_values.csv`` — a faithful transcription of the published
values (rules 13/14: no fitting, no rescaling, zero free parameters). The
workbooks/PDF themselves are NOT committed (re-fetchable; identities pinned
by sha256 below and in the README).

The registry constants consumed from this extract
(``config/capacity_market.py``):

* ``PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]`` = Net ICR / peak - 1
* ``ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]`` = DR CSO / Net ICR
* ``ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"]`` = net import CSO

all three from the ARA-3 / CCP 2026-27 rows (the newest same-cycle
restatement of the CCP the model's capacity anchors are vintage-anchored to).
Re-derive when ISO-NE publishes a newer same-cycle set (the next ARA ICR
filing or CELT vintage, or the reformed prompt-schedule CCP 2028/29 values)
— never because a residual moved.

Usage::

    python scripts/data/fetch_isone_ara_requirements.py            # fetch + verify + write
    python scripts/data/fetch_isone_ara_requirements.py --check    # verify the committed CSV only
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "data" / "raw" / "capacity-market" / "icr-ara" / "neiso"
OUT_CSV = OUT_DIR / "ara_requirement_values.csv"

#: Pinned source identities (verified on every fetch; a mismatch means ISO-NE
#: re-published the document and the intake must be re-reviewed, not silently
#: re-derived).
SOURCES: dict[str, dict[str, str]] = {
    "icr_for_aras.pdf": {
        "url": "https://www.iso-ne.com/static-assets/documents/100029/icr_for_aras.pdf",
        "published": "2025-11-21",
        "sha256": "36c2bdf13d55a3ceda5edb00720df2426d6df90b5df0d7583a68ddeab2af139e",
    },
    "2026_celt.xlsx": {
        "url": "https://www.iso-ne.com/static-assets/documents/100035/2026_celt.xlsx",
        "published": "2026-05-01",
        "sha256": "f799af42cce1376cd4aaae71b77f3374a8612ff34e67c5a48de9106664e76980",
    },
    "2025_celt.xlsx": {
        "url": "https://www.iso-ne.com/static-assets/documents/100023/2025_celt.xlsx",
        "published": "2025-05-01",
        "sha256": "3c4ed6ac549b1b61e32935a2943b5ccb2b3befe4cc7da05f44eb735908e5d55c",
    },
}

#: The ARA ICR filing's "Proposed Values" tables (filing pp. 12 & 16),
#: transcribed. Cross-checked against the PDF text on every fetch when
#: ``pdftotext`` is available (the filing is a scanned-layout FERC PDF, so the
#: numbers are asserted present in the extracted text rather than re-parsed
#: positionally).
FILING_VALUES: dict[str, dict[str, float]] = {
    # CCP -> {metric: MW}; season is summer throughout (the filing's 50/50
    # peak is the summer forecast, net of BTM PV — same basis as the model's
    # EIA-930 demand, see PLANNING_RESERVE_MARGIN_BY_ISO's citation comment).
    "2026-2027 (ARA 3)": {
        "icr": 31_059.0,
        "hqicc": 1_009.0,
        "net_icr": 30_050.0,
        "peak_50_50_net_btm_pv": 26_648.0,
    },
    "2027-2028 (ARA 2)": {
        "icr": 30_896.0,
        "hqicc": 1_041.0,
        "net_icr": 29_855.0,
        "peak_50_50_net_btm_pv": 26_417.0,
    },
}

#: CELT ``4.1 Summary of CSOs`` cells to extract, keyed by workbook. Each
#: entry: (CCP column-header substring, ISO-total row label chain) resolved
#: from the sheet's own labels, never fixed positions.
CELT_CCP_COLUMNS: dict[str, list[str]] = {
    "2026_celt.xlsx": ["2026/2027 (FCA 17)", "2027/2028 (FCA 18)"],
    "2025_celt.xlsx": ["2026/2027 (FCA 17)", "2027/2028 (FCA 18)"],
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch(name: str, cache_dir: Path) -> bytes:
    """Download one pinned source (or reuse a hash-valid cached copy)."""
    spec = SOURCES[name]
    cached = cache_dir / name
    if cached.exists():
        data = cached.read_bytes()
        if _sha256(data) == spec["sha256"]:
            print(f"  {name}: cached copy verified ({len(data):,} bytes)")
            return data
    req = urllib.request.Request(
        spec["url"], headers={"User-Agent": "market-sim-intake"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    digest = _sha256(data)
    if digest != spec["sha256"]:
        raise SystemExit(
            f"{name}: sha256 mismatch — got {digest}, pinned {spec['sha256']}. "
            "ISO-NE re-published the document; re-review the intake before "
            "re-deriving (rule 23)."
        )
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    print(f"  {name}: fetched + verified ({len(data):,} bytes)")
    return data


def _verify_filing_text(pdf_bytes: bytes) -> None:
    """Assert the transcribed filing values appear in the PDF text (pdftotext)."""
    if shutil.which("pdftotext") is None:
        print(
            "  (pdftotext unavailable — filing text cross-check skipped; "
            "identity still pinned by sha256)"
        )
        return
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        text = subprocess.run(
            ["pdftotext", "-layout", tmp.name, "-"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    for ccp, metrics in FILING_VALUES.items():
        for metric, value in metrics.items():
            token = f"{value:,.0f}"
            if token not in text:
                raise SystemExit(
                    f"filing cross-check FAILED: {token} ({ccp} {metric}) "
                    "not found in the PDF text — the transcription table no "
                    "longer matches the published filing."
                )
    print(
        f"  icr_for_aras.pdf: all {sum(len(m) for m in FILING_VALUES.values())} "
        "transcribed values found in the PDF text"
    )


def _celt_cso_rows(xlsx_bytes: bytes, workbook_name: str) -> list[dict[str, object]]:
    """Extract the ISO-NE-total CSO aggregates from CELT sheet 4.1.

    Column blocks are located by their own CCP header labels (which carry the
    auction-vintage annotation, e.g. "Includes ARA 3 Results") and rows by
    their own label chain under "ISO New England Total" — never by position.
    """
    import openpyxl  # heavy import kept local (repo convention)

    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
    ws = wb["4.1 Summary of CSOs"]
    grid = [[c.value for c in row] for row in ws.iter_rows()]

    # Header row: the one whose cells contain the CCP labels.
    header_idx, header = next(
        (i, row)
        for i, row in enumerate(grid)
        if any(isinstance(v, str) and "(FCA" in v for v in row)
    )
    col_of: dict[str, tuple[int, str]] = {}
    for j, v in enumerate(header):
        if isinstance(v, str) and "(FCA" in v:
            for want in CELT_CCP_COLUMNS[workbook_name]:
                if want in v.replace("\n", " "):
                    # summer CSO is the label column itself; the vintage
                    # annotation ("Includes ... Results") rides in the label.
                    vintage = v.replace("\n", " ").split("Includes")[-1].strip()
                    col_of[want] = (j, f"Includes {vintage}")

    # ISO-total block starts at the "ISO New England Total" row.
    start = next(
        i
        for i, row in enumerate(grid)
        if any(isinstance(v, str) and v.strip() == "ISO New England Total" for v in row)
    )

    def _find(label_col_pairs: list[tuple[int, str]]) -> int:
        for i in range(start, min(start + 30, len(grid))):
            row = grid[i]
            if all(
                isinstance(row[c], str) and row[c].strip().rstrip() == want
                for c, want in label_col_pairs
            ):
                return i
        raise SystemExit(f"CELT 4.1 row not found: {label_col_pairs}")

    # Label columns: Resource Type is 1 right of the zone label, subtype 2 right.
    zone_col = next(
        j
        for j, v in enumerate(grid[start])
        if isinstance(v, str) and v.strip() == "ISO New England Total"
    )
    rt, st = zone_col + 1, zone_col + 2
    rows_wanted = {
        "active_dcr_cso": [(st, "TOTAL ACTIVE")],
        "passive_dcr_cso": [(st, "TOTAL PASSIVE")],
        "dcr_cso_total": [(rt, "DCR Total")],
    }
    net_import_idx = next(
        i
        for i, row in enumerate(grid[start:], start)
        if any(
            isinstance(v, str)
            and "Net Import Total" in v
            and "ISO NEW ENGLAND" in str(row[zone_col])
            for v in row
        )
    )

    published = SOURCES[workbook_name]["published"]
    out: list[dict[str, object]] = []
    for ccp, (col, vintage) in sorted(col_of.items()):
        for metric, pairs in rows_wanted.items():
            i = _find(pairs)
            for season, offset in (("summer", 0), ("winter", 1)):
                out.append(
                    dict(
                        source=workbook_name,
                        published=published,
                        ccp=ccp.split(" (")[0],
                        vintage=vintage,
                        metric=metric,
                        season=season,
                        value_mw=round(float(grid[i][col + offset]), 3),
                    )
                )
        for season, offset in (("summer", 0), ("winter", 1)):
            out.append(
                dict(
                    source=workbook_name,
                    published=published,
                    ccp=ccp.split(" (")[0],
                    vintage=vintage,
                    metric="net_import_cso",
                    season=season,
                    value_mw=round(float(grid[net_import_idx][col + offset]), 3),
                )
            )
    return out


def build_extract(cache_dir: Path) -> list[dict[str, object]]:
    """Fetch + verify all three sources and assemble the extract rows."""
    rows: list[dict[str, object]] = []

    print("fetching pinned sources:")
    pdf = _fetch("icr_for_aras.pdf", cache_dir)
    _verify_filing_text(pdf)
    for ccp, metrics in FILING_VALUES.items():
        ccp_name, auction = ccp.split(" (")
        for metric, value in metrics.items():
            rows.append(
                dict(
                    source="icr_for_aras.pdf",
                    published=SOURCES["icr_for_aras.pdf"]["published"],
                    ccp=ccp_name,
                    vintage=auction.rstrip(")"),
                    metric=metric,
                    season="summer",
                    value_mw=value,
                )
            )

    for wb_name in ("2026_celt.xlsx", "2025_celt.xlsx"):
        data = _fetch(wb_name, cache_dir)
        rows.extend(_celt_cso_rows(data, wb_name))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--check",
        action="store_true",
        help="re-derive and diff against the committed CSV (exit 1 on drift)",
    )
    ap.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "isone-ara-sources",
        help="where the (uncommitted) source documents are cached",
    )
    args = ap.parse_args(argv)

    rows = build_extract(args.cache_dir)
    fieldnames = [
        "source",
        "published",
        "ccp",
        "vintage",
        "metric",
        "season",
        "value_mw",
    ]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    content = buf.getvalue()

    if args.check:
        committed = OUT_CSV.read_text()
        if committed != content:
            print("DRIFT: committed extract no longer matches the re-derivation")
            return 1
        print(
            f"OK: {OUT_CSV.relative_to(REPO)} matches the re-derivation "
            f"({len(rows)} rows)"
        )
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.write_text(content)
    print(f"wrote {OUT_CSV.relative_to(REPO)} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
