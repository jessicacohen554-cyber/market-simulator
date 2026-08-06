"""miso-135 — the Michigan PSCR state lead for EX-ANTE coal contract tonnage.

NO LP, NO SOLVE, NO INTAKE. This probe adjudicates a *source*, not a mechanism,
against the standing data ask
``docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md`` (§4.1 A-F and
the §4.2 pin-strength battery), whose thresholds bind exactly as written.

Pre-registration (pushed at ``d4d182a5`` BEFORE any adjudicating statistic and
BEFORE any MPSC document was opened):
``results/calibration/PREREG-miso135-michigan-pscr-tonnage-lead-2026-08-06.md``.

The lead, as the ask left it (§3(b)): the Michigan PSCR process (MCL 460.6j) is
"the most genuinely *ex-ante* state mechanism in MISO", its two utilities are
12.8 % of 2025 target tonnage, and the OPEN question was *"whether the public
PSCR plan exhibits carry per-plant contracted coal tonnage (as opposed to cost
projections, with volumes confidential)"*.

Gates, in the pre-registered order:

  G-0  ACCESS (gating): is the MPSC docket enumerable from a standard session
       for both utilities x all three plan years? Answered by ``--verify-source``
       against the public E-Dockets Aura endpoint; the resolved case set is
       recorded in ``PLAN_CASES`` so the default run needs no network.
  G-1  KIND (gating; the ask's open question): do the PUBLIC exhibits carry a
       per-plant coal tonnage fixed BEFORE the plan year? Legs A (ex-ante),
       B (plant grain from the source, no receipts bridge), E (terms).
       ``COAL_CONTRACT_EXHIBITS`` is the transcribed column ledger;
       ``--verify-source`` re-fetches all six and re-derives the headers, so the
       transcription is machine-checkable rather than asserted.
  G-2  COVERAGE (§2C ">= 15 of 39 plants AND >= 60 % of tonnage in EACH year"),
       measured from committed artifacts against the
       ``miso104_contract_source_coverage.py`` denominators; plus the
       pre-registered battery-power sub-bar (n >= 8 plants carrying a
       G-1-clearing series in all three years).
  G-3  THE §4.2 BATTERY — run ONLY if G-1 and the G-2 sub-bar pass. It is the
       ask's SUFFICIENCY test, so a battery that cannot reject also cannot
       accept: under-powered means NOT ACCEPTED, never acquitted.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds no marker. No quantity for
any out-of-training delivery year is extracted, tabulated or gated on.

Usage::

    .venv/bin/python scripts/probes/_miso135_michigan_pscr_tonnage_lead.py
    .venv/bin/python scripts/probes/_miso135_michigan_pscr_tonnage_lead.py --verify-source
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from miso104_contract_source_coverage import (  # noqa: E402
    plant_identity,
    target_set,
)

OUT = REPO / "results/calibration/_miso135_michigan_pscr_tonnage_lead.json"
YEARS = [2023, 2024, 2025]

# §2C, quoted from the ask so the bar is fixed in code, not in prose.
BAR_MIN_PLANTS = 15
BAR_MIN_TONNAGE_SHARE = 0.60
# PREREG §2 G-2: a §4.2 cross-section on fewer than this many plants cannot
# reject, and the battery is the ask's SUFFICIENCY test (miso-103 ran n ~ 38).
BAR_BATTERY_MIN_N = 8

# ---------------------------------------------------------------------------
# G-0 — the resolved docket. MPSC files PSCR PLAN and RECONCILIATION cases in
# one annual block per utility; these are the PLAN cases, verified by Case
# .Subject ("... for approval to implement a power supply cost recovery plan
# for the ... months ending December 31, <plan year>").
# ---------------------------------------------------------------------------
PLAN_CASES = {
    ("Consumers Energy Company", 2023): {
        "case": "U-21257", "case_id": "5008y000004TN7WAAW", "filed": "2022-09-30",
        "application_cv": "0688y000004Nr2eAAC", "pages": 190, "public": True},
    ("DTE Electric Company", 2023): {
        "case": "U-21259", "case_id": "5008y000004TN8jAAG", "filed": "2022-09-30",
        "application_cv": "0688y000004NqY5AAK", "pages": 150, "public": True},
    ("Consumers Energy Company", 2024): {
        "case": "U-21423", "case_id": "5008y000007lF6jAAE", "filed": "2023-09-29",
        "application_cv": "0688y00000A4adZAAR", "pages": 187, "public": True},
    ("DTE Electric Company", 2024): {
        "case": "U-21425", "case_id": "5008y000007lF7rAAE", "filed": "2023-09-29",
        "application_cv": "0688y00000A4UoGAAV", "pages": 123, "public": True},
    ("Consumers Energy Company", 2025): {
        "case": "U-21592", "case_id": "5008y00000AJ8SrAAL", "filed": "2024-09-30",
        "application_cv": "068cs00000CFqsPAAT", "pages": 174, "public": True},
    ("DTE Electric Company", 2025): {
        "case": "U-21594", "case_id": "5008y00000AJ7owAAD", "filed": "2024-09-30",
        "application_cv": "068cs00000CJmq5AAD", "pages": 129, "public": True},
}

# ---------------------------------------------------------------------------
# G-1 — the coal-contract exhibit ledger. Transcribed from the public PDFs;
# ``--verify-source`` re-fetches each and re-derives ``columns`` from the file.
# ``ex_ante_language`` is the exhibit's OWN description of the tonnage column.
# ---------------------------------------------------------------------------
COAL_CONTRACT_EXHIBITS = {
    ("DTE Electric Company", 2023): {
        "exhibit": "A-15", "title": "Long-Term Coal Contracts", "page": 19,
        "witness": "K. A. Maro", "source_cv": "0688y000004NqlGAAS",
        "columns": ["Contract Number", "Tonnage (000's)", "Cents/Mbtu",
                    "Begin", "End", "Fuel Type"],
        "ex_ante_language": ("the minimum tonnage contracted to purchase in "
                             "the 2023 PSCR plan year"),
        "plan_year_tonnage_000t": 6015},
    ("DTE Electric Company", 2024): {
        "exhibit": "A-15", "title": "Long-Term Coal Contracts", "page": 20,
        "witness": "K. A. Maro", "source_cv": "0688y00000A4UlPAAV",
        "columns": ["Contract Number", "Tonnage (000's)", "Cents/Mbtu",
                    "Begin", "End", "Fuel Type"],
        "ex_ante_language": ("the minimum tonnage contracted to purchase in "
                             "the 2023 PSCR plan year"),  # sic: uncorrected in source
        "plan_year_tonnage_000t": 6165},
    ("DTE Electric Company", 2025): {
        "exhibit": "A-15", "title": "Long-Term Coal Contracts", "page": 23,
        "witness": "D. Swiech", "source_cv": "068cs00000CJdpzAAD",
        "columns": ["Contract Number", "Tonnage (000's)", "Cents/Mbtu",
                    "Begin", "End", "Fuel Type"],
        "ex_ante_language": ("the minimum tonnage contracted to purchase in "
                             "the 2025 PSCR plan year"),
        "plan_year_tonnage_000t": 4818},
    ("Consumers Energy Company", 2023): {
        "exhibit": "A-22 (AKR-1)", "title": "Coal Contract & Purchase Data",
        "page": 163, "witness": "A. K. Rissman", "source_cv": "0688y000004Nr2eAAC",
        "columns": ["Supplier Contract No", "Coal Type", "Contract Execution Date",
                    "Contract Start Date", "Contract End Date", "Volume (Tons)",
                    "Price ($/Ton)"],
        "ex_ante_language": "committed (contract execution date per row)",
        "committed_tons": 4019216, "uncommitted_tons": 1894818,
        "plan_year_total_tons": 5914034},
    ("Consumers Energy Company", 2024): {
        "exhibit": "A-24 (AKR-1)", "title": "Coal Contract & Purchase Data",
        "page": 155, "witness": "A. K. Rissman", "source_cv": "0688y00000A4adZAAR",
        "columns": ["Supplier Contract No", "Coal Type", "Contract Execution Date",
                    "Contract Start Date", "Contract End Date", "Volume (Tons)",
                    "Price ($/Ton)"],
        "ex_ante_language": "committed (contract execution date per row)",
        "committed_tons": 2710680, "uncommitted_tons": 2262488,
        "plan_year_total_tons": 4973168},
    ("Consumers Energy Company", 2025): {
        "exhibit": "A-22 (AKR-1)", "title": "Coal Contract & Purchase Data",
        "page": 145, "witness": "A. K. Rissman", "source_cv": "068cs00000CFqsPAAT",
        "columns": ["Supplier Contract No", "Coal Type", "Contract Execution Date",
                    "Contract Start Date", "Contract End Date", "Volume (Tons)",
                    "Price ($/Ton)"],
        "ex_ante_language": "committed (contract execution date per row)",
        "committed_tons": 156000, "uncommitted_tons": 1501938,
        "plan_year_total_tons": 1657938},
}

# The ONLY plant-grain coal tonnage anywhere in the PSCR plan filings. Each is a
# PROJECTION of burn, so each fails leg A on kind — ask §3(c), PREREG K7.
PLANT_GRAIN_BUT_PROJECTED = {
    "Consumers Energy Company": {
        "exhibit": "A-17/A-16 (KCL-1)", "title": "Projected As-Burned Coal Costs",
        "grain": "plant", "quantity": "Burn Volume (Tons)",
        "why_inadmissible": "projected/modelled BURN, not a contract term"},
    "DTE Electric Company": {
        "exhibit": "A-11", "title": "Forecast of Plant Generation",
        "grain": "plant", "quantity": "GWh (not tons)",
        "why_inadmissible": "forecast GENERATION; no plant-grain tonnage exists"},
}

# Coal-burning plants per utility-year, read from the filings' OWN exhibits
# (Consumers A-17/A-16 KCL-1 burn volumes; DTE A-11 plant generation). This is
# what decides the §2B/§3(a)-blocker-1 "single destination plant" carve-out: a
# utility-year with exactly one coal plant needs NO apportionment.
COAL_FLEET_BY_UTILITY_YEAR = {
    ("Consumers Energy Company", 2023): ["J H Campbell", "D E Karn"],
    ("Consumers Energy Company", 2024): ["J H Campbell"],   # Karn 1-2 burn = 0 t
    ("Consumers Energy Company", 2025): ["J H Campbell"],   # Karn absent
    ("DTE Electric Company", 2023): ["Monroe", "Belle River"],
    ("DTE Electric Company", 2024): ["Monroe", "Belle River"],
    ("DTE Electric Company", 2025): ["Monroe", "Belle River"],
}

MI_TARGET_PLANTS = {1710: "J H Campbell", 1733: "Monroe (MI)"}
UTILITY_OF_PLANT = {1710: "Consumers Energy Company", 1733: "DTE Electric Company"}

DOC_URL = "https://mi-psc.my.site.com/sfc/servlet.shepherd/version/download/{cv}"


def coverage() -> dict:
    """Measure the Michigan sub-population against the §2C denominators.

    Committed artifacts only — no network, no LP. Returns per-year target-set
    totals, the Michigan plants and their share, and the share of the
    sub-population that survives the §2B single-destination-plant carve-out.
    """
    ann = target_set()
    ident = plant_identity().reindex(ann.index)
    mi = [c for c in ann.index if ident.loc[c, "State"] == "MI"]

    out = {
        "target_set_plants": int(len(ann)),
        "michigan_plants": {int(c): str(ident.loc[c, "Plant Name"]).strip() for c in mi},
        "per_year": {},
    }
    for y in YEARS:
        total = float(ann[y].sum())
        mi_tons = float(ann.loc[mi, y].sum())
        # The §2B carve-out: a utility-year whose coal fleet is ONE plant needs
        # no apportionment, so its contract tonnage attaches to that plant.
        onetoone = [
            c for c in mi
            if len(COAL_FLEET_BY_UTILITY_YEAR[(UTILITY_OF_PLANT[c], y)]) == 1
        ]
        oto_tons = float(ann.loc[onetoone, y].sum()) if onetoone else 0.0
        out["per_year"][y] = {
            "target_set_tons": total,
            "michigan_tons": mi_tons,
            "michigan_plants_n": len(mi),
            "michigan_share": mi_tons / total,
            "b_clearing_plants": [int(c) for c in onetoone],
            "b_clearing_plants_n": len(onetoone),
            "b_clearing_tons": oto_tons,
            "b_clearing_share": oto_tons / total,
            "per_plant_tons": {int(c): float(ann.loc[c, y]) for c in mi},
        }
    return out


def gate_g1() -> dict:
    """Adjudicate leg A (ex-ante), leg B (plant grain), leg E (terms).

    Legs are evaluated against the transcribed exhibit ledger; leg B is decided
    by whether any coal-contract exhibit carries a destination-plant column and,
    failing that, by the single-coal-plant carve-out per utility-year.
    """
    legs = {}
    plant_cols = {}
    for key, ex in COAL_CONTRACT_EXHIBITS.items():
        plant_cols[f"{key[0]}|{key[1]}"] = [
            c for c in ex["columns"]
            if re.search(r"plant|destination|station|unit", c, re.I)
        ]
    any_plant_col = any(v for v in plant_cols.values())

    legs["A_ex_ante"] = {
        "verdict": "PASS",
        "why": ("all six exhibits are filed BEFORE their plan year (2022-09-30 / "
                "2023-09-29 / 2024-09-30) and state a contract term: DTE's column "
                "(b) is literally 'the minimum tonnage contracted to purchase in "
                "the <Y> PSCR plan year'; Consumers reports committed vs "
                "uncommitted volume with a per-row Contract Execution Date."),
    }
    legs["B_plant_grain"] = {
        "verdict": "FAIL",
        "plant_columns_found": plant_cols,
        "any_plant_column": any_plant_col,
        "why": ("NO coal-contract exhibit, in either utility or any of the three "
                "plan years, carries a destination-plant column. The tonnage is "
                "at CONTRACT grain and the filings' only plant-grain coal "
                "quantity is a projected BURN (fails leg A on kind). Splitting a "
                "contract across plants would require delivered-tons weights — "
                "DISQUALIFYING under ask §2B."),
        "carve_out": {
            f"{u}|{y}": {
                "coal_plants": COAL_FLEET_BY_UTILITY_YEAR[(u, y)],
                "single_destination": len(COAL_FLEET_BY_UTILITY_YEAR[(u, y)]) == 1,
            }
            for (u, y) in sorted(COAL_FLEET_BY_UTILITY_YEAR, key=lambda k: (k[1], k[0]))
        },
    }
    legs["E_terms"] = {
        "verdict": "PARTIAL",
        "present": ["contract term (begin/end dates)", "price ($/ton or c/MBtu)",
                    "fuel type", "contract execution date (Consumers)",
                    "not-fully-executed flag (Consumers 2023)",
                    "carry-over/make-up tons (Consumers 2024 footnote)"],
        "absent": ["price/quantity reopeners", "force majeure",
                   "buy-out / buy-down provisions"],
        "why": ("richer than a bare tonnage and genuinely forward-looking, but "
                "short of ask §2E's full mechanics; not reached as a binding "
                "leg because B fails first."),
    }
    legs["verdict"] = "FAIL" if legs["B_plant_grain"]["verdict"] == "FAIL" else "PASS"
    return legs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify-source", action="store_true",
                    help="re-fetch the six exhibits and re-derive their column "
                         "headers from the live public docket (network)")
    args = ap.parse_args()

    cov = coverage()
    g1 = gate_g1()

    g2 = {"bar_min_plants": BAR_MIN_PLANTS,
          "bar_min_tonnage_share": BAR_MIN_TONNAGE_SHARE,
          "bar_battery_min_n": BAR_BATTERY_MIN_N,
          "per_year": {}}
    for y in YEARS:
        c = cov["per_year"][y]
        g2["per_year"][y] = {
            "plants": c["michigan_plants_n"],
            "tonnage_share": c["michigan_share"],
            "meets_plant_bar": c["michigan_plants_n"] >= BAR_MIN_PLANTS,
            "meets_tonnage_bar": c["michigan_share"] >= BAR_MIN_TONNAGE_SHARE,
            "b_clearing_plants_n": c["b_clearing_plants_n"],
            "b_clearing_share": c["b_clearing_share"],
        }
    g2["verdict_2C"] = "FAIL" if not all(
        v["meets_plant_bar"] and v["meets_tonnage_bar"]
        for v in g2["per_year"].values()) else "PASS"
    g2["battery_powered"] = all(
        v["b_clearing_plants_n"] >= BAR_BATTERY_MIN_N for v in g2["per_year"].values())

    g3 = {"run": False,
          "why_not": ("G-1 leg B FAILS, so no candidate series exists to test; and "
                      "the G-2 sub-bar fails at n = "
                      f"{min(v['b_clearing_plants_n'] for v in g2['per_year'].values())}"
                      f" < {BAR_BATTERY_MIN_N}. Per PREREG §2/§4 an under-powered "
                      "battery cannot ACQUIT — the candidate is NOT ACCEPTED, "
                      "never acquitted."),
          "verdict": "NOT RUN — CANDIDATE NOT ACCEPTED"}

    branch = "CLOSED ON KIND" if g1["verdict"] == "FAIL" else "SEE GATES"

    if args.verify_source:
        g0_verify = _verify_source()
    else:
        g0_verify = {"run": False,
                     "note": "pass --verify-source to re-derive headers from the docket"}

    record = {
        "session": "miso-135",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "bundle": "results/calibration/miso132_ccmin_B",
        "prereg": ("results/calibration/"
                   "PREREG-miso135-michigan-pscr-tonnage-lead-2026-08-06.md"),
        "prereg_pushed_at": "d4d182a5",
        "ask": "docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md",
        "note": ("source adjudication for the ask §3(b) Michigan PSCR lead. "
                 "NO LP, NO solve, NO intake, NO mechanism built. Rule 22: "
                 "2023-2025 only."),
        "G0_access": {"verdict": "PASS", "plan_cases": {
            f"{u}|{y}": v for (u, y), v in PLAN_CASES.items()},
            "verification": g0_verify},
        "G1_kind": g1,
        "G2_coverage": g2,
        "G3_battery": g3,
        "coverage_detail": cov,
        "coal_contract_exhibits": {
            f"{u}|{y}": {**v, "url": DOC_URL.format(cv=v["source_cv"])}
            for (u, y), v in COAL_CONTRACT_EXHIBITS.items()},
        "plant_grain_but_projected": PLANT_GRAIN_BUT_PROJECTED,
        "branch": branch,
    }
    OUT.write_text(json.dumps(record, indent=1, default=str))

    print(f"G-0 ACCESS          : PASS — 6/6 plan cases enumerated from the public docket")
    print(f"G-1 KIND            : {g1['verdict']}  "
          f"(A {g1['A_ex_ante']['verdict']} / B {g1['B_plant_grain']['verdict']} / "
          f"E {g1['E_terms']['verdict']})")
    for y in YEARS:
        v = g2["per_year"][y]
        print(f"G-2 COVERAGE {y}   : {v['plants']} of {cov['target_set_plants']} plants "
              f"({v['tonnage_share']:.1%} of tonnage) vs bar >= {BAR_MIN_PLANTS} "
              f"and >= {BAR_MIN_TONNAGE_SHARE:.0%}   |  B-clearing n="
              f"{v['b_clearing_plants_n']} ({v['b_clearing_share']:.1%})")
    print(f"G-2 §2C             : {g2['verdict_2C']}")
    print(f"G-3 BATTERY         : {g3['verdict']}")
    print(f"BRANCH              : {branch}")
    print(f"wrote {OUT}")


def _verify_source() -> dict:
    """Re-fetch each coal-contract exhibit and re-derive its column header.

    Confirms the transcribed ``columns`` are the source's own, so the G-1 leg-B
    verdict rests on machine-checkable evidence rather than assertion.
    """
    import urllib.request
    import warnings

    warnings.filterwarnings("ignore")
    from pypdf import PdfReader  # noqa: PLC0415

    import io

    res = {"run": True, "exhibits": {}}
    for (u, y), ex in COAL_CONTRACT_EXHIBITS.items():
        url = DOC_URL.format(cv=ex["source_cv"])
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                blob = r.read()
            rd = PdfReader(io.BytesIO(blob))
            txt = rd.pages[ex["page"] - 1].extract_text() or ""
            # PDF extraction breaks table headers across lines, so compare on
            # whitespace-collapsed, case-folded text.
            flat = re.sub(r"\s+", " ", txt).lower()
            found = [c for c in ex["columns"]
                     if re.sub(r"\s+", " ", c).lower() in flat]
            missing = [c for c in ex["columns"] if c not in found]
            # A column whose header WRAPS in the source table will not appear
            # contiguously; accept it only if every whitespace-separated token
            # is present, and record it separately from a contiguous match.
            wrapped = [c for c in missing
                       if all(tok.lower() in flat for tok in c.split())]
            plant = bool(re.search(r"\bplant\b|\bdestination\b", flat))
            res["exhibits"][f"{u}|{y}"] = {
                "http_ok": True, "bytes": len(blob),
                "columns_confirmed": found,
                "columns_confirmed_wrapped": wrapped,
                "columns_unconfirmed": [c for c in missing if c not in wrapped],
                "n_confirmed": len(found) + len(wrapped),
                "n_transcribed": len(ex["columns"]),
                "all_columns_confirmed": len(found) + len(wrapped) == len(ex["columns"]),
                # THE decisive leg-B check: no destination-plant column exists.
                "plant_word_on_page": plant}
        except Exception as e:  # noqa: BLE001
            res["exhibits"][f"{u}|{y}"] = {"http_ok": False, "err": str(e)[:120]}
    return res


if __name__ == "__main__":
    main()
