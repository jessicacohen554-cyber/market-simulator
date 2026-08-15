"""Write ``calibration_attestation.json`` for the caiso-151 keeper candidate.

The caiso-151 arm is the caiso-148 keeper recipe with ONE delta —
``caiso_firm_import_selfsched_clip=true``, clipping the caiso-77 firm must-flow
FLOOR at CAISO's own measured price-insensitive intertie ceiling — so this
attestation is the caiso-148 keeper's attestation with:

1. a rewritten ``governance.attested_by`` describing the single delta,
2. the caiso-145 **owner** exception ledger **CARRIED FORWARD UNCHANGED IN
   SUBSTANCE**, with each entry's ``magnitude`` re-measured on this bundle, and
3. one new DOF-ledger entry for the mechanism, identification ``measured``.

**On carrying the ledger forward.** The three exception rows were adopted by the
owner at caiso-145 (2026-07-30): C3c-2023 and C3c-2024 on caiso-131 §9
disposition A4 with the caiso-144 evidence, and C3a-2025 on the caiso-141 A2
data wall. This session creates **no new caveat and spends no new ledger slot**
— it re-states the owner's own dispositions against a re-measured bundle. Each
carried entry records its provenance so the owner's act stays attributable and
is never mistaken for a fresh grant by this session.

**C3a-2025 moved and the movement is stated, not buried.** The clip is
E1-ADVERSE by construction and was pre-registered as such: removing forced cheap
overnight import raises overnight λ, and CAISO's model λ already sits ABOVE the
RT actual, so the C3a miss GROWS. Measured against the same-HEAD zero-delta
control: **+11.23 % → +11.72 %, i.e. +0.494 pp**, against the **1.0 pp**
materiality trigger `PREREG-caiso151` §6 fixed in advance — below the trigger,
so reported and not built upon, but an order of magnitude larger than the
0.0 pp caiso-148 recorded and therefore called out explicitly here. It does
**not** reopen the caveat: reopening requires new evidence against a named
caiso-140/141/142/143/144 DO-NOT-REDO cell or the owner-funded non-public hourly
pumped-storage intake.

C3c is **bit-identical** across the two arms — model 0 h > $200 in every year,
identical maxima ($188 / $149 / $74).

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_caiso151_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

SOURCE = REPO / "results/calibration/caiso148_nucavail_B/calibration_attestation.json"
TARGET = REPO / "results/calibration/caiso151_clip_B/calibration_attestation.json"

ATTESTED_BY = (
    "caiso-151 (2026-07-31): the caiso-148 keeper recipe with ONE delta, "
    "caiso_firm_import_selfsched_clip=true — the caiso-77 firm must-flow FLOOR "
    "clipped hour-by-hour at CAISO's measured price-insensitive intertie "
    "ceiling, min_gen[t] = min(pmax x availability[t], ceiling[t]), the system "
    "ceiling allocated across firm tranches pro rata by their own shaped "
    "capability. ZERO new free parameters: a pointwise min of two measured "
    "series, structurally the accepted caiso-138 envelope-clip pattern, "
    "composing with it as a SECOND min on its own flag (rule 19 [R-ONE-MECH]) "
    "and reconciling the caiso-73 shape rather than stacking on it. The "
    "parameter series is a rule-23 frozen derive over CAISO OASIS PUB_BID_DAM "
    "(357 balanced trade days, 1,574,341 resource-hours) whose four honesty "
    "gates were declared EX ANTE and all PASS: CV 0.042 (<=0.20), LOYO level "
    "4.6/8.4/4.6 % (<=25 %), LOYO shape 19.3/12.3/18.6 % over all 288 buckets "
    "(<=25 %), coverage 288/288 in all three years. Single-flag A/B against a "
    "same-HEAD zero-delta control solved in the same session; every criterion "
    "verdict is UNCHANGED and both protective gates (C7 shape, C8 forced "
    "share) PASS on both arms. The lever was pre-registered E1-ADVERSE before "
    "either arm solved and the adverse movement is recorded in the C3a-2025 "
    "exception below (rule 1 [R-STRUCT]: a structurally-correct mechanism "
    "stays in even when the fit worsens, and is equally never adopted because "
    "a residual moved). Evidence: FINDING-caiso151, PREREG-caiso151, "
    "FINDING-caiso150 §F."
)

CARRY = (
    "CARRIED FORWARD from the caiso-148 keeper unchanged in substance; "
    "originally adopted by the OWNER at caiso-145 (2026-07-30). caiso-151 "
    "creates no new caveat and spends no new ledger slot. "
)

REMEASURED = {
    ("price_tail", 2023): (
        "RE-MEASURED on caiso151_clip_B: model 0 h > $200 (max $188) vs RT "
        "actual 47 h — BIT-IDENTICAL to the same-HEAD control. "
    ),
    ("price_tail", 2024): (
        "RE-MEASURED on caiso151_clip_B: model 0 h > $200 (max $149) vs RT "
        "actual 35 h — BIT-IDENTICAL to the same-HEAD control. "
    ),
    ("price_mean", 2025): (
        "RE-MEASURED on caiso151_clip_B: +11.72 % vs RT actual $34.39, against "
        "the control's +11.23 % — a movement of +0.494 pp, BELOW the 1.0 pp "
        "materiality trigger PREREG-caiso151 §6 fixed in advance, and in the "
        "E1-ADVERSE direction that pre-registration predicted. Stated, not "
        "built upon; the caveat is NOT reopened by it. "
    ),
}

NEW_DOF = {
    "name": "caiso_firm_import_selfsched_clip / caiso_intertie_selfsched_ceiling.csv",
    "where": (
        "config.scenarios ScenarioConfig field -> "
        "model.interchange.caiso.inject_caiso_firm_import_selfschedule("
        "selfsched_clip=True); series "
        "data.caiso_intertie_bids.measured_intertie_selfsched_ceiling over "
        "data/raw/_processed-legacy/caiso_intertie_selfsched_ceiling.csv"
    ),
    "identification": "measured",
    "lineage_solves": "1 A/B (caiso-151), single-flag vs a same-HEAD zero-delta control",
    "source": (
        "CAISO OASIS Public Bid Data (PUB_DAM_GRP, tariff §6.5.2.2, 90-day "
        "lag) — every DAM bid AS SUBMITTED. The ceiling is ALL intertie "
        "self-schedule MW (both directions, unsigned) PLUS import-classified "
        "economic MW offered at or below $0/MWh; both limbs together are the "
        "caiso-77 floor's OWN definition of price-taking conduct (CPUC "
        "D.20-06-028, quoted in its docstring) and both are taken generously, "
        "so the table is a one-sided CEILING >= the true price-insensitive "
        "IMPORT position in every hour. That one-sidedness is what makes the "
        "mechanism survive the caiso-150 §B identification wall: direction is "
        "NOT identifiable in the masked feed (94.54 % of self-scheduled MW is "
        "on resources that never submit an economic curve), and a clip at an "
        "upper bound can only REMOVE forcing the measured record cannot "
        "support, never add any. NO fitted scalar: the derive "
        "(scripts/data/derive_caiso_intertie_selfsched.py) is frozen against "
        "residuals per rule 23 [R-FROZEN-DERIVE] and re-runs only on a source "
        "corpus change. Forward-reproducible (rule 13 [R-MEASURED]): OASIS "
        "publishes continuously at a 90-day lag and the shipped table is a "
        "pooled equal-year-weight climatology, so it applies unchanged in a "
        "forecast year exactly as the caiso-73 shape's own climatology does."
    ),
}


def main() -> int:
    """Write the caiso-151 attestation from the caiso-148 keeper's."""
    att = json.loads(SOURCE.read_text())
    att["governance"]["attested_by"] = ATTESTED_BY

    for exc in att["exceptions"]:
        key = (exc.get("criterion"), int(exc.get("year", 0)))
        if key in REMEASURED:
            exc["magnitude"] = REMEASURED[key] + "PRIOR MAGNITUDE: " + exc["magnitude"]
        exc["reason"] = CARRY + exc["reason"]
        exc["carried_from"] = (
            "2026-07-31-caiso148-nuclear-availability -> "
            "2026-07-31-caiso147-chp-heat-rates -> "
            "2026-07-29-caiso139-dump-guard-offer (owner ledger, caiso-145)"
        )

    dof = att["free_parameters"]
    dof["entries"] = [e for e in dof["entries"] if e.get("name") != NEW_DOF["name"]] + [
        NEW_DOF
    ]
    dof["n_entries"] = len(dof["entries"])
    dof["n_residual"] = sum(
        1 for e in dof["entries"] if e.get("identification") == "residual"
    )

    TARGET.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {TARGET}")
    print(f"  exceptions carried: {len(att['exceptions'])}")
    print(
        f"  DOF entries: {dof['n_entries']} ({dof['n_residual']} residual-identified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
