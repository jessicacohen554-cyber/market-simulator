"""Write the caiso-74/75 probe attestations (main + ablation twins).

Derives each bundle's ``calibration_attestation.json`` from the caiso-73
attestation already committed in the repo (same lever set and DOF ledger —
neither probe adds a free parameter), swapping the ``attested_by`` line and
appending the probe's single-delta note. Deterministic from repo state, so
the CI solve-register workflow reproduces byte-identical attestations to the
session's local verification copies.

Usage: python scripts/probes/_caiso7475_attestations.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso73_firm_shape" / "calibration_attestation.json"

DELTA74 = (
    " PLUS caiso_firm_import_shape=True (the caiso-73 delta, carried) PLUS the single "
    "caiso-74 delta: caiso_storage_as_reservation=True — the measured CAISO battery AS-award MW "
    "(Daily Energy Storage Report quarterly data, storage-as-awards clean datatype; DA/IFM LESR "
    "awards 1,010/1,484/1,652 MW avg 2023/24/25, matching DMM-published 1,040/1,500 MW to ~1%) "
    "reserved from the battery power cap pro-rata (ERCOT storage_as_commitment pattern, batteries "
    "only) with the SOC floored at the tariff 30-min sustain (CAISO_AS_SUSTAIN_DURATION_H=0.5h, "
    "the reserve co-opt's own cited constant) of the spin/non-spin award. Zero fitted parameters: "
    "level and shape are the published award series; a capability bound the LP dispatches beneath, "
    "never a price adder, never pinned to actuals. MEASURED OUTCOME: ex-ante inert on the "
    "zone-aggregate fleet (LP battery discharge peaks 3.7-6 GW below the nameplate cap, so the "
    "0.7-2.8 GW derate never binds; dispatch identical to caiso-73 to 0.01 TWh). No residual-tuned "
    "adder is armed in this run. The rule-1-sanctioned offer-curve tuning surface remains as "
    "disclosed in the free_parameters DOF ledger; no new fit was performed in or for this run."
)

DELTA75 = (
    " PLUS caiso_firm_import_shape=True (the caiso-73 delta, carried) PLUS the single "
    "caiso-75 delta: caiso_demand_clock_realign=True — the measured source-data clock correction "
    "to the 2023 CAISO demand input (FINDING-caiso75-demand-clock-2026-07-11): the EIA-930 CISO "
    "Demand column is +1h late vs the extract's own astronomy-verified generation frame for local "
    "dates before 2023-11-01 (monthly best-lag -1 at r 0.984-0.997 against the extract's balance "
    "identity net_gen - interchange; the OASIS SLD TAC actual corroborates at 0.9953), aligned "
    "thereafter. The realignment pulls that window forward 1h onto the wall-true frame; annual "
    "energy conserved to +0.1 MW on the mean — a rule-14 reconciled-real-data clock fix, never a "
    "level rescale, zero fitted parameters, window frozen against residuals (rule 23) and guarded "
    "by scripts/validate_caiso_demand_clock.py. caiso_storage_as_reservation is NOT carried "
    "(measured ex-ante inert in caiso-74; caiso-71 precedent). No residual-tuned adder is armed "
    "in this run. The rule-1-sanctioned offer-curve tuning surface remains as disclosed in the "
    "free_parameters DOF ledger; no new fit was performed in or for this run."
)

TARGETS = [
    (
        "caiso74_storage_as",
        "caiso-74 measured battery AS-award reservation probe session 2026-07-11",
        DELTA74,
    ),
    (
        "caiso74_storage_as-ablation",
        "caiso-74 zero-forcing ablation twin session 2026-07-11",
        DELTA74,
    ),
    (
        "caiso75_demand_clock",
        "caiso-75 measured 2023 demand-clock realignment probe session 2026-07-11",
        DELTA75,
    ),
    (
        "caiso75_demand_clock-ablation",
        "caiso-75 zero-forcing ablation twin session 2026-07-11",
        DELTA75,
    ),
]


def main() -> None:
    """Derive and write the four probe attestations."""
    base = json.loads(BASE.read_text())
    for bundle, attested_by, delta in TARGETS:
        out_dir = ROOT / bundle
        if not out_dir.exists():
            print(f"[skip] {bundle}: bundle dir absent")
            continue
        d = json.loads(json.dumps(base))
        d["governance"]["attested_by"] = attested_by
        head = d["governance"]["note"].split(" PLUS the single caiso-73 delta:")[0]
        d["governance"]["note"] = head + delta
        (out_dir / "calibration_attestation.json").write_text(json.dumps(d, indent=1))
        print(f"[ok  ] {bundle}")


if __name__ == "__main__":
    main()
