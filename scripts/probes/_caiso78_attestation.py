"""Write the caiso-78 probe attestations (main + ablation twin).

Derives each bundle's ``calibration_attestation.json`` from the caiso-77
keeper attestation already committed in the repo (same lever set and DOF
ledger — the probe adds no free parameter and no flag: the single delta is
the CODE-LEVEL ``fleet_to_bins`` heat-rate/capacity-basis fix, a correction
of a measured physical input), swapping the ``attested_by`` line and
appending the probe's single-delta note. Deterministic from repo state, so
the CI solve-register workflow reproduces byte-identical attestations to any
session verification copy (_caiso76/77_attestation.py pattern).

Usage: python scripts/probes/_caiso78_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso77_firm_selfschedule" / "calibration_attestation.json"

DELTA78 = (
    " PLUS the single caiso-78 delta, which is CODE-LEVEL, not a flag: the fleet_to_bins "
    "heat-rate/capacity-basis fix (FINDING-caiso78-cc-hr-basis-2026-07-12 S3). Under "
    "cc_nameplate_summer_derate (keeper-resolved True for CAISO) the plant base heat rate was "
    "divided by the nameplate-RESCALED capacity instead of the net-summer basis its "
    "capacity-weighted sum was accumulated on, deflating every CC plant's base heat rate — and "
    "every offer band built on it — by its own net-summer/nameplate ratio (Moss Landing -27%, "
    "Otay Mesa -17%, La Paloma -13%, the AES ECs -10/-11%; CAISO CC median -9%). The deflation "
    "was DIFFERENTIAL, scrambling the within-CC merit order: the C1 CC-over cluster is five "
    "deflated plants over-running (+1.9..+3.3 TWh each) with Pastoria, the least-deflated peer, "
    "under-running -1.7 TWh/yr in every year. Heat rate is an intensive measured property "
    "(the parquet value is the plant's real EIA/923 net heat rate, CEMS-consistent — Moss "
    "Landing 7.28 vs CEMS-gross 7.03); the deflation was an accounting error, not an estimate, "
    "so the fix is a rule-14 measured-input correction. Zero new free parameters, zero flags; "
    "the offer-curve multipliers are untouched (CAMPD-grounded RELATIVE bands, now multiplying "
    "the correct base). DISCLOSED counter-moves (pre-registered, FINDING S4): C3a/C3b print "
    "WORSE (the corrected marginal CC offer is ~10% higher — the deflated HR was silently "
    "compensating the body overprice, whose root cause stays an open lane), and the 930-family "
    "C2 rows may print further under while the CEMS same-fleet truth improves (adjudicated per "
    "the caiso-77 S5 posture). No residual-tuned adder is armed in this run. The "
    "rule-1-sanctioned offer-curve tuning surface remains as disclosed in the free_parameters "
    "DOF ledger; no new fit was performed in or for this run."
)

TARGETS = [
    (
        "caiso78_cc_hr_basis",
        "caiso-78 corrected CC heat-rate basis probe session 2026-07-12",
        DELTA78,
    ),
    (
        "caiso78_cc_hr_basis-ablation",
        "caiso-78 zero-forcing ablation twin session 2026-07-12",
        DELTA78,
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
