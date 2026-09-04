"""Generate the miso-210 A/B legs' calibration attestations from the keeper's.

The gen_miso186/.../202 pattern. Both legs are the miso-202 keeper recipe
re-solved via ``--replay-bundle``; the arm carries the max-gen CLOCK repair —
``maxgen_events.MODEL_TZ_BY_ISO['MISO']`` (and the M-2 deriver's twin constant)
moved from EST to the measured CST model clock, plus the re-derived M-2
extract. Each leg's attestation is the keeper's with a rewritten
``governance.attested_by`` and this session's disclosures appended AT FULL
MAGNITUDE.

**No new ledger entry.** The arm introduces no parameter: it corrects a
constant to a measured property of the model's own hour index (two r = 1.000
witnesses, miso-208 §0 item 2). ``n_entries`` stays 41 and ``n_residual`` 2.
The clock is recorded as a DISCLOSURE, not a free parameter — there is nothing
that could have been chosen differently once the model clock was measured.

Run this INSTEAD of ``scripts/build_dof_ledger.py`` (which would drop the
documented entries), and because a ``--replay-bundle`` solve writes NO
attestation at all (the miso-200 vacuous-pass trap).

Usage:
    python3 scripts/gen_miso210_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/miso202_unitclip_B/calibration_attestation.json"
CONTROL = REPO / "results/calibration/miso210_control_A"
ARM = REPO / "results/calibration/miso210_clock_B"
GATES = REPO / "results/calibration/_miso210_ab_gates.json"


def build(dst: Path, armed: bool, gates: dict) -> None:
    d = json.loads(SRC.read_text())
    leg = (
        "ARM leg B (MODEL_TZ_BY_ISO['MISO'] Etc/GMT+5 -> Etc/GMT+6 + re-derived M-2 extract)"
        if armed
        else "CONTROL leg A (HEAD 8f5cb32c: EST placement, committed extract)"
    )
    d["governance"]["attested_by"] = (
        f"miso-210 A/B (2026-09-04), {leg}: control miso210_control_A vs arm "
        "miso210_clock_B, both MISO 2023+2024+2025 in one invocation, years "
        "sequential, solved in-session and never on CI (rule 12/16), both from "
        "the SAME committed keeper recipe (2026-09-03-miso-202-unitclip) via "
        "--replay-bundle. The delta is NOT a ScenarioConfig field: it is one "
        "clock constant (mirrored in the M-2 deriver, with the deriver's DA-hub "
        "certificate record shifted by the same hour) and the extract that "
        "constant regenerates. Scored by scripts/probes/_miso210_ab_gates.py, "
        "COMMITTED BLIND with the PREREG (83e73bf8) before any window was "
        "re-placed and before either leg's numbers; S-1/S-2/S-3 restated for a "
        "code+data delta (zero config diffs + commit/extract identity; exact "
        "one-hour placement shift off the production functions; guard-2 "
        "certificate invariance as a hard void). "
        + str(gates.get("verdict", "verdict pending"))
    )
    d.setdefault("disclosures", {})["miso210_ab"] = DISCLOSURE
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


# Rewritten by the session once the pair is scored, so the disclosure quotes
# MEASURED numbers rather than restating the PREREG's expectations. The guard in
# __main__ refuses to write while this is still the placeholder.
_PLACEHOLDER = "PLACEHOLDER"
DISCLOSURE = "PLACEHOLDER — replaced by the measured disclosure after scoring."


if __name__ == "__main__":
    if DISCLOSURE.startswith(_PLACEHOLDER):
        raise SystemExit(
            "refusing to write: DISCLOSURE is still the placeholder. Score the "
            "pair first, then replace it with the measured disclosure."
        )
    if not GATES.exists():
        raise SystemExit(f"refusing to write: {GATES} does not exist — score first.")
    gates = json.loads(GATES.read_text())
    build(CONTROL / "calibration_attestation.json", False, gates)
    build(ARM / "calibration_attestation.json", True, gates)
