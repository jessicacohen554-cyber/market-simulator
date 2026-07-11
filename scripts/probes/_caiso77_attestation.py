"""Write the caiso-77 probe attestations (main + ablation twin).

Derives each bundle's ``calibration_attestation.json`` from the caiso-76
keeper attestation already committed in the repo (same lever set and DOF
ledger — the probe adds no free parameter: the self-schedule floor reuses the
caiso-73 measured level x shape unchanged and carries no tunable value; it
REMOVES the influence of the two G-26 static-fitted firm prices from
dispatch), swapping the ``attested_by`` line and appending the probe's
single-delta note. Deterministic from repo state, so the CI solve-register
workflow reproduces byte-identical attestations to any session verification
copy (_caiso76_attestation.py pattern).

Usage: python scripts/probes/_caiso77_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso76_hydro_budget" / "calibration_attestation.json"

DELTA77 = (
    " PLUS the single caiso-77 delta: caiso_firm_import_selfschedule=True — the firm/contracted "
    "import blocks become must-flow at their shaped capability "
    "(FINDING-caiso77-c1-cluster-firm-selfschedule-2026-07-11): in the real market the RA/LTC "
    "import blocks are self-scheduled or bid at/below $0/MWh (CPUC D.20-06-028 RA import "
    "must-offer; the DMM-documented revealed 4.3-5.9 GW self-scheduled base) and flow independent "
    "of the hourly spot spread, but the model priced them at two G-26 static-fitted Tier-3 "
    "contract-cost proxies ($28/$48) — a price gate that deleted the overnight/evening contracted "
    "base (model -0.6..-2.3 GW vs measured) and left CC_REGULAR running flat overnight (the C1 "
    "CC-over/CT-under cluster: same-fleet CAMPD +6.2/+11.2/+14.3 TWh over, 2023-25). The floor "
    "sets each firm tranche's hourly min_gen to pmax x availability — the published DMM RA-import "
    "x MIC-split level x the measured unit-mean revealed-base shape (the keeper's existing "
    "caiso-73 inputs, eford preserved) — the exact Manitoba/HQ firm must-flow pattern "
    "(MECH_FIRM_IMPORT: a contract, ablation-kept, D-2 exempt by construction). Zero fitted "
    "parameters: no tunable value is introduced; the two static-fitted firm prices can no longer "
    "set the margin (pmin = pmax), so the probe strictly REDUCES the fitted surface. Forward "
    "story: the DMM forward ladder level and the pooled climatology shape regenerate in any "
    "forecast year. DISCLOSED: the C2-2025 family metric may print further negative on the "
    "current bench basis, which is itself inconsistent with same-year CEMS (FINDING S2 "
    "cross-basis note; bench rework filed) — adjudicated against the CEMS same-fleet evidence, "
    "never tuned to. No residual-tuned adder is armed in this run. The rule-1-sanctioned "
    "offer-curve tuning surface remains as disclosed in the free_parameters DOF ledger; no new "
    "fit was performed in or for this run."
)

TARGETS = [
    (
        "caiso77_firm_selfschedule",
        "caiso-77 self-scheduled firm import base probe session 2026-07-11",
        DELTA77,
    ),
    (
        "caiso77_firm_selfschedule-ablation",
        "caiso-77 zero-forcing ablation twin session 2026-07-11",
        DELTA77,
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
