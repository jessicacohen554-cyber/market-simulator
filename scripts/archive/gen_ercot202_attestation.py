"""Write the ercot-202 A/B bundles' governance attestations from the keeper's.

The ercot-202 rule-18 grain-repair pair
(``docs/PRECOMMIT-ercot202-rule18-grain-successor-2026-08-14.md``) adds ZERO
parameters: the control is the run192 keeper recipe replayed byte-faithfully at
HEAD, and the arm is the same recipe plus the single boolean
``ercot_faststart_pool_plant_physics=true`` — a LICENSING-GATE grain correction
whose bound (``constants.FASTSTART_POOL_MIN_DOWN_HOURS = 2.0``) is the existing
constant and whose stamped values are fleet assembly's own. There is no scalar
to add to the ledger and none to remove.

Both attestations are therefore the keeper's, deep-copied with:

* ``governance.attested_by`` set to this session's statement;
* the C3c exceptions-ledger magnitudes re-measured on each bundle's own hourly
  sidecars, on the SCORER'S max-zonal basis (the ``gen_ercot192_attestation.py``
  pattern — the demand-weighted basis was the ercot-192-filed defect);
* one carry sentence appended to each C3c entry's reason.

``free_parameters`` is untouched by construction — n_entries and n_residual are
asserted equal to the keeper's, not edited.

Usage::

    PYTHONPATH=.:src python3 scripts/gen_ercot202_attestation.py \
        --base results/calibration/ercot202_graincontrol_A \
        --arm  results/calibration/ercot202_plantphysics_B
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}

_CONTROL_ATTEST = (
    "ercot-202 session (2026-08-14): CONTROL of the rule-18 [R-PHYSICS] "
    "grain-repair A/B — the run192 keeper recipe replayed at HEAD with ZERO "
    "deltas, the same-HEAD reproduction that separates HEAD drift from the "
    "mechanism, per docs/PRECOMMIT-ercot202-rule18-grain-successor-2026-08-14.md "
    "§7. Zero parameters added or changed; the free-parameter ledger is the "
    "keeper's unchanged."
)
_ARM_ATTEST = (
    "ercot-202 session (2026-08-14): ARM of the rule-18 [R-PHYSICS] grain "
    "repair — the run192 keeper recipe plus ONE boolean, "
    "ercot_faststart_pool_plant_physics=true, which moves "
    "ercot_faststart_pool_offer's licensing gate from the (vacuous) bid-row "
    "grain to PLANT grain, per "
    "docs/PRECOMMIT-ercot202-rule18-grain-successor-2026-08-14.md §2/§7. ZERO "
    "fitted scalars: the flag is a boolean, the bound is the existing constant "
    "FASTSTART_POOL_MIN_DOWN_HOURS = 2.0 (not moved), and the stamped values "
    "are fleet assembly's own bin_min_run / bin_min_down. The free-parameter "
    "ledger is the keeper's unchanged."
)
_CARRY = (
    " CARRIED ONTO THE ercot-202 {TAG}: the A/B toggles only WHICH ROWS ARE "
    "LICENSED to read a frozen offer artifact (a rule-18 physics-grain "
    "correction to an eligibility test, not a scarcity-formation mechanism) — "
    "the accepted model-class limitation is that an LP on competitive/measured "
    "offers cannot form ERCOT's realized RT tail equilibrium, and nothing in a "
    "licensing gate changes that. The counts are re-measured on this run and "
    "reported at full magnitude."
)


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year, on the SCORER'S OWN max-zonal basis
    (reproduces ``ordc.hoursGt200.model`` — see gen_ercot192_attestation)."""
    out: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        out[year] = int((df.groupby("hour")["price"].max() > 200.0).sum())
    return out


def _write(bundle: Path, keeper_attest: dict, attested_by: str, tag: str) -> None:
    """Write one bundle's attestation, re-measuring its own C3c magnitudes."""
    att = json.loads(json.dumps(keeper_attest))  # deep copy
    att["governance"]["attested_by"] = attested_by

    fp = att["free_parameters"]
    assert fp["n_entries"] == keeper_attest["free_parameters"]["n_entries"]
    assert fp["n_residual"] == keeper_attest["free_parameters"]["n_residual"]

    counts = _tail_counts(bundle)
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") == "price_tail" and year in counts:
            exc["magnitude"] = (
                f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
                f"> $200/MWh (re-measured on the ercot-202 {tag})"
            )
            exc["reason"] = re.sub(
                r"\s*CARRIED ONTO THE ercot-202.*$", "", exc.get("reason", "")
            ) + _CARRY.replace("{TAG}", tag.upper())

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; ledger unchanged: "
        f"n_entries {fp['n_entries']}, n_residual {fp['n_residual']})"
    )


def main() -> None:
    """Write both bundles' attestations from the run192 keeper's."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument(
        "--keeper", type=Path, default=REPO / "results/calibration/ercot192_arm_B"
    )
    args = ap.parse_args()
    keeper_attest = json.loads(
        (args.keeper / "calibration_attestation.json").read_text()
    )
    if args.base.exists():
        _write(args.base, keeper_attest, _CONTROL_ATTEST, "control")
    else:
        print(f"skip control: {args.base} not solved yet")
    if args.arm.exists():
        _write(args.arm, keeper_attest, _ARM_ATTEST, "arm")
    else:
        print(f"skip arm: {args.arm} not solved yet")


if __name__ == "__main__":
    main()
