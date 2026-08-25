"""miso-185 — the South FIRM-EXPORT EVIDENCE HUNT: E-0 seller set + E-1 EQR classification.

READ-ONLY vs the model. **No LP is solved and nothing here re-enters a solve
unless the frozen V-LANDS mapping fires** (rule 13 ``[R-MEASURED]``): every
number is a measurement of in-repo registries and publicly retrieved contract
records, written to a JSON record for the finding.

Everything below is frozen by
``results/calibration/PREREG-miso185-south-firm-export-evidence-hunt-2026-08-25.md``
(committed and pushed BEFORE any source was touched, commit 9b1b2b4).

Stages (PREREG section 2):
  E-0  the MISO-South jurisdictional seller set, from in-repo EIA-860 only:
       plants with Balancing Authority Code == MISO and State in {AR, LA, MS,
       TX}, joined to the operable-generator capacity and the owner table;
       operators and owners ranked by capacity. The named incumbents (the
       Entergy opcos, System Energy Resources, Cleco) are asserted present.
       Declared coverage bound: pure marketers with no South plant are OUT of
       the scope-by-seller query.
  E-1  FERC EQR filtered retrieval by seller + quarter (2023Q1-2025Q4),
       contracts + transactions, customers weighted to TVA; classification
       per PREREG section 3 (Q-A crosswalk / Q-B rule-13 firmness+term /
       Q-C cost). Implemented after the access route is established; every
       access probe's verdict is recorded in the finding.

Output: ``results/calibration/_miso185_firm_export_hunt.json``.

Run:
  uv run --no-project --with pyarrow,pandas,numpy --python 3.12 \
    python scripts/probes/_miso185_firm_export_hunt.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

EIA860 = REPO / "data" / "raw" / "eia-860"
OUT = REPO / "results" / "calibration" / "_miso185_firm_export_hunt.json"

# PREREG section 2 E-0: the MISO-South footprint filter (frozen).
SOUTH_STATES = {"AR", "LA", "MS", "TX"}

# PREREG section 2 E-0(a): the named incumbents asserted present (frozen).
NAMED_INCUMBENT_TOKENS = [
    "Entergy Arkansas",
    "Entergy Louisiana",
    "Entergy Mississippi",
    "Entergy Texas",
    "Entergy New Orleans",
    "System Energy Resources",
    "Cleco",
]


def stage_e0() -> dict:
    """E-0: enumerate MISO-South plants/owners/operators and rank by capacity."""
    plant = pd.read_parquet(
        EIA860 / "eia860_plant.parquet",
        columns=[
            "Utility ID",
            "Utility Name",
            "Plant Code",
            "Plant Name",
            "State",
            "Balancing Authority Code",
        ],
    )
    gen = pd.read_parquet(
        EIA860 / "eia860_generator_operable.parquet",
        columns=["Plant Code", "Generator ID", "Nameplate Capacity (MW)", "Status"],
    )
    owner = pd.read_parquet(
        EIA860 / "eia860_owner.parquet",
        columns=["Plant Code", "Generator ID", "Owner Name", "Percent Owned"],
    )

    south = plant[
        (plant["Balancing Authority Code"] == "MISO")
        & (plant["State"].isin(sorted(SOUTH_STATES)))
    ].copy()

    g = gen.merge(
        south[["Plant Code", "Plant Name", "State", "Utility ID", "Utility Name"]],
        on="Plant Code",
        how="inner",
    )
    g["cap_mw"] = pd.to_numeric(g["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0)

    # Operator ranking: the plant's filing utility (EIA-860 operator).
    op_rank = (
        g.groupby("Utility Name", as_index=False)["cap_mw"]
        .sum()
        .sort_values("cap_mw", ascending=False)
    )

    # Owner ranking: per-generator ownership shares where reported; generators
    # absent from the owner table are 100 % their operator's (EIA-860
    # convention: sole ownership is not re-listed), attributed to the operator.
    ow = g.merge(owner, on=["Plant Code", "Generator ID"], how="left")
    ow["pct"] = pd.to_numeric(ow["Percent Owned"], errors="coerce")
    sole = ow["Owner Name"].isna()
    ow.loc[sole, "Owner Name"] = ow.loc[sole, "Utility Name"]
    ow.loc[sole, "pct"] = 1.0
    # Percent Owned is a fraction in some vintages, a percent in others —
    # normalize by magnitude (values > 1.5 read as percents).
    big = ow["pct"] > 1.5
    ow.loc[big, "pct"] = ow.loc[big, "pct"] / 100.0
    ow["owned_mw"] = ow["cap_mw"] * ow["pct"].fillna(1.0)
    own_rank = (
        ow.groupby("Owner Name", as_index=False)["owned_mw"]
        .sum()
        .sort_values("owned_mw", ascending=False)
    )

    incumbents = {}
    hay = "\n".join(
        sorted(set(op_rank["Utility Name"]) | set(own_rank["Owner Name"].astype(str)))
    )
    for tok in NAMED_INCUMBENT_TOKENS:
        incumbents[tok] = tok.lower() in hay.lower()

    return {
        "n_south_plants": int(south["Plant Code"].nunique()),
        "south_cap_mw": float(g["cap_mw"].sum()),
        "by_state_cap_mw": {
            k: float(v) for k, v in g.groupby("State")["cap_mw"].sum().items()
        },
        "operators_by_cap_mw_top25": [
            {"name": r["Utility Name"], "cap_mw": round(float(r["cap_mw"]), 1)}
            for _, r in op_rank.head(25).iterrows()
        ],
        "owners_by_owned_mw_top25": [
            {"name": str(r["Owner Name"]), "owned_mw": round(float(r["owned_mw"]), 1)}
            for _, r in own_rank.head(25).iterrows()
        ],
        "named_incumbents_present": incumbents,
        "coverage_bound": (
            "scope-by-seller: pure marketers with no MISO-South plant are not "
            "enumerable from EIA-860 and are OUT of the E-1 seller-scoped "
            "query (PREREG section 2 E-0)"
        ),
    }


# --- E-1: the FERC EQR seller-quarter screen -------------------------------
#
# Access route (established 2026-08-25, recorded in the finding): the EQR
# Report Viewer's summary reports are served session-free from
#   https://eqrreportviewer.ferc.gov/Summary_Report.aspx
#     ?RptType={Company|Product|Region}&PeriodYear=Y&PeriodNumber=Q
#     &RespondentId=CID&SellerId=CID
# as small (~3-4 KB) PDFs. RptType=Company = "Energy Sales and Bookouts by
# Customer" (top-10 customers by revenue, with a coverage row); RptType=Region
# = "Energy Sales and Bookouts by Balancing Authority" (delivery-point BA).
# Together they screen, per seller-quarter, whether ANY energy sale was made
# to / delivered at a seam-pool counterparty. The Selective Filings full-CSV
# route is EMAIL-GATED (link mailed to a provided address) and is recorded
# UNREACHABLE for this environment; the summary-report route is the filtered
# EQR retrieval the PREREG's E-1 scopes, within the Q-C budget.
#
# Seller CID panel: E-0 jurisdictional sellers resolved against the viewer's
# own Q3-2025 seller list (captured in-session; CIDs verified period-stable).
EQR_URL = (
    "https://eqrreportviewer.ferc.gov/Summary_Report.aspx"
    "?RptType={rpt}&PeriodYear={y}&PeriodNumber={q}"
    "&RespondentId={cid}&SellerId={cid}"
)

SELLER_PANEL: dict[str, str] = {
    # name -> seller CID (viewer lbxSellerSum values, period-stable)
    "Entergy Arkansas, LLC": "6415267",
    "Entergy Louisiana, LLC": "6414346",
    "Entergy Mississippi, LLC": "6414204",
    "Entergy New Orleans, LLC": "6414201",
    "Entergy Texas, Inc.": "6414318",
    "Entergy Power, LLC": "6380696",
    "Entergy Services, LLC": "6257886",
    "System Energy Resources, Inc.": "6263676",
    "Cleco Power LLC": "6184836",
    "Cleco Cajun LLC": "6172319",
    "Louisiana Generating LLC": "6263601",
    "NRG Cottonwood Tenant LLC": "6177099",
    "Cottonwood Energy Company LP": "6262253",
    "NRG Business Marketing LLC": "6437612",
    "Plum Point Energy Associates, LLC": "6174189",
    "Carville Energy LLC": "6178448",
    "Bayou Cove Peaking Power, LLC": "6263589",
    "Arkansas Electric Cooperative Corporation": "6262892",
    "Cooperative Energy": "6447946",
    "Cooperative Energy Incorporated (An Electric Membership Corporation)": "6172334",
    # Reverse/seam screen (corroboration-class, PREREG E-6 level corroboration
    # + the E-1 marketer-bound check): the RTO itself and the pool-side
    # entities that appear in the EQR seller list.
    "Midcontinent Independent System Operator, Inc.": "6218844",
    "Tennessee Valley Authority": "6183191",
    "Associated Electric Cooperative, Inc.": "6321726",
    "Southeastern Power Administration": "6269001",
}

QUARTERS = [(y, q) for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)]

# PREREG section 3 Q-A pool: counterparties / delivery BAs of interest.
# Tokens are matched case-insensitively against extracted PDF text rows.
POOL_TOKENS = [
    "TENNESSEE VALLEY",
    "TVA",
    "SOUTHERN CO",
    "SOUTHERN COMPANY",
    "SOCO",
    "ALABAMA POWER",
    "GEORGIA POWER",
    "MISSISSIPPI POWER",
    "GULF POWER",
    "ASSOCIATED ELECTRIC",
    "AECI",
    "LOUISVILLE GAS",
    "KENTUCKY UTILITIES",
    "LG&E",
    "LGEE",
    "POWERSOUTH",
]


def _fetch_pdf(url: str, dest: Path, tries: int = 3) -> bool:
    """Fetch a summary-report PDF with retries; True iff a PDF landed."""
    import subprocess
    import time

    for attempt in range(tries):
        r = subprocess.run(
            ["curl", "-sS", "--max-time", "120", "-A", "Mozilla/5.0",
             url, "-o", str(dest)],
            capture_output=True,
        )
        if r.returncode == 0 and dest.exists():
            head = dest.read_bytes()[:8]
            if head.startswith(b"%PDF"):
                return True
        time.sleep(5 * (attempt + 1))
    return False


def _pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    try:
        return "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
    except Exception as exc:  # noqa: BLE001 - recorded, not raised
        return f"<<UNPARSEABLE: {exc}>>"


# Period IDs in the viewer's ddlReportPeriodSum, mapped in-session 2026-08-25.
PERIOD_IDS = {(2023, 1): "661", (2023, 2): "662", (2023, 3): "663", (2023, 4): "664",
              (2024, 1): "665", (2024, 2): "666", (2024, 3): "667", (2024, 4): "668",
              (2025, 1): "669", (2025, 2): "670", (2025, 3): "671", (2025, 4): "672"}

# Broadened seller-name token set for the per-period sweep (E-0 panel + the
# reverse/seam screen entities). Any seller whose viewer name matches enters
# that period's fetch set.
SELLER_NAME_RE = (
    r"entergy|cleco|system energy|louisiana generating|cottonwood|nrg |"
    r"plum point|carville|bayou cove|arkansas electric|cooperative energy|"
    r"south mississippi|midcontinent independent|tennessee valley|"
    r"associated electric|southeastern power"
)


def _period_seller_list(y: int, q: int) -> list[tuple[str, str]]:
    """One viewer session dance (type + period postbacks) -> that period's
    (CID, name) seller list. Seller CIDs are PERIOD-SPECIFIC (the defect the
    first sweep hit: a CID valid for one period renders other periods' report
    headers over an EMPTY body), so every period's list must be fetched."""
    import html as Hm
    import re as _re
    import time

    import requests

    url = "https://eqrreportviewer.ferc.gov/"
    pfx = ("TabContainerReportViewer$TabPanelReporting$TabContainerReports$"
           "TabPanelSummaryReports$")

    def hidden(doc: str) -> dict:
        f = {}
        for m in _re.finditer(
            r'<input type="hidden" name="([^"]+)"(?:[^>]*? value="([^"]*)")?[^>]*/?>',
            doc,
        ):
            f[m.group(1)] = Hm.unescape(m.group(2) or "")
        return f

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": url})
    r0 = s.get(url, timeout=120)
    time.sleep(2)
    f = hidden(r0.text)
    f[pfx + "ddlReportTypeSum"] = "1"
    f["__EVENTTARGET"] = pfx + "ddlReportTypeSum"
    r1 = s.post(url, data=f, timeout=300)
    time.sleep(2)
    f = hidden(r1.text)
    f[pfx + "ddlReportTypeSum"] = "1"
    f[pfx + "ddlReportPeriodSum"] = PERIOD_IDS[(y, q)]
    f["__EVENTTARGET"] = pfx + "ddlReportPeriodSum"
    r2 = s.post(url, data=f, timeout=300)
    time.sleep(2)
    m = _re.search(r'lbxSellerSum"[^>]*>(.*?)</select>', r2.text, _re.S)
    if not m:
        return []
    return [
        (v, Hm.unescape(t))
        for v, t in _re.findall(
            r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', m.group(1)
        )
    ]


def stage_e1(pdf_dir: Path) -> dict:
    """E-1 screen: per seller-quarter, customers + delivery BAs vs the pool.

    Two phases per quarter: (1) the viewer session dance to obtain that
    period's seller list and resolve the matched sellers' PERIOD-SPECIFIC
    CIDs; (2) session-free Summary_Report.aspx GETs (Company = energy sales
    and bookouts by customer, top-10 by revenue with a coverage row; Region =
    energy sales and bookouts by delivery-point Balancing Authority)."""
    import re as _re
    import time

    pdf_dir.mkdir(parents=True, exist_ok=True)
    out: dict = {
        "route": (
            "per-period seller-list dance + session-free Summary_Report.aspx "
            "GETs (PDF); seller CIDs are period-specific"
        ),
        "reports": {},
        "hits": [],
        "fetch_failures": [],
        "period_seller_matches": {},
    }
    for (y, q) in QUARTERS:
        sellers = _period_seller_list(y, q)
        matched = [
            (cid, nm)
            for cid, nm in sellers
            if _re.search(SELLER_NAME_RE, nm, _re.I)
        ]
        out["period_seller_matches"][f"{y}Q{q}"] = {
            "n_sellers_listed": len(sellers),
            "matched": [{"cid": c, "name": n} for c, n in matched],
        }
        for cid, name in matched:
            for rpt in ("Company", "Region"):
                key = f"{y}Q{q}_{cid}_{rpt}"
                dest = pdf_dir / f"{key}.pdf"
                if not dest.exists():
                    ok = _fetch_pdf(EQR_URL.format(rpt=rpt, y=y, q=q, cid=cid), dest)
                    time.sleep(0.6)
                    if not ok:
                        out["fetch_failures"].append(key)
                        continue
                text = _pdf_text(dest)
                up = text.upper()
                pool_rows = sorted({tok for tok in POOL_TOKENS if tok in up})
                body = _re.search(r"Low Price\n(.*?)\n\s*#\s*of Lines:", text, _re.S)
                body_txt = _re.sub(r"\n+", " | ", body.group(1).strip()) if body else ""
                rec = {
                    "seller": name,
                    "bytes": dest.stat().st_size,
                    "empty_body": (not body_txt) or body_txt.startswith("Top 10 Total"),
                    "pool_tokens_found": pool_rows,
                    "body": body_txt[:2000],
                }
                if rpt == "Company":
                    m = _re.search(r"Top 10% of Total\s*([0-9.]+)", text)
                    rec["top10_coverage_pct"] = float(m.group(1)) if m else None
                if pool_rows:
                    rec["raw_text"] = text
                    out["hits"].append(key)
                out["reports"][key] = rec
    return out


def main() -> None:
    rec: dict = {}
    if OUT.exists():
        rec = json.loads(OUT.read_text())
    if "e0_seller_set" not in rec:
        rec["e0_seller_set"] = stage_e0()
    e0 = rec["e0_seller_set"]
    print(
        f"E-0: {e0['n_south_plants']} MISO-South plants, "
        f"{e0['south_cap_mw']:.0f} MW; incumbents "
        f"{e0['named_incumbents_present']}"
    )
    if "--e1" in sys.argv:
        pdf_dir = REPO / "results" / "calibration" / "_miso185_eqr_pdfs"
        prior = rec.get("e1_eqr_screen")
        if prior is not None and "period_seller_matches" not in prior:
            # First sweep used one period's CIDs for every quarter; CIDs are
            # period-specific, so its non-2025Q3 rows rendered empty bodies.
            # Preserved for the record, superseded by the corrected sweep.
            rec["e1_v1_defective_period_cids"] = {
                "defect": (
                    "seller CIDs resolved from the 2025Q3 list were applied "
                    "to all 12 quarters; every non-2025Q3 report rendered "
                    "the requested header over an EMPTY body"
                ),
                "hits": prior.get("hits"),
                "n_reports": len(prior.get("reports", {})),
            }
        rec["e1_eqr_screen"] = stage_e1(pdf_dir)
        e1 = rec["e1_eqr_screen"]
        n = len(e1["reports"])
        hits = e1["hits"]
        print(f"E-1: {n} seller-quarter reports; POOL HITS: {len(hits)}")
        for h in hits:
            print("  HIT:", h, e1["reports"][h]["pool_tokens_found"])
        print("fetch failures:", len(e1["fetch_failures"]))
    OUT.write_text(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
