#!/usr/bin/env python3
"""Apply the 2026-07-10 PJM keeper-demotion registry/attestation edits.

The apply-miso-1347-edits precedent: these four files carry multi-kilobyte
single-line JSON values that a hand-transcribed full-file push could silently
corrupt, so the edits travel as anchored splices and run server-side (the
apply-pjm-seam-ladder workflow). Idempotent: every edit checks its own
already-applied marker and no-ops. The companion plain-text code patch
(2026_07_10_pjm96_code.patch) carries every normal-width file of the session;
this script carries only the long-line JSON edits.

Edits (the 2026-07-10 pjm-95 -> pjm-94 demotion, CLAUDE.md rule 24):
1. pjm-95 registry sidecar — append the demotion note to `definition`.
2. pjm-94 registry sidecar — append the re-promotion note to `definition`.
3. keepers.json — PJM -> 2026-07-09-pjm-94-stgas-netload in BOTH the per-ISO
   map and the `keepers` list.
4. pjm-95 attestation — resolve the temp_dependent_derate ledger entry's
   `open_validation` with the probe verdict.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

P95_SIDECAR = (
    REPO / "frontend/data/backcast/registry/2026-07-09-pjm-95-temp-derate.json"
)
P94_SIDECAR = (
    REPO / "frontend/data/backcast/registry/2026-07-09-pjm-94-stgas-netload.json"
)
KEEPERS = REPO / "frontend/data/backcast/keepers.json"
ATTESTATION = (
    REPO
    / "results/calibration/pjm95_stgas_drag_tempderate/calibration_attestation.json"
)

P95_NOTE = (
    " [2026-07-10 DEMOTED pjm-95 -> pjm-94 (rule 24 own-fleet validation, the pre-agreed exit in "
    "the attestation's open_validation): scripts/probes/_pjm_temp_capability_envelope.py — the "
    "ERCOT closure test on PJM CAMPD + zone TMAX — REFUTES the literature slopes on PJM's own "
    "fleet: capability envelope flat (p98 0.98-1.11x reference across all hot bins, all classes, "
    "all years, vs model 0.84-0.95), CC_REGULAR proves >=1.00x net-summer at TMAX>=34C (median "
    "1.00, 78-89% of capacity >=0.95x), scarcity-hour slopes ~0/positive (CC -0.10, CT +0.16, "
    "CC_CHP +0.58 %/degC vs model -0.76/-1.26). The C3b/C3c gains came from deleting capability "
    "the fleet measurably has; the 2025 tail re-opens as the G-20 scarcity-structure gap.]"
)

P94_NOTE = (
    " [2026-07-10 RE-PROMOTED to PJM keeper: pjm-95 (this recipe + temp_dependent_derate) demoted "
    "back here after the rule-24 PJM-fleet validation refuted the temp-derate slopes "
    "(scripts/probes/_pjm_temp_capability_envelope.py; see the pjm-95 entry for the findings). "
    "Honest state: C3b 2025 duration NRMSE 0.217 FAIL and C3c 2025 DA tail 0h/51h re-open — the "
    "structural scarcity-pricing gap (G-20 Phase 2), not a derate.]"
)

VERDICT = (
    "RESOLVED 2026-07-10 — REFUTED, mechanism exits the keeper (demotion pjm-95 -> pjm-94): "
    "scripts/probes/_pjm_temp_capability_envelope.py (the ERCOT closure test ported to PJM CAMPD "
    "+ zone TMAX, class/zone map from the model's own fleet build, 2023-2025). Findings mirror "
    "ERCOT's: (a) capability envelope FLAT — p98 output/reference 0.98-1.11x in EVERY hot bin up "
    "to 36-40C for CC/CT/ST_GAS/CC_CHP in all three years, where the raw curves predict "
    "0.84-0.95; (b) lower-bound test — CC_REGULAR median max-output/net-summer 1.00 at TMAX>=34C "
    "with 78-89% of capacity proven >=0.95x (production cannot exceed capability, so the fleet "
    "demonstrates its rating on the exact hours the derate cuts it); (c) max-incentive "
    "scarcity-hour slopes (RT>$200, 5,147 plant-hours; RT>$100, 25,093 companion) CC_REGULAR "
    "-0.10/-0.15 %/degC vs model -0.76, CT_PEAKER +0.16/+0.27 vs -1.26, CC_CHP +0.58 vs -0.76 — "
    "no admissible signature (ST_GAS -0.67 vs -0.54 at the $100 threshold is the one near-model "
    "reading, on a <2%-of-load class whose envelope is nonetheless flat). The pjm-95 C3b/C3c "
    "gains were therefore obtained by deleting capability the fleet measurably has (rule 1: "
    "right number, unreal mechanism), and the 2025 price residual re-opens as an honest scarcity-"
    "structure gap (G-20 Phase 2)."
)

OLD_KEEPER = "2026-07-09-pjm-95-temp-derate"
NEW_KEEPER = "2026-07-09-pjm-94-stgas-netload"


def _splice_definition(path: Path, note: str) -> bool:
    d = json.loads(path.read_text())
    if note.strip() in d["definition"]:
        return False
    d["definition"] += note
    path.write_text(
        json.dumps(d, indent=1) + "\n"
        if path.read_text().endswith("\n")
        else json.dumps(d, indent=1)
    )
    return True


def main() -> None:
    changed = []
    if _splice_definition(P95_SIDECAR, P95_NOTE):
        changed.append(P95_SIDECAR.name)
    if _splice_definition(P94_SIDECAR, P94_NOTE):
        changed.append(P94_SIDECAR.name)

    k = json.loads(KEEPERS.read_text())
    if k.get("PJM") != NEW_KEEPER:
        assert k.get("PJM") == OLD_KEEPER, f"unexpected PJM keeper {k.get('PJM')}"
        k["PJM"] = NEW_KEEPER
        k["keepers"] = [NEW_KEEPER if x == OLD_KEEPER else x for x in k["keepers"]]
        assert NEW_KEEPER in k["keepers"] and OLD_KEEPER not in k["keepers"]
        KEEPERS.write_text(json.dumps(k, indent=1))
        changed.append(KEEPERS.name)

    a = json.loads(ATTESTATION.read_text())
    for e in a["free_parameters"]["entries"]:
        if e.get("name", "").startswith("temp_dependent_derate"):
            if not e["value"]["open_validation"].startswith("RESOLVED"):
                e["value"]["open_validation"] = VERDICT
                ATTESTATION.write_text(json.dumps(a, indent=1))
                changed.append(ATTESTATION.name)

    print("changed:", changed or "nothing (already applied)")


if __name__ == "__main__":
    main()
