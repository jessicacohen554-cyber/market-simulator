"""W3a finisher: compose the caiso-65 attestation and promotion edits.

Run in CI by .github/workflows/w3a-finisher.yml against a fresh origin/main
checkout, AFTER dashboard_add_run has registered the ablation twin under its
own id. Performs the pure-file promotion edits (owner decision 2026-07-07):

1. results/calibration/caiso65_seam_envelope_clock/calibration_attestation.json
   — caiso-60's DOF ledger carried forward verbatim, lineage line amended,
   plus the two MEASURED clock-lag constants of the envelope fix (rule 23:
   lag-scan identified, drift-guarded, zero new free parameters).
2. The caiso-65 registry sidecar — definition flipped PROBE→KEEPER with the
   promotion disclosures, ablation_twin linked.
3. frontend/data/backcast/keepers.json — CAISO keeper swapped to caiso-65.

Idempotent: each edit is skipped when already applied.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE_ID = "2026-07-07-caiso65-seam-envelope-clock"
ABL_ID = "2026-07-07-caiso65-seam-envclock-ablation"
OLD_KEEPER = "2026-07-06-caiso-60-p1-native"

ATTEST_SRC = (
    REPO / "results/calibration/caiso60_p1native_ra/calibration_attestation.json"
)
ATTEST_DST = (
    REPO
    / "results/calibration/caiso65_seam_envelope_clock/calibration_attestation.json"
)
SIDECAR = REPO / f"frontend/data/backcast/registry/{BASE_ID}.json"
ABL_SIDECAR = REPO / f"frontend/data/backcast/registry/{ABL_ID}.json"
KEEPERS = REPO / "frontend/data/backcast/keepers.json"

LAG_ENTRIES = [
    {
        "name": "_CAISO_INTERCHANGE_LAG_STD_H",
        "where": "data/eia_loader.py (per-DIBA stamp -> model-clock correction, corridor envelope)",
        "identification": "measured-physical",
        "lineage_solves": "0 (lag-scan identified, never solve-tuned)",
        "value": 1,
        "source": (
            "standard-time lag of the CISO per-DIBA interchange stamps vs the model "
            "hourly frame: best lag -1 h, corr 0.972 vs 0.930 runner-up (2023-2025); "
            "absolute frame anchored by January solar astronomy and the 2024-04-08 "
            "eclipse dip. FINDING-caiso-seam-tz-correction-2026-07-07 §2."
        ),
        "note": (
            "rule-23 frozen: re-derives only from the lag scan in "
            "scripts/validate_caiso_seam_hod_frame.py, which FAILS if the parquet's "
            "stamps change (an honest re-fetch retires this constant, rule 26)."
        ),
    },
    {
        "name": "_CAISO_INTERCHANGE_LAG_DST_H",
        "where": "data/eia_loader.py (per-DIBA stamp -> model-clock correction, corridor envelope)",
        "identification": "measured-physical",
        "lineage_solves": "0 (lag-scan identified, never solve-tuned)",
        "value": 2,
        "source": (
            "daylight-time lag of the CISO per-DIBA interchange stamps vs the model "
            "hourly frame: best lag -2 h, corr 0.961 vs 0.919 runner-up (2023-2025); "
            "same anchors as the standard-time entry."
        ),
        "note": (
            "rule-23 frozen: same guard as _CAISO_INTERCHANGE_LAG_STD_H; the pair is "
            "one measured correction, not two tunables."
        ),
    },
]

LINEAGE_ADDENDUM = (
    " | carried to caiso-65 (W3a envelope-clock fix, promoted 2026-07-07 owner "
    "decision): identical recipe/DOF; adds the two MEASURED clock-lag constants "
    "(entries below) - zero new free parameters (rule 23, drift-guarded)."
)

KEEPER_DEFINITION_PREFIX = (
    "KEEPER (promoted 2026-07-07, owner decision; supersedes caiso-60 - same "
    "recipe, corrected envelope clock). "
)

PROMOTION_DISCLOSURES = (
    " Promotion disclosures: C-gate statuses and grade summary identical to the "
    "caiso-60/61 lineage; C1 free-class 7/8->6/8 - 2023 CC_REGULAR crossed the "
    "band edge (+4.52 TWh) as the corrected envelope trims ~0.3-0.5 GW of "
    "phantom morning imports that backfill mostly with CC (fix-real: CI/local "
    "dispatch byte-identical across highspy 1.15.1/1.14.0, so not solver "
    "drift); C8 CT_PEAKER FAIL inherited from the caiso-58/60 lineage "
    "(owner-held per the G-11 decision); C6 attested via "
    "calibration_attestation.json (caiso-60 DOF ledger + the two measured "
    "clock-lag constants). Ablation twin: " + ABL_ID + "."
)


def compose_attestation() -> None:
    if ATTEST_DST.exists():
        data = json.loads(ATTEST_DST.read_text())
        if any(
            e["name"] == "_CAISO_INTERCHANGE_LAG_STD_H"
            for e in data["free_parameters"]["entries"]
        ):
            print("  skip: attestation already composed")
            return
    data = json.loads(ATTEST_SRC.read_text())
    fp = data["free_parameters"]
    fp["seeded"] = fp["seeded"] + LINEAGE_ADDENDUM
    fp["entries"] = fp["entries"] + LAG_ENTRIES
    fp["n_entries"] = len(fp["entries"])
    ATTEST_DST.write_text(json.dumps(data, indent=1) + "\n")
    print(
        f"  attestation written: {ATTEST_DST.relative_to(REPO)} "
        f"({fp['n_entries']} entries, {fp['n_residual']} residual)"
    )


def promote_sidecar() -> None:
    sc = json.loads(SIDECAR.read_text())
    if sc.get("definition", "").startswith("KEEPER"):
        print("  skip: sidecar already promoted")
        return
    if not ABL_SIDECAR.exists():
        raise SystemExit(
            f"ablation sidecar missing: {ABL_SIDECAR} — run dashboard_add_run first"
        )
    definition = sc["definition"]
    probe_prefix = (
        "PROBE/KEEPER-CANDIDATE (W3a seam-clock fix; keeper decision = owner). "
    )
    if definition.startswith(probe_prefix):
        definition = definition[len(probe_prefix) :]
    sc["definition"] = KEEPER_DEFINITION_PREFIX + definition + PROMOTION_DISCLOSURES
    sc["ablation_twin"] = ABL_ID
    SIDECAR.write_text(json.dumps(sc, indent=2) + "\n")
    print("  sidecar promoted + ablation_twin linked")


def swap_keeper() -> None:
    k = json.loads(KEEPERS.read_text())
    if k.get("CAISO") == BASE_ID:
        print("  skip: keepers.json already swapped")
        return
    if k.get("CAISO") != OLD_KEEPER:
        raise SystemExit(
            f"keepers.json CAISO is {k.get('CAISO')!r}, expected {OLD_KEEPER!r} — aborting"
        )
    k["CAISO"] = BASE_ID
    k["keepers"] = [BASE_ID if x == OLD_KEEPER else x for x in k["keepers"]]
    KEEPERS.write_text(json.dumps(k, indent=4) + "\n")
    print("  keepers.json: CAISO ->", BASE_ID)


def main() -> None:
    print("w3a finisher edits:")
    compose_attestation()
    promote_sidecar()
    swap_keeper()


if __name__ == "__main__":
    main()
