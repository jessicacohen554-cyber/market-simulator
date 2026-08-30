"""Fetch an ISO-NE SCC Monthly Report and derive the conventional-hydro extract.

The source is ISO-NE ISO Express -> Operations Reports -> **Seasonal Claimed
Capability** (the per-resource monthly listing of every participant generator
asset's summer/winter claimed capability):

    https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/seasonal-claimed-capability

The tree page is JS-driven; its listing is served by the
``docWidgetGetMore`` endpoint (``start`` + ``treenode`` parameters), which
resolves each month to a stable ``/static-assets/documents/<id>/scc_<month>_<year>.xlsx``
path. The workbook's ``SCC_Report_Current`` sheet carries one row per asset
with two five-column season blocks whose order is verified per-vintage against
the ``SCC_Report_Summary`` totals (the blocks are labelled in a merged header
row; this script re-derives the labels and cross-foots the workbook rather
than trusting column positions).

Deliverable (committed): ``data/raw/capacity-market/scc/neiso/scc_hydro_<season>_<YYYY-MM>.csv``
— the ACTIVE conventional-hydro asset extract (hydraulic-turbine unit types
HDP / HDR / HW / HL; type PS "Hydraulic Turbine - Reversible" = pumped storage
is EXCLUDED, a storage resource in this model), a faithful transcription of
the published per-asset values (rules 13/14: no fitting, no rescaling).

The class factor consumed by
``config/capacity_market.py::HYDRO_ACCREDITATION_CREDIT_BY_ISO["NEISO"]`` is
the printed ``sum(summer SCC)`` over the model's own accreditation basis
``model.capacity_evolution.adequacy.modelled_hydro_nameplate_mw("NEISO")``
(capx-S4, docs/handoffs/FINDING-capx-s4-neiso-hydro-2026-08-30.md). Re-derive
on a newer SCC vintage or EIA census (rule 23) — never on a residual.

Usage::

    python scripts/data/fetch_isone_scc_hydro.py                # latest report
    python scripts/data/fetch_isone_scc_hydro.py --month august --year 2026
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.cookiejar
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "data" / "raw" / "capacity-market" / "scc" / "neiso"

TREE_PAGE = (
    "https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/"
    "seasonal-claimed-capability"
)
LISTING_ENDPOINT = (
    "https://www.iso-ne.com/isoexpress/web/reports/download/docWidgetGetMore"
)

#: Market Rule 1 §III.1.5.1 hydraulic-turbine unit types that are CONVENTIONAL
#: hydro. ``PS`` (Hydraulic Turbine - Reversible) is pumped storage and is
#: deliberately absent — it is a storage resource in this model, not part of
#: the conventional-hydro accreditation pool.
CONVENTIONAL_HYDRO_UNIT_TYPES = frozenset({"HDP", "HDR", "HW", "HL"})

#: SCC_Report_Current column layout (0-indexed), verified against the header
#: row on every parse (the script fails loudly if the workbook changes shape).
COL = {
    "asset_id": 0,
    "name": 1,
    "status": 2,
    "unit_type": 3,
    "settlement_only": 4,
    "intermittent": 5,
    "dispatchable": 6,
    "scc_determination": 8,
    "state": 10,
    "load_zone": 11,
    "fuel": 12,
}
SEASON_BLOCKS = (19, 24)  # establish/seasonal/demo-date/SCC/effective per block
SCC_OFFSET = 3  # block start -> "SCC (MW)" column


def _opener() -> urllib.request.OpenerDirector:
    """Cookie-carrying opener bootstrapped with the isox_token session."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.open(TREE_PAGE, timeout=60).read()
    if not any(c.name == "isox_token" for c in jar):
        raise RuntimeError(
            "ISO Express session bootstrap failed: no isox_token cookie from "
            + TREE_PAGE
        )
    return opener


def list_reports(opener: urllib.request.OpenerDirector) -> list[dict]:
    """Return the SCC report listing (newest first), one dict per month."""
    url = (
        LISTING_ENDPOINT
        + "?"
        + urllib.parse.urlencode(
            {"start": 0, "treenode": "seasonal-claimed-capability"}
        )
    )
    req = urllib.request.Request(
        url,
        headers={"Referer": TREE_PAGE, "X-Requested-With": "XMLHttpRequest"},
    )
    return json.load(opener.open(req, timeout=60))["data"]


def fetch_workbook(
    opener: urllib.request.OpenerDirector, month: str | None, year: int | None
) -> tuple[str, bytes]:
    """Download the requested (or newest) SCC workbook; return (name, bytes)."""
    docs = list_reports(opener)
    if month and year:
        want = f"scc_{month.lower()}_{year}.xlsx"
        matches = [d for d in docs if d["path"].endswith("/" + want)]
        if not matches:
            raise SystemExit(
                f"{want} not in the first listing page "
                f"({[d['path'].rsplit('/', 1)[-1] for d in docs[:5]]}...)"
            )
        doc = matches[0]
    else:
        doc = docs[0]
    name = doc["path"].rsplit("/", 1)[-1]
    data = opener.open("https://www.iso-ne.com" + doc["path"], timeout=120).read()
    return name, data


def derive_hydro_extract(workbook: bytes) -> tuple[list[dict], dict]:
    """Parse the workbook -> (per-asset hydro rows, derivation summary)."""
    import openpyxl  # deferred: the only non-stdlib dependency

    wb = openpyxl.load_workbook(io.BytesIO(workbook), read_only=True)
    ws = wb["SCC_Report_Current"]
    rows = ws.iter_rows(values_only=True)
    season_row = next(rows)
    header = next(rows)
    if header[COL["asset_id"]] != "Asset ID" or header[COL["fuel"]] != "Fuel Type":
        raise SystemExit(f"SCC_Report_Current header changed shape: {header[:14]}")
    labels = {
        i: v for i, v in enumerate(season_row) if isinstance(v, str) and "Claimed" in v
    }
    if sorted(labels) != list(SEASON_BLOCKS):
        raise SystemExit(f"season blocks moved: {labels}")
    summer_block = next(i for i in SEASON_BLOCKS if "Summer" in labels[i])
    winter_block = next(i for i in SEASON_BLOCKS if "Winter" in labels[i])

    def num(v):
        return float(v) if isinstance(v, (int, float)) else 0.0

    extract, cross = [], {"summer": 0.0, "winter": 0.0, "sog_summer": 0.0}
    for row in rows:
        if row[COL["asset_id"]] is None:
            continue
        summer_scc = num(row[summer_block + SCC_OFFSET])
        winter_scc = num(row[winter_block + SCC_OFFSET])
        if row[COL["settlement_only"]] == "EMS":
            cross["summer"] += summer_scc
            cross["winter"] += winter_scc
        if row[COL["status"]] != "ACTIVE":
            continue
        if row[COL["unit_type"]] not in CONVENTIONAL_HYDRO_UNIT_TYPES:
            continue
        extract.append(
            {
                "asset_id": row[COL["asset_id"]],
                "name": row[COL["name"]],
                "unit_type": row[COL["unit_type"]],
                "settlement_only": row[COL["settlement_only"]],
                "intermittent": row[COL["intermittent"]],
                "dispatchable": row[COL["dispatchable"]],
                "scc_determination": row[COL["scc_determination"]],
                "state": row[COL["state"]],
                "load_zone": row[COL["load_zone"]],
                "fuel": row[COL["fuel"]],
                "summer_establish_mw": num(row[summer_block]),
                "summer_scc_mw": summer_scc,
                "winter_establish_mw": num(row[winter_block]),
                "winter_scc_mw": winter_scc,
            }
        )

    # Cross-foot the whole workbook against its own summary sheet so a silent
    # season-block or units change can never ship a wrong extract.
    summary = {
        r[0]: (num(r[1]), num(r[2]))
        for r in wb["SCC_Report_Summary"].iter_rows(values_only=True)
        if r and isinstance(r[0], str)
    }
    published = summary.get("Total EMS Generator Capability:")
    if published is None or abs(published[1] - cross["summer"]) > 0.01:
        raise SystemExit(
            f"summer cross-foot failed: derived {cross['summer']:.3f} vs "
            f"summary {published}"
        )
    return extract, {
        "n_assets": len(extract),
        "summer_scc_mw": round(sum(r["summer_scc_mw"] for r in extract), 3),
        "winter_scc_mw": round(sum(r["winter_scc_mw"] for r in extract), 3),
    }


def main() -> None:
    """Fetch, derive, write the committed CSV, and print the class factor."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--month", help="report month name, e.g. august")
    ap.add_argument("--year", type=int, help="report year, e.g. 2026")
    args = ap.parse_args()

    name, workbook = fetch_workbook(_opener(), args.month, args.year)
    sha = hashlib.sha256(workbook).hexdigest()
    extract, summary = derive_hydro_extract(workbook)

    stem = name.replace("scc_", "").replace(".xlsx", "")  # e.g. august_2026
    out = OUT_DIR / f"scc_hydro_{stem}.csv"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(extract[0]))
        writer.writeheader()
        writer.writerows(extract)

    print(f"source workbook : {name}  sha256={sha}")
    print(f"wrote           : {out.relative_to(REPO)}  ({summary['n_assets']} assets)")
    print(f"summer SCC total: {summary['summer_scc_mw']} MW")
    print(f"winter SCC total: {summary['winter_scc_mw']} MW")
    try:
        sys.path.insert(0, str(REPO / "src"))
        from market_sim.model.capacity_evolution.adequacy import (
            modelled_hydro_nameplate_mw,
        )

        basis = modelled_hydro_nameplate_mw("NEISO")
        print(
            f"class factor    : {summary['summer_scc_mw']} / {basis:.1f} = "
            f"{summary['summer_scc_mw'] / basis:.4f}  "
            "(HYDRO_ACCREDITATION_CREDIT_BY_ISO['NEISO'])"
        )
    except Exception as exc:  # data/raw hydro budget may be un-hydrated
        print(f"class factor    : basis unavailable in this checkout ({exc})")


if __name__ == "__main__":
    main()
