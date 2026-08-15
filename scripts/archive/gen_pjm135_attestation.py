"""Write ``calibration_attestation.json`` for the pjm-135 net-position candidate.

``pjm135_netpos_keeper_C`` is the ``2026-07-27-pjm-133-nameplate`` keeper recipe
replayed with ONE delta: ``pjm_external_net_position_cut=true``. Governance
posture and the accepted-limitation ledger are therefore the keeper's, inherited
unchanged, with ONE added ledger entry.

The delta adds **zero residual-identified degrees of freedom** (rule 23
``[R-DOF]``). It is one one-sided aggregate interface row per hour capping the
summed injection across the five ``PJM_external -> border`` links — i.e. the
LP's own net interchange — at the measured (month x hour-of-day) percentile of
PJM's published tie-line net position. It reuses the tie-line file the per-border
envelope already reads and the existing ``PJM_EXTERNAL_FLOW_PERCENTILE`` constant
verbatim: no scale, no haircut, no blend, no new percentile. So the ledger gains
a ``measured-external`` entry and ``n_residual`` is unchanged — the same posture
as the already-ledgered ``PJM EAST interface cut (joint EMAAC import cap)``,
whose construction this shares (``_build_joint_interface_cut``).

Usage:
    python scripts/gen_pjm135_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results/calibration/pjm133_nameplate_B/calibration_attestation.json"
ARM = REPO / "results/calibration/pjm135_netpos_keeper_C/calibration_attestation.json"

NEW_ENTRY = {
    "name": "PJM star-node NET-position cut (joint external seam cap)",
    "where": "run_config.scenario_config.pjm_external_net_position_cut",
    "identification": "measured-external",
    "lineage_solves": (
        "0 solves added to the tuning lineage — the cap is the published PJM "
        "tie-line net position at the existing constants.PJM_EXTERNAL_FLOW_"
        "PERCENTILE (95.0), bucketed (month x hour-of-day) exactly as the "
        "per-border envelope already is. Nothing was swept, and PREREG "
        "§4's no-feedback ceiling forbids ever sweeping it."
    ),
    "value": (
        "eia930.envelopes.pjm_net_interchange_envelope(year, hours, 95.0) — "
        "one one-sided aggregate row per hour: "
        "sum_z Flow(PJM_external -> z) <= envelope(t)"
    ),
    "source": (
        "PJM Data Miner 2 import_export_act_sch_interchange "
        "(data/raw/iso-specific-transmission/PJM_<year>_import_export_act_sch_"
        "interchange.csv) — the same feed the per-border deliverability "
        "envelope and the IMPORT_NODE_LINKS ratings are read from."
    ),
    "forward_story": (
        "A net-position capability envelope regenerates for a forward year "
        "from the same feed and responds to changed conditions. Forecast years "
        "carry no measured tie file, so the envelope is None and the node is "
        "left uncapped — the two-track construction pjm_measured_interface_"
        "limits already uses."
    ),
    "rule_13_admissibility": (
        "A published net interchange position is a market/physical input, not "
        "an outcome pinned to a residual: it is applied as a one-sided "
        "CEILING the LP clears within on its own economics, never as a target "
        "the model is forced onto. The LP's net position remains strictly "
        "inside it (arm B: -30.41/-23.66/-27.53 TWh against a measured "
        "-39.98/-32.83/-32.93), so no volume is pinned to the actual."
    ),
}

ATTESTED_BY = (
    "pjm-135 star-node NET-position cut 2026-07-28: the "
    "2026-07-27-pjm-133-nameplate keeper recipe replayed with a SINGLE delta, "
    "pjm_external_net_position_cut=true. Chartered by FINDING-pjm135 §5-§6 and "
    "gated by PREREG-pjm135-star-node-net-position-cut-2026-07-28.md, committed "
    "and pushed BEFORE any arm solved. "
    "DRIVER: the priced star node was bounded ONLY by marginal per-border, "
    "per-direction percentiles (build_pjm_external_flow_groups caps each link "
    "at its own border's p95; inject_pjm_seam_flow_limit sizes each neighbor's "
    "bands from the same rows, double-counting Dominion via Carolinas+TVA and "
    "triple-counting AEP_Ohio via MISO+TVA+LGEE). Five marginal 95th "
    "percentiles were summed as though they were a joint one and NOTHING "
    "bounded the total, so the model's own net interchange ran "
    "-28.89/-21.86/-25.80 TWh against a measured -39.98/-32.83/-32.93 — a "
    "7.1-11.1 TWh/yr structural over-supply with a NEGATIVE hourly R^2, and "
    "~10 % of hours more import-heavy than PJM has ever been in that "
    "(month, hour-of-day) bucket. Rule 19 [R-ONE-MECH]: the joint cap REPLACES "
    "the sum-of-marginals ceiling on the aggregate question and dominates it; "
    "the per-border groups keep the locational bound. "
    "EVIDENCE (arms pjm135_control_A / pjm135_netpos_B, all three years in one "
    "invocation): every pre-registered gate PASSES. P1 enforcement "
    "23.48/21.22/18.56 % of hours above the envelope -> 0.00 %, max excess on "
    "the constrained flows 0.000000 MW. P2 direction toward the measured value "
    "and never past it. K2 zero slack and zero dump in BOTH arms, ALL years — "
    "the pre-registered principal risk, since the cap binds in 93.2/92.1/96.6 % "
    "of top-1 % load hours. K5 arm A reproduces pjm134_control_A "
    "BYTE-IDENTICALLY (0.000000000 MW, 19 classes, every hour, 3 years). "
    "Rule-22 leave-one-year-out clean: the delta is same-signed in every year "
    "independently (net -1.52/-1.80/-1.73 TWh; CC_REGULAR +0.58/+0.52/+0.48; "
    "CT_PEAKER +0.27/+0.38/+0.41), and the two rubric flips are carried by "
    "DIFFERENT years (C1 by 2023, C3a by 2025), so neither rests on one year. "
    "Solve cost: NONE — arm B ran 33.6 min against arm A's 40. "
    "HONEST SCOPE, carried and never dropped: this is INERT on the Dominion "
    "zonal inversion it was chartered against. Dominion CT_PEAKER moves "
    "+0.024/+0.038/+0.063 TWh against gaps of -6.7/-7.4/-7.2, and only ~15 % of "
    "the ISO-wide CC_REGULAR gain lands in Dominion — the rest goes west, "
    "exactly as the measured zero-dual copper-plate predicts (PJM_external is "
    "price-tied to every PJM zone in 100.00 % of hours, max |delta| = 0.0000 "
    "$/MWh). The C1/C3a improvement is an ISO-WIDE effect, not a fix to the "
    "zonal allocation defect, which stays OPEN. Rule 1 [R-STRUCT]: the delta "
    "was chartered as structurally correct and PREREG §4 pre-registered "
    "INERT-on-the-defect as the expected outcome before the solve; the gate "
    "movement is a consequence, not the justification, and PREREG §4's "
    "no-feedback ceiling was honoured — no percentile, multiplier, haircut or "
    "scarcity exemption was applied to the envelope, and none may be."
)


def main() -> int:
    """Write the arm's attestation from the keeper's, plus the one new entry."""
    att = json.loads(KEEPER.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=ATTESTED_BY)

    fp = att["free_parameters"]
    names = {e["name"] for e in fp["entries"]}
    if NEW_ENTRY["name"] not in names:
        fp["entries"] = [*fp["entries"], NEW_ENTRY]
    fp["n_entries"] = len(fp["entries"])
    # Unchanged on purpose: the delta adds no residual-identified parameter.
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )

    ARM.parent.mkdir(parents=True, exist_ok=True)
    ARM.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {ARM.relative_to(REPO)} — {fp['n_entries']} DOF entries "
        f"({fp['n_residual']} residual-identified, unchanged from the keeper's "
        f"{json.loads(KEEPER.read_text())['free_parameters']['n_residual']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
