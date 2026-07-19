"""Write the caiso-102 bundle attestation (the +1h frame-defect fix leg).

Derives ``caiso102_hourfix_B/calibration_attestation.json`` from the caiso-101
KEEPER attestation already committed in the repo (identical lever set — the
leg carries NO flag delta and NO new mechanism), swapping the ``attested_by``
line and appending the single-delta note. The delta is a rule-14
measured-input integrity correction (the `_eia_hourly_frame_filled`
hour-ending anchor defect, FINDING-caiso102 §5), so the DOF ledger is
UNCHANGED — zero new parameters, ``n_entries``/``n_residual`` untouched
(the _caiso99_attestation.py pattern, minus the ledger append).

Usage: python scripts/probes/_caiso102_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso101_wp3_B" / "calibration_attestation.json"
OUT = ROOT / "caiso102_hourfix_B" / "calibration_attestation.json"

DELTA102 = (
    " PLUS the single caiso-102 delta — NOT a lever: the +1h frame-defect "
    "fix (FINDING-caiso102 §5, issue #2562). "
    "`eia_loader._eia_hourly_frame_filled` anchored its reconstructed year "
    "on the EIA-930 `Local time` stamp as if interval-beginning; the stamps "
    "are hour-ending, so every gap-bridged BA-year (CISO-2025 8751 rows, "
    "PJM-2023, MISO-2025) solved one hour LATE — the caiso-101 keeper's "
    "entire exogenous 2025 hourly world (HSL solar/wind profiles, the "
    "caiso-80 supply-consistent demand, runtime interchange fallbacks) was "
    "rotated +1h against the unrotated LMP actuals it is scored on (model "
    "2025 solar hod profile lag −1 r=0.9997 vs lag 0 r=0.9525; evening "
    "solar 8.41 vs measured 4.20 TWh). Fixed at the loader root "
    "(interval-beginning anchor) and re-derived through the fixed loader "
    "(rule 23, citing the defect, never a residual): "
    "caiso_2025_hsl_hourly.parquet + caiso_supply_consistent_demand_2025.csv "
    "(2023/2024 artifacts byte-identical after rebuild, md5-checked). "
    "Pre-registered hard gates (FINDING-caiso102 §6, committed before "
    "adjudication): 2023/2024 solve outputs byte-identical to the "
    "same-machine caiso102_repro_A; 2025 solar aligns at lag 0; C1 12/12; "
    "C7/C8 PASS. Zero parameters moved — the DOF ledger is identical to "
    "caiso-101."
)


def main() -> None:
    att = json.loads(BASE.read_text())
    att["governance"]["attested_by"] = (
        "caiso-102 inelastic-charge/evening-merit session 2026-07-19 (the "
        "+1h frame-defect fix, single-delta A/B vs same-machine "
        "caiso102_repro_A; carries the caiso-101 keeper attestation + lever "
        "set verbatim — no flag delta, no new mechanism, zero DOF delta)"
    )
    att["governance"]["note"] = att["governance"]["note"] + DELTA102
    OUT.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
