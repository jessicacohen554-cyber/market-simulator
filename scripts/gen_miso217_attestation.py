"""Generate the miso-217 ARM leg's calibration attestation from the keeper's.

The gen_miso186/.../213 pattern. The arm is the miso-213 keeper recipe re-solved
via ``scripts/replay_keeper.py --set miso_intermediate_gas_offer_margin=true``
(single delta). The CONTROL is the keeper bundle itself (``miso213_layering_B``,
already attested, never re-solved), so only the arm's attestation is written: the
keeper's with a rewritten ``governance.attested_by`` and this session's
disclosures appended AT FULL MAGNITUDE.

**No new ledger entry.** The arm introduces no parameter: it supplies an EXISTING
mechanism (``gas_offer_net_revenue_margin``) with the PARENT class's
already-registered, already-frozen ``phys_econ_*`` on three classes its own merge
list omitted — coverage, not a lever (rule 19 [R-ONE-MECH]). ``n_entries`` stays
41 and ``n_residual`` 2.

Run this INSTEAD of ``scripts/build_dof_ledger.py`` (which would drop the
documented entries), and because a replay solve writes NO attestation at all —
the miso-200 vacuous-pass trap, which bit this session in its mirror image: the
first scoring pass ran on a bundle with no attestation, so C6 read UNATTESTED,
guard (b) of the C3c standing rule blocked the reclassification, and C3c scored
FAIL x3 on values BYTE-IDENTICAL to the control's. See DISCLOSURE (3).

Usage:
    python3 scripts/gen_miso217_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/miso213_layering_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso217_intermphys_B"
GATES = REPO / "results/calibration/_miso217_ab_gates.json"

DISCLOSURE = (
    "REPORTED AT FULL MAGNITUDE. (1) THE DEFECT: gas_offer_net_revenue_margin "
    "merges its phys_* keys onto exactly five gas classes (CC_REGULAR, CC_CHP, "
    "CT_CHP, CT_PEAKER, ST_GAS), so the three duty-split *_INTERMEDIATE curves "
    "the armed splits route to carry NONE of them, gas_offer_margin_markup_mult "
    "returns its documented rule-24 neutral 0.0 for every band, and the mechanism "
    "SKIPS 38,501.0 MW = 58.4 % of MISO's assembled gas capacity — leaving it in "
    "the fully fuel-scaled multiplier form the mechanism exists to replace "
    "(measured miso-215 §2). (2) THE REPAIR: one MISO-gated default-off "
    "ScenarioConfig field, miso_intermediate_gas_offer_margin, resolving at "
    "data/offer_curves._offer_curve_for_group (fleet-assembly time, so a "
    "replay --set actually fires) and returning a COPY carrying the PARENT "
    "class's own phys_econ_low / phys_econ_high. ECON-ONLY by design, frozen in "
    "the PREREG before the solve. ZERO FREE PARAMETERS, no new ledger entry "
    "(41 -> 41, n_residual 2 -> 2); the borrowing is VALIDATED, not assumed — each "
    "cohort's own CEMS-measured marginal-HR multiplier lands within 0.0344 / "
    "0.0388 / 0.0149 of the parent midpoint it borrows against a +-0.06 bar, on "
    "94-100 % of the cohort's capacity (miso-215 §3). Registered in "
    "_CACHE_KEY_OPTIONAL_FIELDS at its default, which the repo's three cache-key "
    "freeze tests caught: without it the pinned default key moved off "
    "4c6b03ae098b6e3e and would have orphaned every cached run. (3) THE FIRST "
    "SCORING PASS FIRED K-4, AND IT WAS AN INSTRUMENT CONDITION, NOT A MODEL "
    "RESULT — disclosed rather than renegotiated. A replay writes no attestation, "
    "so the arm's C6 read UNATTESTED; guard (b) of the C3c standing rule requires "
    "governance to PASS, so C3c did not reclassify and scored FAIL in all three "
    "years. THE C3c VALUES ARE BYTE-IDENTICAL BETWEEN THE LEGS: 3 vs 30, 7 vs 37, "
    "0 vs 88 hours of RT-expressible LMP > $200/MWh in 2023/2024/2025. The arm "
    "did not move the price tail at all. This attestation is what the gate was "
    "missing; the re-score is reported beside the first pass, both in the record. "
    "(4) S-2 LIVENESS, measured BEFORE the solve: exactly 534 tranches gain a "
    "markup — 264 CT_INTERMEDIATE + 234 CC_INTERMEDIATE + 36 ST_GAS_INTERMEDIATE, "
    "the PREREG's P-1 bar to the unit — every one positive, ZERO existing markups "
    "moved, ZERO changes outside the econ band, and mc changes confined to exactly "
    "those 534 rows (max |dmc| on every other row 0.0). Cap-weighted fixed margins "
    "installed: CT_INTERMEDIATE $14.20/MWh, ST_GAS_INTERMEDIATE $7.48, "
    "CC_INTERMEDIATE $1.51. (5) THE C1 COST, AT FULL MAGNITUDE. The largest movers "
    "(control -> arm, TWh): CT_PEAKER-2024 -0.884 -> -3.634, COAL_PRB-2024 -3.166 "
    "-> -2.159, CT_PEAKER-2023 -5.121 -> -5.934, CC_REGULAR-2024 +7.419 -> +7.947, "
    "CC_REGULAR-2023 -2.774 -> -2.288. NO BAND EXIT (K-1 silent) — but the "
    "PRE-REGISTERED, EXPLICITLY UN-INSTRUMENTED RISK MATERIALISED: the "
    "cross-class backfill the static screen cannot see consumed 91 % of "
    "CC_REGULAR-2024's headroom, 0.581 -> 0.053 TWh. (6) C8: CT_PEAKER forced "
    "share 0.2044/0.1218/0.1421 -> 0.2280/0.1573/0.1319 — 2023 rises further above "
    "the 0.15 peaker budget and 2024 CROSSES IT, while 2025 falls. K-2 is silent "
    "as pre-registered because rule 20's conditional provenance+shape route still "
    "clears (zero new D-4 failures, zero new D-1 failures on CT_PEAKER), but the "
    "budget crossing is a real cost of the arm and is named here, not buried. "
    "(7) C3a, REPORTED AND NEVER THE JUSTIFICATION (rule 1 [R-STRUCT]): "
    "+0.9132 -> +1.0959 (+0.183 pp, AWAY from zero), -3.839 -> -2.879 (+0.960, "
    "toward), -11.7466 -> -12.2965 (-0.550, AWAY). The PREREG predicted "
    "|dC3a-2025| < 0.5 pp and measured 0.550 — the prediction is WRONG by 0.05 pp "
    "and is scored so. (8) THE ARM'S OWN FORM FOOTPRINT (PREREG §6), like-for-like "
    "on the ECON band: CT_INTERMEDIATE 14.97 % of its own cap-weighted offer "
    "against CT_PEAKER's already-accepted 19.19 % — 4.22 pp BELOW, so §6's "
    "disposition does not fire. But ST_GAS_INTERMEDIATE is 15.36 % against "
    "ST_GAS's 6.24 %, +9.12 pp ABOVE its parent; the disposition as pre-registered "
    "keys on the CT cohort only and does not reach it. That is a scope limit of my "
    "own PREREG, disclosed, not renegotiated."
)


def build(dst: Path, gates: dict) -> None:
    d = json.loads(SRC.read_text())
    d["governance"]["attested_by"] = (
        "miso-217 A/B (2026-09-05), ARM leg B (miso_intermediate_gas_offer_margin "
        "False -> True): control = the miso-213 keeper bundle miso213_layering_B "
        "itself (already attested, never re-solved) vs arm miso217_intermphys_B, "
        "MISO 2023+2024+2025 in one invocation, years sequential, solved "
        "in-session and never on CI (rules 12/16), from the SAME committed keeper "
        "recipe via replay_keeper --set. The delta is ONE ScenarioConfig field "
        "(rule 24 registry) supplying an EXISTING mechanism with the parent gas "
        "class's already-frozen phys_econ_* on three classes its merge list "
        "omitted — coverage, not a lever (rule 19 [R-ONE-MECH]); zero free "
        "parameters, no new ledger entry. Scored by "
        "scripts/probes/_miso217_ab_gates.py, COMMITTED BEFORE THE SOLVE with "
        "every band frozen from the PREREG and the control's own committed "
        "verdict; S-0 inherited, S-1 single delta, S-2 liveness measured before "
        "the solve, K-1..K-6. " + str(gates.get("verdict", "verdict pending"))
    )
    d.setdefault("disclosures", {})["miso217_ab"] = DISCLOSURE
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


if __name__ == "__main__":
    if not GATES.exists():
        raise SystemExit(f"refusing to write: {GATES} does not exist — score first.")
    build(ARM / "calibration_attestation.json", json.loads(GATES.read_text()))
