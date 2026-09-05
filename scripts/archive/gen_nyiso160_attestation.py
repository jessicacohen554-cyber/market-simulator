"""Emit the nyiso-160 audit replay's ``calibration_attestation.json`` (C6 governance gate).

nyiso-160 is the touchpoint-prep audit run in place of the stopped Leg 2
(`FINDING-nyiso160-leg2-stop-and-tpaudit-2026-08-30.md`): the designated
keeper ``2026-08-30-nyiso-159-loss-surface`` recipe replayed ZERO-DELTA at
HEAD into ``nyiso160_tpaudit_replay``. The DOF ledger is the keeper's own,
carried VERBATIM — no lever, no parameter, no mechanism change (the audit's
A3 leg verifies exactly that from the recorded surfaces).

THE GENERATOR IS THE SOURCE OF TRUTH: editing the emitted JSON by hand is
reverted by the next run of this script.

Usage:
    python scripts/gen_nyiso160_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results" / "calibration" / "nyiso159_lossarm_B"
REPLAY = REPO / "results" / "calibration" / "nyiso160_tpaudit_replay"

FINDING = "results/calibration/FINDING-nyiso160-leg2-stop-and-tpaudit-2026-08-30.md"
AUDIT = "results/calibration/_nyiso160_tpaudit.json"

REPLAY_ATTESTED_BY = (
    "session nyiso-160 (2026-08-30). TOUCHPOINT-PREP AUDIT REPLAY — the "
    "designated keeper 2026-08-30-nyiso-159-loss-surface recipe replayed "
    "ZERO-DELTA at HEAD via scripts/replay_keeper.py, run in place of the "
    f"stopped Leg-2 AORR intake ({FINDING}: the owner cannot produce the "
    "MyNYISO files; the leg closes with cause at access, the nyiso-97 "
    "stop-if-walled class, and no substitute winter mechanism is invented "
    "per nyiso-158 s1.4 and the nyiso-97 s5 re-open bar). No lever, no "
    "parameter, no mechanism change — the ledger is the keeper's own, "
    f"carried verbatim. AUDIT VERDICT ({AUDIT}): the keeper REPLAYS "
    "IDENTICALLY — A1 max abs divergence 0.0 on every hourly-sidecar value "
    "column in all three years (max zonal |dprice| 0.0 x3); A2 C3a "
    "+2.35/-1.21/-11.48 vs committed +2.35/-1.21/-11.48 (delta 0.00 pp, "
    "lw-lambda identical to 4 dp); A3 zero differing levers (the two "
    "differing keys are post-recording rule-24 schema growth at registered "
    "default False, proven inert by A1). No G1-class drift; the "
    "touchpoint-prep condition is SATISFIED. NEVER a keeper candidate — "
    "the keeper itself, re-established at HEAD."
)


def main() -> None:
    """Write the replay bundle's attestation from the keeper's committed one."""
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    doc = json.loads(json.dumps(base))
    doc["governance"]["attested_by"] = REPLAY_ATTESTED_BY
    doc["governance"]["note"] = (
        "nyiso-160 (2026-08-30): zero-delta HEAD-replay audit of the "
        "nyiso-159 keeper. The mechanism notes and free-parameter ledger "
        "are the keeper's, unchanged; see attested_by for this bundle's "
        "role and the audit evidence."
    )
    (REPLAY / "calibration_attestation.json").write_text(
        json.dumps(doc, indent=1) + "\n"
    )
    print(f"wrote {REPLAY / 'calibration_attestation.json'}")
    print(
        "free_parameters: n_entries="
        f"{doc['free_parameters']['n_entries']} (carried verbatim)"
    )


if __name__ == "__main__":
    main()
