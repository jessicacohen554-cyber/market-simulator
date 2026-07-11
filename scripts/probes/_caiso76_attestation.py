"""Write the caiso-76 probe attestations (main + ablation twin).

Derives each bundle's ``calibration_attestation.json`` from the caiso-75
attestation already committed in the repo (same lever set and DOF ledger —
the probe adds no free parameter: both hydro switches select a measured
source series, they carry no tunable value), swapping the ``attested_by``
line and appending the probe's single-delta note. Deterministic from repo
state, so the CI solve-register workflow reproduces byte-identical
attestations to any session verification copy
(_caiso7475_attestations.py pattern).

Usage: python scripts/probes/_caiso76_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso75_demand_clock" / "calibration_attestation.json"

DELTA76 = (
    " PLUS the single caiso-76 delta: hydro_backfill_year=2024 + hydro_eia930_monthly=True — the "
    "measured conventional-hydro budget correction "
    "(FINDING-caiso76-hydro-budget-2026-07-11): the 2025 EIA-923 vintage is a monthly-survey-only "
    "early release carrying 26 of ~185 CAISO hydro plants (12.32 of the measured 21.32 TWh, "
    "EIA-930 NG: WAT); the missing 9.0 TWh of zero-carbon inflow was being served by gas "
    "(the C2 2025 +6.5% excess), imports and un-curtailed solar. The correction backfills "
    "non-reporting plants at their 2024 monthly generation (per-plant coverage + MW envelope) and "
    "repins each year's monthly budget to the measured EIA-930 NG: WAT total "
    "(2023 23.90->24.40, 2024 21.48->22.68, 2025 12.32->21.32 TWh) — the existing early-release "
    "machinery (NEISO-2025 precedent), first keeper-line use. Zero fitted parameters: both "
    "switches select a measured source series; level and shape are EIA-930; never pinned to a "
    "dispatch outcome (the LP still chooses when to release water within the measured "
    "hydro_dispatch_envelope). Forward story: forecast path keeps its climatology budget; the "
    "correction regenerates on the early-release cadence and dies when the final 923 lands. "
    "DISCLOSED: with backfill_year=2024, 2023 carries 5 plants (+0.42 TWh pre-repin) absent from "
    "its final vintage — the 930 repin rescales the total back to the measured 24.40 TWh; CISO "
    "NG: WAT includes PS net output (no separate PS series), the same like-for-like note as the "
    "envelope cap. No residual-tuned adder is armed in this run. The rule-1-sanctioned "
    "offer-curve tuning surface remains as disclosed in the free_parameters DOF ledger; no new "
    "fit was performed in or for this run."
)

TARGETS = [
    (
        "caiso76_hydro_budget",
        "caiso-76 measured 2025 hydro budget correction probe session 2026-07-11",
        DELTA76,
    ),
    (
        "caiso76_hydro_budget-ablation",
        "caiso-76 zero-forcing ablation twin session 2026-07-11",
        DELTA76,
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
        d["governance"]["note"] = d["governance"]["note"] + DELTA76
        (out_dir / "calibration_attestation.json").write_text(json.dumps(d, indent=1))
        print(f"[ok  ] {bundle}")


if __name__ == "__main__":
    main()
