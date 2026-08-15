"""Write ``calibration_attestation.json`` for the nyiso-98 PROMOTED arm.

``2026-07-29-nyiso-98-nucavail`` (``results/calibration/nyiso98_nucavail``)
was registered as a gate-passing, KEEPER-RECOMMENDED arm and the promotion was
surfaced to the owner rather than taken by the building session (the NYISO
lane convention since nyiso-96). The OWNER PROMOTED IT on 2026-07-29
(AskUserQuestion, this session). This script builds the C6 attestation the
promotion requires (rule 21 [R-DOF]: every keeper carries a DOF ledger),
inheriting the nyiso-96 keeper's UNION'd 21-entry ledger and adding ONE
measured entry for the arm's single delta.

The delta adds **zero fitted scalars**: the deriver's constants
(``EVENT_RAW_MAX`` 0.90, per-day cap 1.0, ``SCALE_CLIP`` 1.25, ``WEDGE_TOL``
0.01) are inherited FROZEN and unmodified from the ERCOT deriver — verified by
the PJM extract still reproducing byte-for-byte under ``--check`` — and the
level stays owned by the pre-existing EIA-923 anchor
``NUCLEAR_MONTHLY_CF_BY_YEAR``. The entry REPLACES an estimate (a fleet-month
CF smeared flat across four reactors, structurally unable to represent one
unit being out) with a measured per-reactor physical state, so ``n_residual``
stays 6.

Usage:
    python scripts/gen_nyiso98_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = REPO / "results/calibration/nyiso96_ctamort/calibration_attestation.json"
DEST = REPO / "results/calibration/nyiso98_nucavail/calibration_attestation.json"

NEW_ENTRY = {
    "name": "nuclear_unit_availability (NYISO, measured per-reactor daily NRC)",
    "where": "run_config.scenario_config.nuclear_unit_availability",
    "identification": "measured-physical",
    "lineage_solves": (
        "0 solves added to the tuning lineage — the mechanism was built to a "
        "pre-registration (docs/PREREG-nyiso98-nuclear-availability-"
        "2026-07-29.md, committed AND PUSHED before the extract was derived "
        "and before any LP ran) and A/B-tested ONCE against its same-HEAD "
        "zero-delta control (2026-07-29-nyiso-98-control-zerodelta). Nothing "
        "was swept and no parameter was adjusted after the result."
    ),
    "value": (
        "Each of the four NYISO reactors (FitzPatrick 6110_1, Ginna 6122_1, "
        "Nine Mile Point 1/2 2589_1/2) takes its own MEASURED DAILY "
        "availability in place of the fleet-month NUCLEAR_MONTHLY_CF_BY_YEAR "
        "smear: data/raw/nuclear-availability-NYISO.csv, 4,384 reactor-days, "
        "365/366-day coverage every year, all 36 months reconciling inside "
        "WEDGE_TOL so no month is dropped. The anchor owns the LEVEL (annual "
        "nuclear TWh moves -0.01/-0.02/-0.14 %); NRC owns the TIMING."
    ),
    "source": (
        "NRC daily Power Reactor Status reports "
        "(data/raw/nrc-reactor-status/<YYYY>PowerStatus.txt, "
        "scripts/data/fetch_nrc_reactor_status.py) reduced by the frozen "
        "derive scripts/data/derive_nuclear_availability.py --iso NYISO "
        "(rule 23 [R-FROZEN-DERIVE]: re-derives only when a new NRC year "
        "lands). Every deriver constant is inherited UNMODIFIED from the "
        "ERCOT deriver and the PJM extract still reproduces byte-for-byte "
        "under --check, so nothing was re-tuned for NYISO (rule 25 "
        "[R-ISO-SCOPE]); the level anchor NUCLEAR_MONTHLY_CF_BY_YEAR "
        "['NYISO'] is pre-existing and untouched. No parameter is fitted to "
        "a residual."
    ),
    "forward_story": (
        "A refuel window / reactor power state is a physical availability "
        "event that regenerates for a forward year through the "
        "NUCLEAR_MONTHLY_CF / refuel-block scheduling path already in the "
        "forecast lane, and responds to changed conditions through the "
        "outages the fleet actually takes (rule 13 admissibility) — the same "
        "class as the CAMPD fossil outage windows and as ERCOT's live keeper "
        "overlay ercot_nuclear_unit_availability."
    ),
    "rule_13_admissibility": (
        "The overlay sets AVAILABILITY from an independent physical "
        "instrument (percent of licensed thermal power at the NRC morning "
        "report), never generation from a metered outcome. STATED TENSION, "
        "NOT HIDDEN: nuclear is a flat must-run price-taker, so an "
        "availability overlay on it sits close to an output overlay. The "
        "line that keeps it admissible is that the LEVEL remains owned by "
        "the independent EIA-923 anchor and never by the scored series — the "
        "EIA-930 NG:NUC series this run is SCORED against is used only as a "
        "validation target and is forbidden as an input (rule 13)."
    ),
}

ATTESTED_BY = (
    "nyiso-98 OWNER PROMOTION 2026-07-29: the 2026-07-29-nyiso-96-ctamort "
    "keeper recipe re-solved on current main with ONE delta — "
    "nuclear_unit_availability=True, the ISO-generic measured per-reactor "
    "DAILY NRC Power Reactor Status availability replacing the fleet-month "
    "NUCLEAR_MONTHLY_CF_BY_YEAR smear — A/B'd against its same-HEAD "
    "zero-delta control (2026-07-29-nyiso-98-control-zerodelta, which "
    "reproduces the nyiso-96 keeper criterion-for-criterion including its "
    "published knife-edge 2023 CC_REGULAR cell at -2.76 of ±2.94). EVERY "
    "PRE-REGISTERED GATE PASSED: build-time G1 raw-NRC lift +0.304 (gate >= "
    "+0.10), G2 reconciled retention 104 % (gate >= 70 % — this is the PJM "
    "failure mode, where retention was NEGATIVE), G3 max annual |dTWh| "
    "0.14 % (gate < 0.5 %); in-solve S1 (no criterion verdict flips) and S2 "
    "(the mechanism's own target closes in every year). THE LEVER QUEUE'S "
    "STATED DEFECT WAS A BENCHMARK ARTIFACT AND THE SESSION CORRECTED IT "
    "BEFORE BUILDING THE ARM: 'nuclear r_day drops 0.84 -> 0.50/0.51 in "
    "2024-25' is scored against EIA-930 NYIS NG:NUC, which posts EXACTLY "
    "0.0 MW in contiguous blocks (1,179 h 2023 / 380 h 2024 / 117 h 2025 — "
    "zeros in the source parquet, not NaN, not the repo's gap-bridging), "
    "FALSIFIED against NRC on ALL 81 gap days across the three years with "
    "ZERO survivors (every one has >=1 NY reactor at 100 % of licensed "
    "thermal power). Gap-masked the ordering INVERTS to 0.446/0.833/0.534 — "
    "2023 is the WORST year, not the best — so the '2024-25 drop' does not "
    "exist as described. The target was re-based onto gap-clean r_day in "
    "the pre-registration, before the arm existed. THE RULE-1 [R-STRUCT] "
    "CASE, stated without leaning on fit: this replaces an ESTIMATE — a "
    "fleet-month CF smeared flat across four reactors, structurally unable "
    "to represent a single unit being out — with the MEASURED PHYSICAL "
    "STATE of each reactor from a public per-unit daily instrument, at zero "
    "fitted scalars, with the level still owned by the independent EIA-923 "
    "anchor. That it also nearly doubles the 2023 and 2025 daily-tracking "
    "correlation is corroboration, not the argument."
)

RESIDUALS_NOTE = (
    "SCORED EFFECT vs the same-HEAD zero-delta control "
    "(2026-07-29-nyiso-98-control-zerodelta): S2, the mechanism's own "
    "pre-registered target, CLOSES IN EVERY YEAR — gap-clean nuclear r_day "
    "0.446/0.833/0.534 -> 0.885/0.960/0.917 and r_hr 0.418/0.819/0.502 -> "
    "0.834/0.941/0.836, reproducing the build-time extract-arithmetic "
    "prediction (0.885/0.960/0.917) TO THREE DECIMALS, which is itself the "
    "strongest available check that nothing else moved. Displacement lands "
    "on IMPORTS (max |arm-control| hourly class delta 1,380/1,620/2,272 MW) "
    "— the physical signature of a must-run reactor going out and coming "
    "back, and the reason the mistracking mattered: the smear was "
    "mis-timing 0.6-1.3 GW of must-run supply against a measured import "
    "series that is itself an open mistracking item (queue item 9). S1 "
    "HOLDS: every criterion verdict is IDENTICAL to the control — C1 14/14 "
    "free 10/10, C2/C3a/C3b/C4/C7/C8 PASS. REPORTED HONESTLY, NOT PATCHED "
    "(rule 14 [R-ACCURATE]): the knife-edge 2023 CC_REGULAR cell walks "
    "-2.76 -> -2.79 TWh against ±2.94, consuming ~14 % of its remaining "
    "0.18 TWh headroom. It stays IN BAND and the accurate measured input "
    "STAYS IN — a thinner margin against an accurate physical input is a "
    "discovered root cause elsewhere, never grounds to restore a "
    "known-defective estimate. C8 2024 ST_GAS 30.43 -> 30.47 % forced "
    "(+0.04 pp), grounded above budget on BOTH sides — the fragile cell "
    "does not flip; C7 D-1 rows move in the third decimal. C3c (not the "
    "gate, roof-blocked) 3/0/7 -> 4/0/7 h >$300 vs actual 10/12/42. LOYO "
    "(rule 22): NO parameter is fitted to any year — the deriver constants "
    "are frozen cross-ISO inheritances and each year's overlay derives from "
    "that year's own NRC reports against that year's own 923 anchor; all "
    "three years scored in this one bundle, direction consistent in each. "
    "LIVE-MECHANISM CHECK recorded BEFORE results were read (nyiso-89 §4a): "
    "29,088/32,184/26,136 availability cells changed with ZERO changes "
    "outside nuclear rows, min_gen tracking cell-for-cell."
)

OPEN_ITEMS = (
    "(0) OWNER-ACCEPTED MISREPRESENTATION, CARRIED FORWARD UNCHANGED from "
    "the nyiso-96 promotion (owner decision 2026-07-29): CT_PEAKER is "
    "under-produced 0.22/0.19/0.74 TWh against a measured 1.88/1.76/2.22 "
    "with a start deficit of 5.20x/6.52x/2.43x, and the promoted "
    "tranche_startup_amortization mechanism moves the model's CT offers in "
    "the OPPOSITE direction from the fleet's measured conduct (53-66 % of "
    "measured CT energy clears below its own SRMC at its own zonal price). "
    "This keeper does not touch it — the nuclear delta moves CT_PEAKER by "
    "+0.010/-0.001/-0.002 TWh. Per FINDING-nyiso96 §5 it is a KNOWN, "
    "DELIBERATELY-ACCEPTED misrepresentation, not an open mechanism lane; "
    "un-accepting it requires a published-primary-source mechanism, never a "
    "floor (rule 17; h14-21 windowed floors OFF by owner directive "
    "2026-07-27). (1) C3c remains the SOLE determination blocker, 4/0/7 h "
    ">$300 vs actual 10/12/42 (2023 3->4 h, otherwise unchanged): a "
    "DIAGNOSED, UNCLOSED structural limitation of the five-zone "
    "representation with an EMPTY lever queue — nyiso-94 (DA virtual) and "
    "nyiso-95 (TSA derate) closed G ex-ante on identification, and "
    "nyiso-97 closed the surviving SCUC load-pocket candidate ex-ante on "
    "CONTENT (the as-enforced Con Ed AORR is MyNYISO-walled; the public "
    "2008-vintage Appendix B carries no derivable NYC parameter). Re-open "
    "conditions: FINDING-nyiso97 §5, none currently satisfiable. (2) C1 "
    "2023 CC_REGULAR passes at -2.79 of ±2.94 — margin 0.15 TWh, THINNER "
    "than the nyiso-96 keeper's 0.18 and now the ISO's tightest cell; the "
    "downstate CC deficit root cause (nyiso-81 'downstate ST/CC mix "
    "boundary' + pinned CC_CHP under-dispatch) is unchanged underneath the "
    "pass and any future arm must budget against this narrower headroom. "
    "(3) NEW, RAISED BY THIS SESSION AND DELIBERATELY NOT DONE (rule 24): "
    "the EIA-930 zero-block audit must be repeated for the OTHER component "
    "series this repo scores against — import, NG:WAT, NG:OIL — and for "
    "the other five ISOs' BAs. NYISO NG:OIL (r_day 0.07) is the obvious "
    "next suspect, and hydro + import are both live queue items whose "
    "scored residuals may be contaminated the same way. Any NYISO "
    "statistic scored against EIA-930 NG:NUC without the gap mask is "
    "unreliable, including two numbers previously on the record (the lever "
    "queue's r_day ordering and nyiso-92's 2023 nuclear level). (4) "
    "Remaining dispatch-matching components by measured mistracking: "
    "import hourly shape r_hr 0.45-0.61 (nyiso-86 §3, queue item 9), "
    "hydro_ror_split pending its NYISO classifier review (Niagara hybrid "
    "label, queue item 8). Nuclear is CLOSED by this keeper. (5) Carried "
    "from nyiso-96: the keeper-lineage meta still arms "
    "dual_fuel_oil_reattribution for NYISO — a recording basis the CLI has "
    "since pinned NEISO-only; dropping it is a zero-dispatch-delta cleanup "
    "for the next re-solve (queue item 10). (6) Two 2025 months (Feb, Apr) "
    "hit the frozen SCALE_CLIP 1.25 and reconcile only to -0.62 %/-0.32 %, "
    "inside WEDGE_TOL but at its edge; re-check them if a future NRC year "
    "lands (rule 23 — data change only, never a residual)."
)


def main() -> int:
    """Build nyiso-98's attestation from the nyiso-96 keeper's."""
    att = json.loads(PRIOR_KEEPER.read_text())
    gov = dict(att.get("governance", {}))
    gov["attested_by"] = ATTESTED_BY
    gov["residuals_note"] = RESIDUALS_NOTE
    att["governance"] = gov
    att["_open_items"] = OPEN_ITEMS
    fp = att["free_parameters"]
    names = {e["name"] for e in fp["entries"]}
    if NEW_ENTRY["name"] not in names:
        fp["entries"] = [*fp["entries"], NEW_ENTRY]
    fp["seeded"] = (
        "2026-07-29 nyiso-98 — UNION'd forward from the nyiso-96 keeper "
        "ledger (21 entries) and NOT rebuilt (a blind build_dof_ledger.py "
        "rebuild drops the curated measured/published entries — the failure "
        "mode the nyiso-81/87/89/92/96 notes all recorded). ONE new entry: "
        "nuclear_unit_availability on the measured NYISO NRC daily basis. "
        "n_residual STAYS 6 — the entry adds ZERO fitted scalars (deriver "
        "constants inherited FROZEN and unmodified from ERCOT, verified by "
        "the PJM extract still reproducing byte-for-byte under --check; the "
        "level anchor NUCLEAR_MONTHLY_CF_BY_YEAR is pre-existing and "
        "untouched) and REPLACES an estimate rather than adding a degree of "
        "freedom."
    )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    DEST.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {DEST.relative_to(REPO)} — {fp['n_entries']} DOF entries "
        f"({fp['n_residual']} residual-identified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
