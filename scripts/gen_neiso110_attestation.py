"""Governance attestation for the neiso-110 keeper candidate (session ``neiso-110``).

neiso-110 is the committed ``neiso109_gasrepair_span`` recipe replayed full-span
2020-2025 with **exactly one config delta**,
``neiso_coldsnap_derate_dualfuel_unswitched=True``, promoted on the owner ruling
of 2026-09-16. The attestation therefore carries neiso-109's governance forward
unchanged and adds only what this session did.

Rule 21 ``[R-DOF]``: the promoted change adds **no free parameter**. It is a
SCOPE CORRECTION to an existing mechanism — ``neiso_gas_coldsnap_derate`` — that
introduces no floor, no curve and no scalar, and leaves every coefficient of the
parent derate untouched (``t0`` -7.0 C / ``slope`` 0.018 per C / ``cap`` 0.20),
so rule 23 ``[R-FROZEN-DERIVE]`` is not engaged either. ``n_entries`` and
``n_residual`` are untouched.

Why it is promoted, stated so it cannot be read as an accuracy claim: the parent
derate exempts every EIA-860 dual-fuel unit on the premise that
``apply_dual_fuel_pricing`` has switched it to oil. That switch is
``mc = min(gas, oil)``, so it fires only where delivered gas has reached the oil
parity. Across Winter Storm Elliott (2022-12-23..27) Algonquin gas ran
$12.54-15.08/MMBtu against an oil parity of $20.985 -- the switch was
$5.9-8.4/MMBtu from firing -- while 6,896 MW (39.3 % of NEISO gas capacity) sat
exempt from a physical fuel-availability constraint. The correction conditions
the exemption on its own premise. Rule 1 ``[R-STRUCT]``: it is promoted for
structural fidelity, and the measured effect is reported at full magnitude as
IMMATERIAL (below).

Usage::

    python3 scripts/gen_neiso110_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results/calibration/neiso109_gasrepair_span/calibration_attestation.json"
DST = ROOT / "results/calibration/neiso110_dualfuel_span/calibration_attestation.json"

NEISO110 = {
    "session": "neiso-110 (2026-09-16)",
    "incumbent": "2026-09-16-neiso109-gas-repair",
    "charter": "docs/CHARTER-neiso110-winter-oil-driver-2026-09-16.md",
    "prereg": "docs/PRECOMMIT-neiso110-coldsnap-dualfuel-2026-09-16.md",
    "lineage": [
        "docs/FINDING-neiso110-winter-oil-driver-2026-09-16.md",
        "docs/RESULT-neiso110-coldsnap-dualfuel-screen-2026-09-16.md",
    ],
    "owner_ruling": (
        "2026-09-16, verbatim: 'Is this a recommended keeper candidate? If so plz promote. "
        "If structural integrity improves but gates regress that may still be a keeper.' "
        "Structural integrity improves and NO gate regresses, so the ruling's weaker limb is "
        "not even needed; the promotion rests on rule 1 [R-STRUCT], never on the residual."
    ),
    "config_delta_vs_incumbent": [
        "neiso_coldsnap_derate_dualfuel_unswitched: False -> True"
    ],
    "free_parameters_added": 0,
    "free_parameters_rationale": (
        "A scope condition on one existing mechanism. No floor, no curve, no scalar, no "
        "adder; the parent derate's t0/slope/cap are byte-identical, so rule 23 "
        "[R-FROZEN-DERIVE] is not engaged. The condition is the gas-vs-oil-parity comparison "
        "apply_dual_fuel_pricing already computes -- it introduces no new quantity."
    ),
    "rule_17_floor_window": {
        "driver": (
            "The gas-electric pipeline constraint in deep cold (NERC/FERC Winter Storm "
            "Elliott analysis) -- INHERITED UNCHANGED from the parent derate. It is the "
            "EXEMPTION that carried no driver evidence."
        ),
        "window": (
            "INHERITED UNCHANGED: NEISO_COLDSNAP_FLOOR_HOURS (hours 6-9, 17-20) on days "
            "whose NEISO load-weighted daily TMIN is below neiso_gas_derate_t0_c. No new "
            "window is introduced; out-of-window frac is identically 0 by construction."
        ),
        "forward": (
            "INHERITED UNCHANGED: regenerates from a forecast year's pinned TMIN, and the "
            "switch condition regenerates from the same forward gas/oil series the parity "
            "test already uses."
        ),
    },
    "rule_19_one_mechanism": (
        "REPLACES an unconditional exemption with a conditional one inside the SAME "
        "mechanism; it does not stack a second derate. Where the exemption's premise holds "
        "the arm is BYTE-IDENTICAL to the legacy path (guarded by tests/iso/neiso/"
        "test_neiso_coldsnap_dualfuel_exemption.py::test_switch_always_active_is_byte_"
        "identical_to_legacy), so it can only remove an exemption that was never earned."
    ),
    "measured_effect_reported_at_full_magnitude": {
        "verdict": "IMMATERIAL. Promoted for structural fidelity, NOT for accuracy.",
        "oil_gap_closed_pct_by_year": {
            "2020": 0.01,
            "2021": 0.05,
            "2022": 0.10,
            "2023": 0.01,
            "2024": 0.00,
            "2025": 0.02,
        },
        "oil_twh_delta_total": 0.00154,
        "c3a_pct_control_to_arm": {
            "2020": [4.109, 4.137],
            "2021": [-0.440, -0.405],
            "2022": [-6.205, -6.120],
            "2023": [-5.476, -5.432],
            "2024": [-3.328, -3.306],
            "2025": [-5.093, -5.071],
        },
        "c3a_note": (
            "Improves in 5 of 6 years; 2020 moves 0.028 pp further from the bench. Every "
            "move is < 0.09 pp and none approaches a band edge."
        ),
        "no_regression": (
            "slack and dump delta 0.0000 in all six years; hours >$300 = 0 in both legs in "
            "all six years; reserve-co-opt dual nonzero in 0 of 26,280 family-hours per "
            "year in BOTH legs (the co-opt was already dormant and remains so); D1/D2/D4 "
            "legitimacy statuses identical to the incumbent; largest non-oil class move "
            "0.0033 TWh against ~100 TWh of load."
        ),
        "what_it_does_not_fix": (
            "The winter oil miss is UNCHANGED as a model miss and stays ledgered. The "
            "measured reason is in the RESULT: at Elliott the model's minimum thermal "
            "headroom is 6,959 MW against a 3,600 MW reserve requirement -- 3,359 MW clear "
            "of binding -- while derating 100 % of ALL NEISO gas would remove only 1,985 MW. "
            "No admissible magnitude of this mechanism family can produce a reserve-short "
            "hour, so the derate channel is not the explanation for the missing price tail."
        ),
    },
    "solve_provenance": {
        "solved_by": "span shard session_01A6aTizYouZELNWHJE2BZRT",
        "shard_branch": "claude/neiso110-span-2020-2025",
        "shard_commit": "0d0004e197c205d6c7ea6d634d1a252f0fc86244",
        "pinned_source_revision": "c0916408bf1d69a8c8b249a76c6716ab024b1b29",
        "years": [2020, 2021, 2022, 2023, 2024, 2025],
        "control": (
            "No control solve spent. G-DRIFT form 4: every changed hunk between the "
            "incumbent's basis_sha b6ded93731fec2a0680a6bb7bf30d6c7caab7656 and HEAD "
            "classifies INERT for a NEISO backcast (hydro-cascade and coal-fuel-inventory "
            "default-off gates, SOCO/NWPP scoping, a PJM-only offer gate, a DEFAULT_ISO_ORDER "
            "display append, and a calibration_reference.json delta with 22 SOCO lines and 0 "
            "NEISO/ISNE lines). Corroborated mechanically: surface_stamp('NEISO') reproduces "
            "the incumbent's fingerprint 9d35c270c69e9eee, 197 rows, moved {}, at HEAD."
        ),
        "shared_inputs_provenance": (
            "The bundle's eight content-addressed shared inputs were regenerated in the "
            "parent with --rebuild-benchmark (no re-solve) and every one hashes IDENTICAL to "
            "the incumbent's: eia930-a79ecddc812c, eia923-c06a87821698, campd-1782e1223554, "
            "unit_outages-c6be5bbb89ab, unit_outages_short-849e1d0a5f28, "
            "unit_outages_partial-b00540584f5f, unit_outages_e923-eec106f23392, "
            "unit_outages_layup-c622c4d5058e."
        ),
    },
    "test_baseline": (
        "Zero regressions, measured not assumed: tests/unit + tests/scoring + tests/regression "
        "run in full on the branch and compared test-by-test against a clean origin/main "
        "checkout of the same 20 files -- 64 failures on each, sets identical member-for-member "
        "(both comm directions empty). The cache-key pin is unmoved "
        "(test_caiso_ra_mpb_anchor.py) because the new field is registered in "
        "_CACHE_KEY_OPTIONAL_FIELDS + _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS at 'False'."
    ),
}


def main() -> None:
    """Write neiso-110's attestation by carrying neiso-109's forward + this delta."""
    att = json.loads(SRC.read_text())
    att["neiso110"] = NEISO110
    DST.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {DST.relative_to(ROOT)}")
    print(
        f"  free_parameters.n_entries  = {att['free_parameters']['n_entries']} (unchanged)"
    )
    print(
        f"  free_parameters.n_residual = {att['free_parameters']['n_residual']} (unchanged)"
    )


if __name__ == "__main__":
    main()
