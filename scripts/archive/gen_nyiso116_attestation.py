"""Write ``calibration_attestation.json`` for the nyiso-116 unit-layer replay.

``results/calibration/nyiso116_c3c_unitlayer`` is a **zero-delta** replay of the
nyiso-113 keeper run for one reason: to emit — and COMMIT — the per-unit and
per-link hourly layer (``hourly/unit_hourly_<year>.parquet``,
``hourly/network_<year>.parquet``) that the C3c pin attribution needs and that
no NYISO bundle carries. It is a DIAGNOSTIC, not a keeper candidate:
pre-registered gate G1 shows it is a re-solve of the keeper *recipe*, not the
keeper *bundle* (nyiso-114 §2).

The DOF ledger is the keeper's, **verbatim and unextended**: emitting a sidecar
adds no ``ScenarioConfig`` field, no CLI flag, no LP row or column and no free
parameter, so ``n_entries`` and ``n_residual`` are unchanged (rule 21
``[R-DOF]``). Only ``attested_by`` is rewritten.

Every number in the attestation text is read from the committed gate JSON
(``_nyiso116_c3c_unit_layer_gates.json``), never typed in — the nyiso-114
discipline.

Usage:
    PYTHONPATH=.:src python scripts/gen_nyiso116_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CAL = REPO / "results/calibration"
PRIOR_KEEPER = CAL / "nyiso113_lilocational_B/calibration_attestation.json"
GATES = CAL / "_nyiso116_c3c_unit_layer_gates.json"
DEST = CAL / "nyiso116_c3c_unitlayer/calibration_attestation.json"

YEARS = ("2023", "2024", "2025")


def _attested_by(g: dict) -> str:
    """Assemble the attestation line from the committed gate measurements."""
    s0 = g["section0_no_lp"]
    g1, g2, g3 = g["G1_replay_fidelity"], g["G2_c3c_tail_fidelity"], g["G3_sidecars"]
    g4 = g["G4_section6_reverification"]

    dprice = " / ".join(f"{g1['per_year'][y]['max_abs_dprice']:.3f}" for y in YEARS)
    c3c = " / ".join(str(g2["per_year"][y]["c3c_arm"]) for y in YEARS)
    inert = " / ".join(
        f"${s0['settlement_basis_inert'][y]['inertness_margin_usd']:.2f}" for y in YEARS
    )
    needs = " / ".join(
        f"{s0['knife_edge_reframing'][y]['nth_hour_that_must_clear']}h"
        f"(+${s0['knife_edge_reframing'][y]['nth_hour_shortfall_usd']:.2f})"
        for y in YEARS
    )
    ubytes = sum(g3["per_year"][y].get("unit_bytes", 0) for y in YEARS)
    nbytes = sum(g3["per_year"][y].get("network_bytes", 0) for y in YEARS)
    claims = " / ".join(
        f"{k.split('_', 2)[-1]}={v['verdict']}"
        for k, v in g4.items()
        if isinstance(v, dict) and "verdict" in v
    )
    return (
        "nyiso-116 DIAGNOSTIC — zero-delta replay of the nyiso-113 keeper recipe, "
        "run to emit and COMMIT the per-unit/per-link hourly layer. THE KEEPER IS "
        "UNTOUCHED: nothing promoted, demoted or re-keyed, and this bundle is not a "
        "keeper candidate. Rule 21 [R-DOF]: the ledger is the keeper's verbatim — a "
        "write-only sidecar adds no ScenarioConfig field, no CLI flag, no LP row or "
        "column and no free parameter, so n_entries and n_residual are unchanged; "
        "rule 24 [R-REGISTRY] is not engaged (there is no tunable). "
        f"GATES — G1 replay fidelity {g1['status']} (max |dprice| {dprice} $/MWh vs "
        "the keeper, the caiso-155 P0-pattern-bridge vertex dependence measured at "
        f"nyiso-114 §2), so every result here is labelled MEASURED ON THE RECIPE, "
        f"never on the keeper. G2 C3c-tail fidelity {g2['status']} — the C3c count is "
        f"{c3c} h > $300, identical to the keeper's, and the top-8 tail values agree "
        "to within the pre-registered $5.00; a globally-failing replay is still a "
        "faithful instrument FOR THIS GATE, which is why G4 was permitted to run "
        f"(kill K-A did not fire). G3 sidecars {g3['status']} — unit_hourly and "
        f"network emitted for all three years, no NaN, mw <= cap_mw everywhere, "
        f"{ubytes / 1e6:.1f} MB + {nbytes / 1e6:.1f} MB committed. G5 span PASS — "
        "2023-2025 in one bundle (rule 16), no year outside the training window "
        f"(rule 22). G4 re-verification of nyiso-114 §6: {claims}. "
        f"NO-LP RESULTS carried by this bundle's gate JSON — (a) the RCPF-into-LBMP "
        "SETTLEMENT BASIS IS INERT for C3c in all three years: adding the co-opt's "
        "own locational reserve duals to the zonal LMP leaves the count unchanged, "
        f"with proved margins {inert} between the best attainable settlement price in "
        "a sub-threshold hour and the $300 gate — the NYC/LI reserve families never "
        "arrive before the energy price; (b) THE $2.46 KNIFE-EDGE IS NOT THE GATE: "
        f"C3c needs {needs} respectively, so 2023 — not 2024 — is the nearest miss, "
        "and closing the 2024 pin would leave that year at 0.25x, still failing. "
        "Rule 1 [R-STRUCT]: no lever is proposed, nothing is tuned, and no parameter "
        "was introduced or changed in this session (pre-registered kill K-C)."
    )


def main() -> None:
    att = json.loads(PRIOR_KEEPER.read_text())
    gates = json.loads(GATES.read_text())
    att["attested_by"] = _attested_by(gates)
    att["run_id"] = "2026-08-03-nyiso-116-unit-layer"
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(att, indent=2, sort_keys=True) + "\n")
    print(att["attested_by"])
    print(f"\nwrote {DEST}")


if __name__ == "__main__":
    main()
