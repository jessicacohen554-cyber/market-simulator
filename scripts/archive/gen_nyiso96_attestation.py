"""Write ``calibration_attestation.json`` for the nyiso-96 PROMOTED arm.

``2026-07-29-nyiso-96-ctamort`` (``results/calibration/nyiso96_ctamort``) was
registered as a REJECTED probe — the session adjudicated
``tranche_startup_amortization`` -> NYISO ``R`` on rule 1 [R-STRUCT] grounds
(docs/FINDING-nyiso96-ct-start-frequency-2026-07-29.md §5) and left the run
unpromoted despite a strictly better scorecard (C1 PASS 14/14 vs the keeper's
13/14). That finding explicitly surfaced the call to the owner: "If the owner
prefers the gate, the run is registered and promotable — but the peaker
diagnosis in §2 and nyiso-90/91 would then need re-opening as a known,
deliberately-accepted misrepresentation rather than an open item."

The OWNER MADE THAT CALL on 2026-07-29 (C3c load-pocket scoping session,
AskUserQuestion step 0b): promote ``2026-07-29-nyiso-96-ctamort`` to keeper,
accepting the C1 trade — CT_PEAKER degrading 27-39 % — with the regression on
the record. This script builds the C6 attestation that promotion requires
(rule 21 [R-DOF]: every keeper carries a DOF ledger), inheriting the nyiso-92
keeper's UNION'd 20-entry ledger and adding ONE measured entry for the arm's
single mechanism-family delta.

The delta adds **zero fitted scalars** (FINDING §DOF ledger): the start costs
are the already-cited-and-ledgered NREL ``BIN_STARTUP_COST_PER_MW`` table
($20/MW CT, $50/MW CC duct bands, in use for the committed tranche since the
ERCOT lineage), and the amortization horizon is the measured
``campd_ct_run_lengths_NYISO.csv`` artifact (22 plants + a pooled class
fallback of 4.0 h over 34,057 measured NYISO CAMPD runs). ``n_residual``
stays 6.

Usage:
    python scripts/gen_nyiso96_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = (
    REPO / "results/calibration/nyiso92_hydro_envfloor/calibration_attestation.json"
)
DEST = REPO / "results/calibration/nyiso96_ctamort/calibration_attestation.json"

NEW_ENTRY = {
    "name": "tranche_startup_amortization (v3 measured NYISO run-length basis)",
    "where": (
        "run_config.scenario_config.tranche_startup_amortization + "
        "tranche_startup_measured_runs"
    ),
    "identification": "measured-physical",
    "lineage_solves": (
        "0 solves added to the tuning lineage — the mechanism was built to a "
        "pre-registration (docs/handoffs/nyiso96-preregistration.md, committed "
        "before the A/B launched) and A/B-tested ONCE against its same-HEAD "
        "zero-delta control (2026-07-29-nyiso-96-control-zerodelta). Nothing "
        "was swept and no parameter was adjusted after the result."
    ),
    "value": (
        "Each thermal tranche's offer adds start_cost_per_mw / "
        "expected_run_hours: start costs from the NREL BIN_STARTUP_COST_PER_MW "
        "table already ledgered for the committed tranche ($20/MW "
        "CT_PEAKER/CT_CHP, $50/MW CC duct bands); expected run hours from the "
        "plant's own measured CAMPD run-length p50 "
        "(campd_ct_run_lengths_NYISO.csv, 22 plants + pooled class fallback "
        "4.0 h, 34,057 measured runs 2023-2025). Realised offer increment "
        "~$5/MWh on the CT bands, as pre-registered."
    ),
    "source": (
        "NREL startup-cost table (docs/parameter-citations.md, pre-existing "
        "citation) + data/raw CAMPD unit conduct reduced by the frozen derive "
        "scripts/data/derive_campd_ct_run_lengths.py (rule 23 "
        "[R-FROZEN-DERIVE]: re-derives only on a CAMPD source update). No "
        "parameter is ported from another ISO (rule 25 [R-ISO-SCOPE]) and "
        "none is fitted to a residual."
    ),
    "forward_story": (
        "Both inputs regenerate for a forward year: the NREL table is a "
        "published engineering constant, and the run-length basis re-derives "
        "from rolling CAMPD history conditioned on the fleet, responding to "
        "changed conditions through the runs the fleet actually produces "
        "(rule 13 admissibility)."
    ),
    "rule_13_admissibility": (
        "A start-cost amortization over a measured expected run length is a "
        "market-design input (bid production cost recovery), not an outcome "
        "pinned to a residual: no volume or price is pinned, the LP still "
        "chooses dispatch, and prices remain LP duals (rule 4 [R-DUALS])."
    ),
}

ATTESTED_BY = (
    "nyiso-96 OWNER PROMOTION 2026-07-29: the 2026-07-28-nyiso-92-hydro-"
    "envelope keeper recipe re-solved on current main with ONE mechanism-"
    "family delta — tranche_startup_amortization + tranche_startup_measured_"
    "runs (v3 measured NYISO CAMPD run-length basis) — A/B'd against its "
    "same-HEAD zero-delta control (2026-07-29-nyiso-96-control-zerodelta, "
    "which reproduces the nyiso-92 keeper on every number checked). THE "
    "SESSION THAT BUILT IT DID NOT PROMOTE IT: FINDING-nyiso96-ct-start-"
    "frequency-2026-07-29.md §5 adjudicated the mechanism R on rule 1 "
    "[R-STRUCT] grounds — the arm flips NYISO's only failing load-bearing "
    "gate (C1 2023 CC_REGULAR -3.05 -> -2.76 TWh of ±2.94, C1 14/14 free "
    "10/10) while making the lane's dominant diagnosed structural defect "
    "27-39 % WORSE (CT_PEAKER 0.323/0.305/1.070 -> 0.220/0.188/0.741 TWh "
    "against a measured 1.88/1.76/2.22; start ratio 3.79x/4.25x/1.72x -> "
    "5.20x/6.52x/2.43x), and 53-66 % of measured CT energy clears below its "
    "own SRMC at its own zonal price, so the fleet demonstrably does not "
    "price this way. The finding surfaced the promotion as an owner-visible "
    "call, and the OWNER TOOK THE GATE on 2026-07-29 (AskUserQuestion, C3c "
    "load-pocket scoping session): promote for the C1 PASS, accepting the "
    "CT_PEAKER degradation. Per the finding's own terms, the peaker "
    "diagnosis (nyiso-90/91/96 §2) is hereby re-opened as a KNOWN, "
    "DELIBERATELY-ACCEPTED MISREPRESENTATION rather than an open mechanism "
    "item — see _open_items (0). C3c (3/0/7 h >$300 vs actual 10/12/42) is "
    "bit-for-bit unchanged and remains the SOLE determination blocker; its "
    "surviving candidate (SCUC load-pocket security commitment + BPCG) is "
    "the same session's scoping lane."
)

RESIDUALS_NOTE = (
    "SCORED EFFECT vs the same-HEAD zero-delta control (2026-07-29-nyiso-96-"
    "control-zerodelta): C1 fuel-mix — the control's ONLY failing cell, 2023 "
    "CC_REGULAR -3.05 TWh of ±2.94 — walks to -2.76 and PASSES (14/14, free "
    "10/10); the displaced energy lands on CC_REGULAR (+0.284/+0.496/+0.408 "
    "TWh) and ST_GAS (+0.159/+0.183/+0.175), sourced from CT_PEAKER "
    "(-0.184/-0.190/-0.447), CT_CHP (-0.121/-0.097/-0.056) and CC_CHP "
    "(-0.141/-0.363/-0.062). Every other criterion is IDENTICAL to the "
    "control: C2/C3a/C3b/C4/C7/C8 PASS, C3c FAIL 3/0/7 h >$300 vs actual "
    "10/12/42 (bit-for-bit unchanged — the lever buys exactly zero tail "
    "hours). REPORTED HONESTLY, NOT PATCHED: both CC_REGULAR and CT_PEAKER "
    "are UNDER-produced against measured; the arm shrinks the larger "
    "shortfall by widening the smaller one, so no class is better "
    "represented — the C1 PASS is an owner-accepted trade, not a closed "
    "defect. Median CT run length 6->7/6->5/6->6 h vs measured 5 "
    "(essentially unmoved; the model's blocks were already the right "
    "length). LOYO (rule 22): the mechanism carries NO parameter fitted to "
    "any year — the run-length basis is a pooled 2023-2025 measured "
    "statistic and the start costs are a published constant; all three "
    "years scored in this one bundle, direction consistent in each."
)

OPEN_ITEMS = (
    "(0) OWNER-ACCEPTED MISREPRESENTATION ON THE RECORD (owner decision "
    "2026-07-29, this promotion): CT_PEAKER — already the dominant open item "
    "— degrades 27-39 % under the promoted mechanism (0.220/0.188/0.741 TWh "
    "vs measured 1.88/1.76/2.22; start deficit 5.20x/6.52x/2.43x vs "
    "measured), and the mechanism moves the model's CT offers in the "
    "OPPOSITE direction from the fleet's measured conduct (53-66 % of "
    "measured CT energy clears below its own SRMC at its own zonal price). "
    "Per FINDING-nyiso96 §5 this is carried as a KNOWN, DELIBERATELY-"
    "ACCEPTED misrepresentation, not an open mechanism lane: the class sits "
    "below the 2 % materiality floor (ungated), every in-model lever is "
    "adjudicated (nyiso-83/84/90/91/94/95/96), and the surviving candidate "
    "is the SCUC load-pocket security commitment + BPCG sub-zonal lane "
    "(owner-authorized for scoping 2026-07-29, data-first). Un-accepting it "
    "requires that lane to produce a published-primary-source mechanism — "
    "never a floor (rule 17; h14-21 windowed floors OFF by owner directive "
    "2026-07-27). (1) C3c remains the SOLE determination blocker, UNCHANGED "
    "3/0/7 h >$300 vs actual 10/12/42: the measured tail is SUMMER RT "
    "scarcity (2025 Jun 23-25 = 18 of 42 h; Jan-2024 storm Gerri = 0 h). "
    "DA virtual depth (nyiso-94) and TSA transfer derate (nyiso-95) are "
    "closed G ex-ante on identification; the load-pocket lane is what "
    "remains. (2) C1 2023 CC_REGULAR now PASSES at -2.76 of ±2.94 — margin "
    "0.18 TWh, still thin; the downstate CC deficit root cause (nyiso-81 "
    "'downstate ST/CC mix boundary' + pinned CC_CHP under-dispatch) is "
    "unchanged underneath the pass. (3) NEXT dispatch-matching components "
    "by measured mistracking (carried from nyiso-92): nuclear r_day 0.50 in "
    "2024-25 (refuel timing; nuclear_unit_availability N=U), import hourly "
    "shape r_hr 0.45-0.61 (nyiso-86 §3), hydro_ror_split pending its NYISO "
    "classifier review (Niagara hybrid label). (4) The keeper-lineage meta "
    "still arms dual_fuel_oil_reattribution for NYISO — a recording basis "
    "the CLI has since pinned NEISO-only; dropping it from the lineage is a "
    "zero-dispatch-delta cleanup for the next re-solve."
)


def main() -> int:
    """Build nyiso-96's attestation from the nyiso-92 keeper's."""
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
        "2026-07-29 nyiso-96 — UNION'd forward from the nyiso-92 keeper "
        "ledger (20 entries) and NOT rebuilt (a blind build_dof_ledger.py "
        "rebuild drops the curated measured/published entries — the failure "
        "mode the nyiso-81/87/89/92 notes all recorded). ONE new entry: "
        "tranche_startup_amortization on the v3 measured NYISO run-length "
        "basis. n_residual STAYS 6 — the entry adds ZERO fitted scalars "
        "(published NREL start costs already in use for the committed "
        "tranche + a measured pooled CAMPD statistic, rule 23)."
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
