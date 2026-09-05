"""Emit the nyiso-155 A/B arms' ``calibration_attestation.json`` (C6 governance gate).

nyiso-155 is the chartered hydro truncation repair RE-ARM
(``results/calibration/PREREG-nyiso155-hydro-truncation-repair-2026-08-25.md``,
pushed and blob-verified BEFORE any measurement). Two bundles:

* **Control** (``nyiso155_hydro_control``) — the committed keeper
  ``2026-08-22-nyiso-152-duty-complete`` recipe replayed ZERO-DELTA at HEAD.
  Its attestation is the keeper's own, ledger carried VERBATIM (no lever, no
  parameter, no mechanism change), with ``attested_by`` re-stamped to say what
  this bundle is.
* **Arm** (``nyiso155_hydro_repair``) — the identical recipe plus exactly the
  pair ``hydro_backfill_year=2024`` + ``hydro_eia930_monthly=True``: a rule 14
  ``[R-ACCURATE]`` measured-input correction with **zero free parameters**.
  One DOF-ledger ENTRY is appended for the input artifact (the nyiso-108
  pattern: +1 entry, +0 residual — the entry introduces no scalar; the 2024
  backfill census and the EIA-930 ``NG: WAT`` monthly level are measured
  series, derived blind to any residual). ``n_residual`` UNCHANGED.

THE GENERATOR IS THE SOURCE OF TRUTH: editing the emitted JSON by hand is
reverted by the next run of this script.

Usage:
    python scripts/gen_nyiso155_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results" / "calibration" / "nyiso152_armSE"
CONTROL = REPO / "results" / "calibration" / "nyiso155_hydro_control"
ARM = REPO / "results" / "calibration" / "nyiso155_hydro_repair"

PREREG = "results/calibration/PREREG-nyiso155-hydro-truncation-repair-2026-08-25.md"

CONTROL_ATTESTED_BY = (
    "session nyiso-155 (2026-08-25). ZERO-DELTA CONTROL of the pre-registered "
    f"hydro truncation repair A/B ({PREREG}, pushed and blob-verified BEFORE "
    "any measurement): the committed keeper 2026-08-22-nyiso-152-duty-complete "
    "recipe replayed unchanged at HEAD ac194ba via scripts/replay_keeper.py. "
    "No lever, no parameter, no mechanism change — the ledger is the keeper's "
    "own, carried verbatim. G1 IDENT is REPORTED AGAINST THIS BUNDLE: the "
    "control is NOT bit-identical to the committed keeper in 2023/2024 "
    "(max |ddispatch| 658.4/457.9 MW, max hourly |dlambda| 2.18/2.61 $/MWh, "
    "annual mean lambda +0.016/+0.018 $/MWh; 2025 EXACTLY identical), with "
    "every pinned input extract content-identical, demand and reserve "
    "requirements bit-identical, and an identical package environment — the "
    "same-objective alternative-optima reshuffle signature, reported per the "
    "prereg G1 failure branch, never adjudicated in-session."
)

ARM_ATTESTED_BY = (
    "session nyiso-155 (2026-08-25). ARM of the pre-registered hydro "
    f"truncation repair A/B ({PREREG}, pushed and blob-verified BEFORE any "
    "measurement), against same-HEAD control 2026-08-25-nyiso-155-hydro-"
    "control. The pair --set hydro_backfill_year=2024 --set "
    "hydro_eia930_monthly=true re-arms the rule 14 [R-ACCURATE] truncated-"
    "vintage input repair that nyiso-108 armed and promoted on 2026-07-31 and "
    "that subsequently fell out of the keeper lineage SILENTLY (no de-arm "
    "decision anywhere in the record; the two flags are solve_and_persist "
    "kwargs, invisible to ScenarioConfig-field lineage-fidelity checks). "
    "Zero fitted scalars; no new ScenarioConfig field; no derive script "
    "touched. THE HONESTY CONSTRAINT IS PART OF THIS ATTESTATION: under the "
    "EIA-930 monthly level pin the hydro VOLUME statistic is NEAR-TAUTOLOGICAL "
    "BY CONSTRUCTION (budget and benchmark become the same series; the arm "
    "reads -4.28/-2.64/-0.19 % by construction) — declared, never banked as "
    "an improvement; dispatch SHAPE is the only load-bearing hydro evidence."
)

DOF_ENTRY = {
    "name": "hydro_vintage_input_repair",
    "where": (
        "meta.hydro_backfill_year=2024 + meta.hydro_eia930_monthly=true "
        "(solve_and_persist kwargs -> data.hydro.build_hydro_fleet / "
        "load_hydro_budget)"
    ),
    "identification": "measured",
    "lineage_solves": (
        "nyiso-108 A/B (2026-07-31, armed+promoted, owner override); "
        "nyiso-155 re-arm A/B (2026-08-25)"
    ),
    "value": {
        "hydro_backfill_year": 2024,
        "hydro_eia930_monthly": True,
        "n_scalars": 0,
        "note": (
            "Plant census backfilled from the complete 2024 EIA-923 vintage "
            "(2025 early release retains 2.0 % of NYIS HY plants); monthly "
            "energy level pinned to EIA-930 NG: WAT, independently validated "
            "by NYISO MIS P-63 Hydro (+1.30/+0.74/+0.60 % agreement). Both "
            "series are measured inputs derived blind to any residual; the "
            "pair regenerates forward via forecast_monthly_hydro (rule 13). "
            "Same-config identification as the CAISO/PJM/MISO/NEISO keepers' "
            "standing arm (PJM/MISO backfill-only, PS fold)."
        ),
    },
}


def main() -> None:
    """Write both bundles' attestations from the keeper's committed one."""
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())

    control = json.loads(json.dumps(base))
    control["governance"]["attested_by"] = CONTROL_ATTESTED_BY
    (CONTROL / "calibration_attestation.json").write_text(
        json.dumps(control, indent=1) + "\n"
    )
    print(f"wrote {CONTROL / 'calibration_attestation.json'}")

    arm = json.loads(json.dumps(base))
    arm["governance"]["attested_by"] = ARM_ATTESTED_BY
    fp = arm["free_parameters"]
    names = [e.get("name") for e in fp["entries"]]
    if DOF_ENTRY["name"] not in names:
        fp["entries"].append(DOF_ENTRY)
    fp["n_entries"] = len(fp["entries"])
    # n_residual UNCHANGED: the appended entry carries zero scalars and a
    # measured identification (rule 21 [R-DOF]).
    (ARM / "calibration_attestation.json").write_text(json.dumps(arm, indent=1) + "\n")
    print(
        f"wrote {ARM / 'calibration_attestation.json'} "
        f"(n_entries {fp['n_entries']}, n_residual {fp['n_residual']})"
    )


if __name__ == "__main__":
    main()
