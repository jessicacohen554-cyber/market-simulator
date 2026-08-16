"""Write the miso-160 calibration attestations (control + arm).

Both bundles are ``replay_keeper`` re-solves of the MISO keeper
``2026-08-15-miso-159-cod-vintage``'s own ``meta.json`` at this session's HEAD,
``--year 2023 2024 2025`` in ONE invocation each, years sequential inside the
invocation (rules 12 / 16). The CONTROL carries ZERO deltas; the ARM changes
EXACTLY ONE ``ScenarioConfig`` field, ``summer_wefor_share_override = 1.0599``,
applied through the generic ``prb_overrides`` channel and recorded verbatim in
``run_config.json`` (rule 24 [R-REGISTRY]).

The DOF ledger, disclosures and exceptions are inherited from the keeper's own
attestation. The arm adds ONE entry whose identification is *derived* from a
published measured record (never *residual*), so the residual count is
unchanged — and the standing open root-cause item on ``SUMMER_WEFOR_SHARE``
(miso-157 B-DISAGREE) is RETIRED for MISO by the owner's provenance decision
plus this derivation.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "miso159_cod_B"
CONTROL = REPO / "results" / "calibration" / "miso160_wefor_A"
ARM = REPO / "results" / "calibration" / "miso160_wefor_B"

_COMMON = (
    "miso-160, 2026-08-16. PREREG "
    "results/calibration/PREREG-miso160-summer-wefor-measured-share-2026-08-16.md "
    "pushed at a96702b (blob 57d2b8b1, verified byte-identical against the "
    "FETCHED remote ref) BEFORE the construction was built, the derive was "
    "computed, or any solve was launched. Both arms are replay_keeper re-solves "
    "of the 2026-08-15-miso-159-cod-vintage keeper's own meta.json at this "
    "session's HEAD, --year 2023 2024 2025 in ONE invocation each, years "
    "sequential (rules 12 / 16). Rule 22: no year outside 2023-2025 was solved, "
    "scored or registered; MISO holds neither complete nor final and the "
    "holdout spend freeze is untouched. "
    "K0/V2 PASSES IN ITS STRONGEST FORM: the zero-delta CONTROL reproduces the "
    "committed keeper BIT-IDENTICALLY — 0 of 70,080 differing P1 zone-hour "
    "price cells in EVERY year (demand-weighted LMP 32.8306 / 30.5432 / "
    "39.4959, equal to the keeper's committed sidecars to the 4th decimal) — "
    "so no K0-class drift is carried and the off path of the new field is "
    "proven byte-inert at the FULL-SOLVE grain, not merely the unit-test "
    "grain. SESSION-INFRA DISCLOSURE: this container's git transport has no "
    "credentials (the miso-159 situation); every artifact traveled to the "
    "branch via the API path with per-blob byte verification, and the "
    "implementation traveled as a three-piece patch "
    "(.claude-transfer/miso160/, reassembly sha256 e0679f23, pieces "
    "9b83a95e/f8ebe4bc/8143d607) for a follow-on git session to apply."
)

CONTROL_NOTE = "CONTROL — ZERO DELTAS (scripts/replay_keeper.py, no --set). " + _COMMON

ARM_NOTE = (
    "ARM — EXACTLY ONE MECHANISM CHANGES: summer_wefor_share_override=1.0599. "
    + _COMMON
    + " "
    "WHAT THE MECHANISM IS, and why it is a rules-1/14 measured replacement "
    "rather than a lever. SUMMER_WEFOR_SHARE = 0.30 is a self-declared UNCITED "
    "A-PRIORI HEURISTIC (fuel_trajectories.py's own words) that removes 70% of "
    "every non-coal thermal unit's forced-outage rate from Jun-Sep and shifts "
    "it into the shoulder — the REVERSE of the physical sign for forced "
    "outages, which correlate positively with heat and load. Its declaration "
    "names its sole exit: a measured seasonal forced-outage shape clearing "
    "docs/handoffs/miso-outage-grain-data-ask-2026-07.md. THE PROVENANCE GATE "
    "WAS TAKEN BY THE OWNER (2026-08-16, that ask's §9): MISO's published "
    "ticket-based MOM outage record adjudicates the forced-outage seasonal "
    "shape (clears the ask's §2 A/C/D/E); CAMPD is inadmissible for outage "
    "measurement (output-derived — the ask's own §2A ground; documented "
    "phantom-outage bias; ZERO CT_PEAKER windows); and §2a accepts FLEET-level "
    "grain for this one deliverable, because replacing a fleet-uniform scalar "
    "invents no unit/class attribution (the miso-85/87 closures are "
    "untouched). THE DERIVED VALUE (rule 23, cites the data, never a "
    "residual): R* = 1.0599 = the unweighted mean over 2023/2024/2025 of "
    "[Jun-Sep mean offline MW / annual mean offline MW], region MISO, causes "
    "Derated+Forced+Unplanned (the GADS EFOR-family basis the WEFOR table "
    "carries, which includes equivalent derated hours), through the PRODUCTION "
    "loader miso_outage_mw_series; per-year 1.1039/0.9671/1.1086, "
    "V1-reproducing miso-157's published composite to <=0.0004; basis fixed in "
    "the PREREG before the number was computed; no sweep, no alternative "
    "basis tried. Probe scripts/probes/_miso160_wefor_shape_instrument.py; "
    "record results/calibration/_miso160_wefor_shape_instrument.json; unit "
    "tests tests/unit/config/test_miso160_summer_wefor_override.py (4/4). "
    "PHASE-0/1 GATES: V1 PASS 3/3; V2 bit-identical (above); V3 fleet "
    "identity PASS both arms (n_gen 2929/2923/2923, 6 carry zones); V4a "
    "winter invariance EXACTLY 0.0 all units all years; V4b per-unit "
    "annual-mean conservation <=1.3e-17; V5/S-CACHE PASS (default key "
    "unmoved vs HEAD, armed key distinct). S-CONSERVE FIRED ONCE AND THE "
    "DEFECT WAS THE INSTRUMENT'S OWN, disclosed: the probe's first month "
    "masks used the real 2024 leap calendar against the model's fixed "
    "non-leap clock (240 mis-labelled hours); rebuilt on the production "
    "_hour_to_month_index and re-run, R* unchanged at 1.0599. "
    "MEASURED REACH (arm - control, production arrays): Jun-Sep thermal "
    "capability -3.46 / -3.59 / -3.67 GW (2025 by class: CT_PEAKER -1.541, "
    "ST_GAS -0.951, CC_REGULAR -0.943, CHP classes -0.23); top-200 Jun-Sep "
    "demand hours -3.62 / -3.72 / -3.69 GW; winter untouched; annual mean "
    "conserved (final-array residue <=0.12 GW, the multiplicative overlay "
    "interaction, reported not gated). "
    "DIRECTION DISCLOSED IN ADVANCE (PREREG P-3): prices UP in all three "
    "years toward the failing gate, summer-concentrated — measured "
    "+3.83/+4.18/+3.98% Jun-Sep demand-weighted, +0.68/+0.68/+0.69% annual "
    "(the shoulder leg gives back the conserved outage energy, as the "
    "mechanism requires). P-3'S MAGNITUDE BANDS MISSED HIGH and the miss is "
    "reported at full size: 2025 annual registered +2.5 to +9%, measured "
    "+0.69% — the reach was exactly as predicted (P-2 inside its band), but "
    "the price response per removed GW is far below the miso-159 episode's "
    "(that repair removed capability in ALL hours including the binding "
    "shoulder; this one removes summer capability into a cushion that is "
    "deep, ~6.3 GW within $20/MWh, and RETURNS capability to the shoulder). "
    "NONE of the residual improvement is claimed as calibration skill; "
    "adoption grounds are rules 1/14 — a measured, owner-adjudicated input "
    "replacing an uncited heuristic on the price-setting availability path. "
    "A PREREG BOOKKEEPING MISS, disclosed: PREREG §2 said the ledger's "
    "residual count falls 2 -> 1, on the standing description of "
    "SUMMER_WEFOR_SHARE as 'in the DOF ledger under identification "
    "residual'. The committed ledger carries NO separate entry for the "
    "share — it is tracked as an open rule-20 root-cause item in the "
    "governance prose (miso-159's attested_by), and the two residual entries "
    "are the offer-curve pair. So: entries 30 -> 31 (the new derived entry "
    "below), n_residual UNCHANGED at 2, and the open root-cause item on the "
    "share is RETIRED for MISO — the honest form of the improvement the "
    "PREREG described."
)

_DOF_ENTRY = {
    "name": "summer_wefor_share_override",
    "where": "run_config.scenario_config.summer_wefor_share_override",
    "identification": "derived-measured",
    "lineage_solves": "1 (this arm; no sweep, no variant)",
    "value": 1.0599,
    "note": (
        "ZERO CONTINUOUS DOF IN THE RULE-21 SENSE: one derived constant whose "
        "value is the pooled 2023-2025 Jun-Sep/annual ratio of MISO's "
        "published MOM outage record's unplanned offline MW "
        "(Derated+Forced+Unplanned), computed by a fixed pre-registered "
        "procedure through the production loader — no tunable scale, window "
        "or tolerance, and no residual entered its identification. Replaces "
        "the uncited SUMMER_WEFOR_SHARE=0.30 heuristic for MISO only (rule "
        "25; the constant stays the default elsewhere). Rule 13/14 forward "
        "story: the pooled seasonal shape regenerates from the same record "
        "for any window (the MAINTENANCE_MONTHLY_SHAPE pattern) and responds "
        "to changed conditions through each unit's own WEFOR level. Rule 23: "
        "re-derive only on a source-data update, never on a residual."
    ),
}


def _build(note: str, armed: bool) -> dict:
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att["governance"] = dict(att["governance"])
    att["governance"]["attested_by"] = note
    if armed:
        fp = att["free_parameters"]
        fp["entries"] = list(fp["entries"]) + [_DOF_ENTRY]
        fp["n_entries"] = len(fp["entries"])
        # n_residual UNCHANGED: the new entry is derived-measured, and the
        # ledger's two residual entries (the offer-curve pair) are untouched.
    return att


def main() -> None:
    for bundle, note, armed in (
        (CONTROL, CONTROL_NOTE, False),
        (ARM, ARM_NOTE, True),
    ):
        att = _build(note, armed)
        out = bundle / "calibration_attestation.json"
        out.write_text(json.dumps(att, indent=1) + "\n")
        print(
            f"wrote {out.relative_to(REPO)} "
            f"(dof entries {att['free_parameters']['n_entries']}, "
            f"residual {att['free_parameters']['n_residual']})"
        )


if __name__ == "__main__":
    main()
