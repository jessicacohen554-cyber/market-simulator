"""Generate the miso-213 ARM leg's calibration attestation from the keeper's.

The gen_miso186/.../210 pattern. The arm is the miso-210 keeper recipe
re-solved via ``scripts/replay_keeper.py --set
miso_zonal_gas_basis_skip_923_priced=true`` (single delta). The CONTROL is the
keeper bundle itself (``miso210_clock_B``, already attested, never re-solved),
so only the arm's attestation is written: the keeper's with a rewritten
``governance.attested_by`` and this session's disclosures appended AT FULL
MAGNITUDE.

**No new ledger entry.** The arm introduces no parameter: a boolean SCOPE on an
existing measured input (rule 19 [R-ONE-MECH] — the EIA-923 print already
embeds the regional delivered premium the zonal basis adds). ``n_entries``
stays 41 and ``n_residual`` 2.

Run this INSTEAD of ``scripts/build_dof_ledger.py`` (which would drop the
documented entries), and because a replay solve writes NO attestation at all
(the miso-200 vacuous-pass trap).

Usage:
    python3 scripts/gen_miso213_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/miso210_clock_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso213_layering_B"
GATES = REPO / "results/calibration/_miso213_ab_gates.json"


def build(dst: Path, gates: dict) -> None:
    d = json.loads(SRC.read_text())
    d["governance"]["attested_by"] = (
        "miso-213 A/B (2026-09-05), ARM leg B (miso_zonal_gas_basis_skip_923_priced "
        "False -> True): control = the miso-210 keeper bundle miso210_clock_B itself "
        "(bit-identity of the replay channel established at miso-210 S-0, not "
        "re-solved) vs arm miso213_layering_B, MISO 2023+2024+2025 in one "
        "invocation, years sequential, solved in-session and never on CI (rule "
        "12/16), from the SAME committed keeper recipe via replay_keeper --set. "
        "The delta is ONE ScenarioConfig field (rule 24 registry): the MISO zonal "
        "basis skips the cells the EIA-923 print path priced. Scored by "
        "scripts/probes/_miso213_ab_gates.py, COMMITTED BLIND with the arm code "
        "before the solve; S-1 single delta, S-2 fuel-price liveness on the keeper "
        "chain, K-1..K-6, six pre-registered object gates. "
        + str(gates.get("verdict", "verdict pending"))
    )
    d.setdefault("disclosures", {})["miso213_ab"] = DISCLOSURE
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


# Rewritten by the session once the arm is scored, so the disclosure quotes
# MEASURED numbers rather than restating the PREREG's expectations. The guard in
# __main__ refuses to write while this is still the placeholder.
_PLACEHOLDER = "PLACEHOLDER"
DISCLOSURE = "PLACEHOLDER — replaced with the measured disclosure after scoring."


if __name__ == "__main__":
    if DISCLOSURE.startswith(_PLACEHOLDER):
        raise SystemExit(
            "refusing to write: DISCLOSURE is still the placeholder. Score the "
            "arm first, then replace it with the measured disclosure."
        )
    if not GATES.exists():
        raise SystemExit(f"refusing to write: {GATES} does not exist — score first.")
    build(ARM / "calibration_attestation.json", json.loads(GATES.read_text()))
