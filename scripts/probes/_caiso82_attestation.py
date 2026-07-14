"""Write the caiso-82 probe attestations (main + ablation twin).

Derives each bundle's ``calibration_attestation.json`` from the caiso-80
keeper attestation already committed in the repo (same lever set and DOF
ledger — the probe adds no free parameter: the single delta is the gated
``hydro_dispatch_floor`` measured min-flow floor,
FINDING-caiso82-soft-month-margin-2026-07-14 S4), swapping the
``attested_by`` line and appending the probe's single-delta note.
Deterministic from repo state (_caiso76/77/78/80_attestation.py pattern).

Usage: python scripts/probes/_caiso82_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso80_supply_consistent_demand" / "calibration_attestation.json"

DELTA82 = (
    " PLUS the single caiso-82 delta: hydro_dispatch_floor=True "
    "(FINDING-caiso82-soft-month-margin-2026-07-14 S4). The budget-hydro fleet's "
    "hourly dispatch is floored at the measured per-(month x hod) p05 of the ISO's "
    "EIA-930 NG:WAT (constants.HYDRO_FLOOR_PERCENTILE, the symmetric complement of "
    "the armed p95 deliverability envelope), distributed pro-rata to each unit's "
    "monthly budget share and clipped at unit capability and 0 — run-of-river / "
    "FERC-license minimum-release physics: measured CISO p10 hourly WAT stays at "
    "0.8-2.2 GW in every month 2023-2025 while the budget LP vacates the troughs to "
    "0.0-0.9 GW and back-fills them with gas/carbon-rung imports at $40-65 against "
    "actual prices at/below WECC hub parity. Zero new free parameters, zero fitted "
    "values: the percentile mirrors the envelope's, the level is each year's own "
    "measured series (forecast: pooled HYDRO_CLIMATOLOGY_YEARS x hydro_year budget), "
    "re-derives only on source updates (rule 23), never an output pinned back "
    "(rule 14 — the floor is a capability/obligation bound the LP dispatches above, "
    "monthly energy stays pinned to the same measured budget as the keeper). "
    "Mechanism MECH_HYDRO_MINFLOW: non-thermal must-flow (MECH_FIRM_IMPORT class), "
    "excluded from merchant forced-share gates, reported by D-2, D4_WINDOWS all-hours "
    "by measurement, ablated in the zero-forcing twin. Estimation-stage honesty gates "
    "passed BEFORE the solve (FINDING S2): floor fits inside every measured monthly "
    "budget (60-87%, all 36 month-years) and the normalized shape is year-stable "
    "(r 0.79-0.89, p05/mean 0.75 +/- 0.01 across a wet and two drier years). "
    "Pre-registered directions are in FINDING S4, incl. the disclosed 2023 smoke "
    "result that the floor is ~price-inert at the monthly mean (the promotion case "
    "is rule-1 structural fidelity with gates holding, the caiso-72 envelope "
    "precedent — not fit improvement). No residual-tuned adder is armed in this run."
)

TARGETS = [
    (
        "caiso82_hydro_minflow",
        "caiso-82 hydro min-flow floor probe session 2026-07-14",
        DELTA82,
    ),
    (
        "caiso82_hydro_minflow-ablation",
        "caiso-82 zero-forcing ablation twin session 2026-07-14",
        DELTA82,
    ),
]


def main() -> None:
    """Derive and write the two probe attestations."""
    base = json.loads(BASE.read_text())
    for bundle, attested_by, delta in TARGETS:
        out_dir = ROOT / bundle
        if not out_dir.exists():
            print(f"[skip] {bundle}: bundle dir absent")
            continue
        d = json.loads(json.dumps(base))
        d["governance"]["attested_by"] = attested_by
        d["governance"]["note"] = d["governance"]["note"] + delta
        (out_dir / "calibration_attestation.json").write_text(json.dumps(d, indent=1))
        print(f"[ok  ] {bundle}")


if __name__ == "__main__":
    main()
