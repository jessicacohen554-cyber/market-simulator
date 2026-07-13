"""Write the caiso-80 probe attestations (main + ablation twin).

Derives each bundle's ``calibration_attestation.json`` from the caiso-78
keeper attestation already committed in the repo (same lever set and DOF
ledger — the probe adds no free parameter: the single delta is the gated
``caiso_supply_consistent_demand`` measured-input replacement, owner-signed
Option A of FINDING-caiso80-demand-basis-wedge-2026-07-13), swapping the
``attested_by`` line and appending the probe's single-delta note.
Deterministic from repo state, so the CI solve-register workflow reproduces
byte-identical attestations to any session verification copy
(_caiso76/77/78_attestation.py pattern).

Usage: python scripts/probes/_caiso80_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso78_cc_hr_basis" / "calibration_attestation.json"

DELTA80 = (
    " PLUS the single caiso-80 delta: caiso_supply_consistent_demand=True (owner-signed "
    "Option A, FINDING-caiso80-demand-basis-wedge-2026-07-13 S6). The CISO EIA-930 Demand "
    "cell — the model's backcast demand input — carries the same fabricated solar-shaped "
    "block as the corrupt NG cell by the Demand = NetGen + TI identity (onset 2024-05), "
    "plus a ~6 TWh/yr flat CHP host-accounting wedge and the chronic 930 identity gap: "
    "+10.4/+11.6/+18.5 TWh/yr (2023/24/25) that the transmission-level grid fleet the "
    "model represents did not serve. The replacement series demand(t) = 930 NetGen(t) - "
    "NG_cell(t) + CEMS bench-gas grid(t) + cogen grid flat + geo/biomass fold-in flat - "
    "TI(t) (207.40/212.19/205.59 TWh) is a derived measured artifact "
    "(scripts/derive_caiso_supply_consistent_demand.py, guard-railed to the committed "
    "CEMS anchors and the FINDING S6 pre-registered windows) — every term measured, "
    "regenerates per year from source data, re-derives only on source updates (rule 23), "
    "never an output pinned back (rule 14). It makes the model's demand basis identical "
    "to the honest CEMS-anchored basis the run is scored against (the demand-side "
    "completion of the owner-signed bench rework). Zero new free parameters, zero fitted "
    "values; supersedes caiso_demand_clock_realign by construction (the series rides the "
    "generation frame's clock). Pre-registered directions and the disclosed 2023 "
    "soft-month risk are in the FINDING S6; LOYO is scored (the construction is "
    "year-specific measured data, so the caiso-78 code-fix LOYO exemption does NOT "
    "apply). No residual-tuned adder is armed in this run."
)

TARGETS = [
    (
        "caiso80_supply_consistent_demand",
        "caiso-80 supply-consistent demand probe session 2026-07-13",
        DELTA80,
    ),
    (
        "caiso80_supply_consistent_demand-ablation",
        "caiso-80 zero-forcing ablation twin session 2026-07-13",
        DELTA80,
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
