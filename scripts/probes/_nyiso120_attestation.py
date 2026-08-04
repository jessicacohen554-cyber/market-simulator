#!/usr/bin/env python3
"""nyiso-120 — write each arm's calibration attestation.

Both arms are byte-faithful replays of the ``2026-08-03-nyiso-118-seny-span``
keeper recipe with **one committed input file** different, so the attestation is
that keeper's, carried over verbatim except for:

* ``governance.attested_by`` — rewritten per arm.
* a new ``chp_heat_rate_artifact`` block recording which artifact the arm solved
  on (path + sha256 + the East River row), the analogue of the existing
  ``ct_heat_rate_artifact`` block.
* ``_open_items`` — arm B additionally records the measured ``CT_CHP``
  direction.

**The DOF ledger is carried over UNCHANGED — ``n_entries`` 32, ``n_residual``
6.** That is not an oversight: the correction removes a quantity from an
existing measured input using a share measured from CAMPD's own unit-grain
channel at the artifact's own vintage year. There is no number in it to tune,
so it adds no degree of freedom (rule 21 ``[R-DOF]``).

    python scripts/probes/_nyiso120_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/nyiso118_seny_span"
ARM_A = REPO / "results/calibration/nyiso120_control_A"
ARM_B = REPO / "results/calibration/nyiso120_scopegate_B"
ARTIFACT_B = REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_NYISO.csv"
ARTIFACT_A = REPO / "results/calibration/_nyiso120_artifact_A.csv"

_COMMON = (
    "nyiso-120 — the miso-122 hybrid-cogen dark-fuel SCOPE GATE applied to "
    "NYISO's chp_power_only_heat_rates artifact (matrix §5.6/§5.4 handoff; "
    "measured_chp_heat_rates is armed in BOTH arms and NYISO's cell is already "
    "K, so this is a SCOPE refinement inside the K mechanism, not a new lever "
    "and not a new ScenarioConfig field). Pre-registered in "
    "results/calibration/PREREG-nyiso120-eastriver-scope-gate-2026-08-04.md "
    "with KE1-KE9, the A/B design and the decision rule all fixed and PUSHED "
    "BEFORE THE DERIVE WAS RE-RUN AND BEFORE EITHER SOLVE. "
    "THE MEASUREMENT, on NYISO's own data (rule 25 [R-ISO-SCOPE] — miso-122's "
    "verdict filled no NYISO cell): eGRID's CHPCHTI at ORIS 2493 East River is "
    "the SAME OBJECT as the CAMPD dark-boiler fuel (13,629,047 / 13,493,031 = "
    "1.0101, KE1), and CAMPD's power-train fuel over eGRID's own PLNGENAN is "
    "7.3763 against eGRID's credited 7.4205 (ratio 0.9940, KE2) — two "
    "INDEPENDENT meters agreeing to 0.6 % on the power-only rate. So PLHTIAN is "
    "already the power train's fuel, PLHTRT = 7.4205 is already the power-only "
    "rate, and the (PLHTIAN + CHPCHTI) add-back DOUBLE-COUNTS the fuel of two "
    "Dry bottom wall-fired boilers that report EXACTLY ZERO gross load in every "
    "hour of 2023-2025 (KE3: 100.0 % boiler unitType all three years, share "
    "37.51/30.79/30.64 %, max/min 1.22). The applied offer heat rate on 306.0 MW "
    "of NYC CT_CHP therefore falls 11.8032 -> 7.4205 (-37.1 %). "
    "ZERO FREE PARAMETERS and NO NEW NUMBER (rules 5/21/24): the dark share is "
    "CAMPD's own unit-grain heat input over the same plant's total at the "
    "artifact's own eGRID vintage year, there is no threshold, and the derive "
    "logic is miso-122's shipped UNMODIFIED — this session edited no derive "
    "code. Rule 23 [R-FROZEN-DERIVE] citation is a SCOPE-GATE LOGIC CHANGE ON "
    "MEASURED GROUNDS (miso-122), never a residual. "
    "Rule 22: training years 2023-2025 only in one bundle each (rule 16); no "
    "out-of-training year solved, scored or read; the holdout spend freeze is "
    "ACTIVE and untouched."
)

_A = (
    "nyiso-120 CONTROL — the same-HEAD zero-delta baseline, solved on the "
    "PRE-GATE committed artifact. Its existence is mandatory rather than "
    "optional: FINDING-nyiso114 §2 measured that a P0-run-pattern keeper does "
    "not re-solve to byte-identity once main moves, so every A/B delta is "
    "quoted against THIS arm and never against the committed keeper (prereg "
    "KE5). Zero config delta vs the treatment — the two run_config scenario "
    "blocks are identical by construction and only the input file differs. "
) + _COMMON

_B = (
    "nyiso-120 TREATMENT — solved on the HEAD re-derived artifact, in which "
    "East River's flag moves ok -> below_credited and the row leaves the "
    "flag=='ok' applied map, reverting to the incumbent eGRID rate. The "
    "direction is unambiguously DOWNWARD only because NYISO carries no legacy "
    "hand factor (CHP_STEAM_CREDIT_HR_CORRECTION_ISOS = {CAISO, PJM}); in a "
    "hand-factor ISO the identical exclusion would push the rate UP, which is "
    "asserted in the A/B scorer rather than assumed. KE4 no-op fidelity holds "
    "EXACTLY: one applied-rate row changes, zero other flag changes, zero other "
    "applied-rate changes. "
) + _COMMON


def _sha(path: Path) -> str:
    """sha256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_block(path: Path) -> dict:
    """Record which CHP artifact an arm solved on, and East River's row in it."""
    df = pd.read_csv(path)
    row = df[(df["plant_code"] == 2493) & (df["plant_group"] == "CT_CHP")].iloc[0]
    applied = df[df["flag"] == "ok"]
    return {
        "path": str(path.relative_to(REPO)),
        "sha256": _sha(path),
        "rows_applied": int(len(applied)),
        "east_river_2493_CT_CHP": {
            "flag": str(row["flag"]),
            "heat_rate_column": float(row["heat_rate"]),
            "incumbent_model_heat_rate": float(row["model_heat_rate"]),
            "EFFECTIVE_rate_charged": (
                float(row["heat_rate"])
                if str(row["flag"]) == "ok"
                else float(row["model_heat_rate"])
            ),
            "class_capacity_mw": float(row["class_capacity_mw"]),
        },
    }


def main() -> int:
    """Write both arms' attestations from the keeper's."""
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    for bundle, attested, artifact in (
        (ARM_A, _A, ARTIFACT_A),
        (ARM_B, _B, ARTIFACT_B),
    ):
        if not bundle.exists():
            print(f"skip {bundle.name} — not solved yet")
            continue
        att = json.loads(json.dumps(base))  # deep copy
        att["governance"]["attested_by"] = attested
        att["chp_heat_rate_artifact"] = _artifact_block(artifact)
        if bundle is ARM_B:
            att.setdefault("_open_items", []).insert(
                0,
                "CT_CHP was ALREADY the worst-matched CHP class on the incumbent "
                "keeper (its own attestation records the class under-dispatched "
                "-67.9/-67.6/-62.0 %). This correction cuts the class's largest "
                "plant's offer rate by 37.1 %, so it moves CT_CHP TOWARD the "
                "measured level rather than away from it — but it is NOT claimed "
                "to close that gap, and the gap is not the reason the correction "
                "ships. It ships because the input was wrong (rule 14 "
                "[R-ACCURATE]). The named successor for the residual remains "
                "the BTM host-steam holdout (chp_btm_pct / chp_grid_pmin_mw) and "
                "the CT_CHP must-run treatment, unchanged by this session.",
            )
        out = bundle / "calibration_attestation.json"
        out.write_text(json.dumps(att, indent=1) + "\n")
        print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
