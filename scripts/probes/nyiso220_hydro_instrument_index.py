"""nyiso-220 — WHICH INSTRUMENT governs WHICH quantity for each NYISO hydro plant?

nyiso-219 flagged, and deliberately asserted nothing about, a question that decides
which corpus a licence pull should even target: NYISO's two dominant hydro projects
are **international boundary-water** projects, so the instrument that actually binds
their water may be a **treaty / IJC order** rather than the FERC licence article.
Getting this wrong returns the wrong document for **71.4 % of the fleet's MW**.

This probe is the settled answer, built as a deterministic index rather than prose.
For every plant it records, **separately**, the instrument governing:

1. the **water entitlement** (how much water the plant may take), and
2. the **operating band** (the pool/headpond level range it must respect), and
3. the **conservation period** -- the horizon over which the instrument requires a
   total flow to be preserved, which is the quantity the hydro budget row's period
   length would be identified from (rule 21 ``[R-DOF]`` case 2, a *published
   categorical duration class*, zero fitted scalars).

**THE RESULT, stated so the index is readable without the finding:** for **both**
dominant projects and for **both** quantities, the governing instrument is an
international one -- **not** the FERC licence. nyiso-219's caution was correct.

* **Robert Moses Niagara (P-2216, 51.89 % of fleet MW)** -- entitlement by the 1950
  Niagara Diversion Treaty (a recurring *time-of-day schedule of instantaneous
  minimum flows* over the Falls, not a volumetric budget); operating band by the
  International Niagara Board of Control's 1993 Directive (revised 2017) over the
  Chippawa-Grass Island Pool. **NEITHER states any energy/volume conservation
  period**: verified mechanically against the full treaty text, which contains zero
  occurrences of ``elevation``, ``reservoir``, ``storage``, ``pondage``, ``forebay``,
  ``pool``, ``monthly``, ``weekly``, ``accounting`` or ``average``.
* **Robert Moses St. Lawrence (P-2000, 19.48 %)** -- entitlement by the IJC's
  2016 Supplementary Order of Approval and Regulation Plan 2014 (Bv7), on an
  approved **weekly** flow regulation plan; within-week variation by the Commission's
  **directive on peaking and ponding**. That directive states its conservation
  periods **explicitly and categorically**: peaking preserves the **daily** total,
  ponding preserves the **weekly** total.
* **Every other plant (28.62 % of fleet MW)** is on a domestic river, so its
  operating band lives in its **FERC licence article** -- and FERC document text is
  **not retrievable from this container** (``www.ferc.gov`` / ``cms.ferc.gov`` 403;
  eLibrary is an Angular SPA whose real API base ``/eLibraryWebAPI/api/`` responds
  but whose ``Search``/``Document`` controllers are absent).

ZERO LP. Nothing armed, no ``ScenarioConfig`` field, keeper untouched, no held-out
year spent. No period length is *chosen* or *swept* here -- rule 21 ``[R-DOF]``
case 3 and rule 1 ``[R-STRUCT]`` both forbid that, and this probe only records what
published instruments say.

Source (committed): ``results/calibration/_nyiso219_ferc_licence_index.csv``.
PRECOMMIT: ``results/calibration/PRECOMMIT-nyiso220-hydro-operating-ranges.md``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INDEX = REPO / "results" / "calibration" / "_nyiso219_ferc_licence_index.csv"
OUT_JSON = REPO / "results" / "calibration" / "_nyiso220_hydro_instrument_index.json"

# Water sources that are INTERNATIONAL BOUNDARY WATERS between the US and Canada.
# Membership is a geographic fact about the river, not a tuned list: these are the
# two reaches over which the 1909 Boundary Waters Treaty gives the IJC jurisdiction
# and over which the 1950 Niagara Treaty and the IJC's Lake Ontario-St. Lawrence
# Orders of Approval operate.
BOUNDARY_WATERS: dict[str, str] = {
    "niagara river": "NIAGARA",
    "st lawrence river": "ST_LAWRENCE",
}

# The instruments, each with the verbatim provision this index relies on. Every
# number here is QUOTED FROM A PUBLISHED DOCUMENT -- none is fitted, derived from a
# residual, or selected because it moves a criterion.
INSTRUMENTS: dict[str, dict[str, object]] = {
    "NIAGARA": {
        "entitlement_instrument": (
            "Treaty between the United States of America and Canada concerning the "
            "uses of the waters of the Niagara River, signed Washington 1950-02-27"
        ),
        "entitlement_provisions": [
            "Art. III -- available water = total Lake Erie outflow to the Welland "
            "Canal and Niagara River less domestic, sanitary and navigation use",
            "Art. IV -- no power diversion may reduce the flow over Niagara Falls "
            "below 100,000 cfs each day between 08:00 and 22:00 EST from Apr 1 to "
            "Sep 15, and between 08:00 and 20:00 EST from Sep 16 to Oct 31; below "
            "50,000 cfs at any other time",
            "Art. V -- all water in excess of the Art. IV scenic flow may be "
            "diverted for power",
            "Art. VI -- the waters made available for power are divided equally "
            "between the United States and Canada",
            "Art. VII -- the two designated representatives (the International "
            "Niagara Committee) ascertain, determine and record the amounts of "
            "water available and the amounts used for power diversions",
        ],
        "operating_band_instrument": (
            "International Niagara Board of Control 1993 Directive (revised 2017), "
            "governing the Chippawa-Grass Island Pool (CGIP)"
        ),
        "operating_band_provisions": [
            "operational long-term average CGIP level of 171.16 m (561.55 ft), "
            "IGLD 1985, maintained by the Power Entities (OPG and NYPA) through "
            "the International Niagara Control Works",
            "tolerances for the CGIP level as measured at the Material Dock gauge "
            "(numeric tolerance values are stated in the Directive itself, which "
            "is NOT reproduced in the semi-annual progress reports read here)",
            "maximum permissible accumulated deviation +/- 0.91 meter-months "
            "(measured accumulated deviation 1973-03-01 to 2023-08-31: "
            "0.13 meter-months)",
        ],
        # The load-bearing negative, verified mechanically rather than by summary.
        "conservation_period_hours": None,
        "conservation_period_note": (
            "NO energy or volume conservation period is stated by either "
            "instrument. The treaty's only temporal structure is a recurring "
            "time-of-day schedule of INSTANTANEOUS MINIMUM FLOW RATES over the "
            "Falls (Art. IV) -- a rate constraint, not a volumetric budget over a "
            "period. The CGIP Directive constrains a LEVEL to a long-term average "
            "with an accumulated-deviation tolerance in meter-months, which is a "
            "long-horizon level constraint rather than an energy budget. So NO "
            "licensed multi-day budget period is identified for this project."
        ),
        "verified_absent_terms": [
            "elevation",
            "reservoir",
            "storage",
            "pondage",
            "forebay",
            "pool",
            "monthly",
            "weekly",
            "accounting",
            "average",
        ],
        "sources": [
            "https://www.internationalwaterlaw.org/documents/regionaldocs/niagra1950.html",
            "https://ijc.org/sites/default/files/INBC_semi_annual_141_Final_Signed.pdf",
        ],
    },
    "ST_LAWRENCE": {
        "entitlement_instrument": (
            "International Joint Commission Supplementary Order of Approval "
            "2016-12-08, with Regulation Plan 2014 (release rules Bv7)"
        ),
        "entitlement_provisions": [
            "the Board sets flows from Lake Ontario through the Moses-Saunders and "
            "Long Sault Dams 'in accordance with the Order of Approval, normally as "
            "specified by the approved WEEKLY flow regulation plan and directives "
            "from the Commission'",
            "Plan 2014 is 'a set of release rules (algorithms) that produce an "
            "unambiguous release amount each week'",
            "J limit -- maximum change in flow from one week (quarter-month) to the "
            "next is 700 m3/s, or 1,420 m3/s if Lake Ontario is above 75.2 m and "
            "ice is not forming",
            "M limit -- maximum Seaway-season flow is limited to prevent the WEEKLY "
            "MEAN level of Lake St. Lawrence at Long Sault Dam falling below "
            "72.60 m (IGLD 1985)",
            "I limit -- the winter flow constraint prevents the river level at Long "
            "Sault falling lower than 71.8 m (IGLD 1985)",
        ],
        "operating_band_instrument": (
            "Commission directive on peaking and ponding; conditions specified in "
            "Addendum No. 3 to the Operational Guides for Regulation Plan 1958-D "
            "(IJC letter 1983-10-13 authorising OPG and NYPA; renewed 2016-11-04 "
            "for 2016-12-01..2021-11-30; renewed 2021-11-30 for "
            "2021-12-01..2026-11-30)"
        ),
        "operating_band_provisions": [
            "ILOSLRB glossary -- 'Peaking: variations in the hourly flows over the "
            "course of a day'",
            "ILOSLRB glossary -- 'Ponding: variation in the day-to-day flows over "
            "the course of a week'",
            "peaking 'lower[s] water flows ... during hours of low electrical "
            "demand ... so that flows may be increased during hours of high demand, "
            "WHILE STILL KEEPING THE TOTAL DAILY FLOW THE SAME as though a constant "
            "flow had passed through the turbines during the 24 hours'",
            "ponding 'lower[s] flows ... on days of low demand, typically weekends, "
            "so that flows may be increased on days of high demand, WHILE STILL "
            "KEEPING THE TOTAL WEEKLY FLOW THE SAME as though a constant flow had "
            "passed through the turbines during the seven days'",
            "peaking operations are curtailed when outflows exceed the "
            "7,930 m3/s (280,000 cfs) peaking threshold",
        ],
        # THE identification: a published categorical duration class, zero scalars.
        "conservation_period_hours": 168,
        "conservation_period_note": (
            "TWO NESTED conservation periods are stated explicitly and "
            "categorically by the governing directive: peaking preserves the TOTAL "
            "DAILY flow (24 h) and ponding preserves the TOTAL WEEKLY flow (168 h). "
            "The outer period -- the one a hydro budget row's period length "
            "corresponds to -- is therefore ONE WEEK, and it is stated in words by "
            "the instrument rather than converted from a volume. This is rule 21 "
            "[R-DOF] case 2 (a published categorical duration class) and carries "
            "ZERO fitted scalars."
        ),
        "verified_absent_terms": [],
        "sources": [
            "https://ijc.org/sites/default/files/2019-04/LOSLRB-Directive-2016.pdf",
            "https://legacyfiles.ijc.org/tinymce/uploaded/Plan2014_CompendiumReport_1.pdf",
            "https://www.ijc.org/sites/default/files/2019-08/ILOSLRB_SAR_Appendix.pdf",
            "https://ijc.org/sites/default/files/LOSLRB_SAR_136_final.pdf",
        ],
    },
    "DOMESTIC": {
        "entitlement_instrument": "FERC licence article (project-specific)",
        "entitlement_provisions": [],
        "operating_band_instrument": "FERC licence article (project-specific)",
        "operating_band_provisions": [],
        "conservation_period_hours": None,
        "conservation_period_note": (
            "NOT RETRIEVED. FERC document text is not reachable from this "
            "container: www.ferc.gov and cms.ferc.gov return 403 to a browser "
            "User-Agent (and to WebFetch); elibrary.ferc.gov serves an Angular SPA "
            "whose real API base /eLibraryWebAPI/api/ responds with genuine JSON "
            "but whose Search, Document and DocFamily controllers return 404, "
            "Docket and File returning only ASP.NET scaffold stubs. An "
            "organisation/edge 403 is reported, not worked around."
        ),
        "verified_absent_terms": [],
        "sources": [],
    },
}


def classify(water_source: str) -> str:
    """Return the instrument class governing a plant on ``water_source``.

    The two international boundary reaches are named in :data:`BOUNDARY_WATERS`;
    every other river is domestic and falls to its FERC licence.
    """
    return BOUNDARY_WATERS.get(water_source.strip().lower(), "DOMESTIC")


def main() -> int:
    """Build the instrument index and write it as deterministic JSON."""
    rows = list(csv.DictReader(INDEX.open()))
    fleet_mw = sum(float(r["nameplate_mw"] or 0.0) for r in rows)

    per_class: dict[str, dict[str, object]] = {}
    plants: list[dict[str, object]] = []
    for r in rows:
        mw = float(r["nameplate_mw"] or 0.0)
        cls = classify(r["water_source"])
        acc = per_class.setdefault(cls, {"plants": 0, "mw": 0.0})
        acc["plants"] = int(acc["plants"]) + 1  # type: ignore[arg-type]
        acc["mw"] = float(acc["mw"]) + mw  # type: ignore[arg-type]
        if cls != "DOMESTIC":
            plants.append(
                {
                    "plant_id": int(r["plant_id"]),
                    "plant_name": r["plant_name"],
                    "nameplate_mw": round(mw, 1),
                    "pct_fleet_mw": round(100.0 * mw / fleet_mw, 3),
                    "ferc_docket": r["ferc_docket"],
                    "water_source": r["water_source"],
                    "instrument_class": cls,
                    "pondage_hours_upper_bound_nid": float(
                        r["pondage_hours_upper_bound"]
                    ),
                }
            )

    payload = {
        "probe": "nyiso220_hydro_instrument_index",
        "question": (
            "which instrument governs which quantity -- FERC licence article vs "
            "treaty / IJC order -- for each NYISO hydro plant"
        ),
        "fleet_mw": round(fleet_mw, 1),
        "coverage_by_instrument_class": {
            cls: {
                "plants": v["plants"],
                "mw": round(float(v["mw"]), 1),
                "pct_fleet_mw": round(100.0 * float(v["mw"]) / fleet_mw, 3),
            }
            for cls, v in sorted(per_class.items())
        },
        "boundary_water_plants": sorted(plants, key=lambda p: -float(p["nameplate_mw"])),
        "instruments": INSTRUMENTS,
        "headline": (
            "For BOTH dominant projects (71.376 % of fleet MW) and for BOTH "
            "quantities -- water entitlement and operating band -- the governing "
            "instrument is INTERNATIONAL, not the FERC licence. A FERC-only pull "
            "would have returned the wrong document for 71.4 % of the fleet."
        ),
        "period_length_identified": {
            "ST_LAWRENCE": {
                "hours": 168,
                "basis": (
                    "published categorical duration class -- the IJC peaking-and-"
                    "ponding directive states that ponding preserves the total "
                    "WEEKLY flow and peaking preserves the total DAILY flow"
                ),
                "fitted_scalars": 0,
                "pct_fleet_mw": 19.483,
            },
            "NIAGARA": {
                "hours": None,
                "basis": (
                    "NONE. Neither the 1950 Treaty nor the INBC 1993 Directive "
                    "states an energy/volume conservation period, verified "
                    "mechanically against the full treaty text. The project's "
                    "intertemporal freedom is the measured 0.244 h forebay pondage "
                    "plus the Lewiston pumped-storage reservoir, which the model "
                    "already represents SEPARATELY as storage."
                ),
                "fitted_scalars": 0,
                "pct_fleet_mw": 51.893,
            },
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    print(f"wrote {OUT_JSON.relative_to(REPO)}")
    print(f"fleet MW {fleet_mw:.1f}")
    for cls, v in payload["coverage_by_instrument_class"].items():  # type: ignore[union-attr]
        print(f"  {cls:12s} {v['plants']:4d} plants  {v['mw']:8.1f} MW  {v['pct_fleet_mw']:6.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
