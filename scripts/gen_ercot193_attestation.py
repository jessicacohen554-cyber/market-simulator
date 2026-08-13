"""Write the ercot-193 A/B bundles' governance attestations from the keeper's.

The ercot-193 SOC re-gate pair (`docs/PRECOMMIT-ercot193-soc-regate-2026-08-13.md`)
adds ZERO parameters: the arm is the run192 keeper recipe replayed byte-faithfully
at HEAD, the control is the same recipe minus the single armed zero-DOF measured
mechanism `ercot_storage_as_soc_reserve` (its ercot-167 identification: measured
60-Day AS awards × published product durations — no fitted scalar exists to
remove from the ledger with it). Both attestations are therefore the keeper's,
deep-copied with:

* ``governance.attested_by`` set to this session's statement;
* the C3c exceptions-ledger magnitudes re-measured on each bundle's own hourly
  sidecars, on the SCORER'S max-zonal basis (`gen_ercot192_attestation.py`
  pattern — the demand-weighted basis was the ercot-192-filed defect, fixed
  this session in `gen_ercot188_attestation.py` too);
* one carry sentence appended to each C3c entry's reason.

``free_parameters`` is untouched by construction — n_entries and n_residual are
asserted equal to the keeper's, not edited.

Usage::

    PYTHONPATH=.:src python3 scripts/gen_ercot193_attestation.py \
        --base results/calibration/ercot193_ctl_nosoc \
        --arm  results/calibration/ercot193_arm_soc
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
    "ercot-193 session (2026-08-13): CONTROL of the standing ercot-167 SOC-reserve "
    "re-gate — the run192 keeper recipe with ONLY ercot_storage_as_soc_reserve "
    "disarmed (the exact inverse of the ercot-167 single delta), solved at HEAD "
    "per docs/PRECOMMIT-ercot193-soc-regate-2026-08-13.md §3. Zero parameters "
    "added or changed; the free-parameter ledger is the keeper's unchanged."
)
_ARM_ATTEST = (
    "ercot-193 session (2026-08-13): ARM of the standing ercot-167 SOC-reserve "
    "re-gate — the run192 keeper recipe replayed byte-faithfully at HEAD "
    "(doubles as the G-REPRO keeper-reproduction check), per "
    "docs/PRECOMMIT-ercot193-soc-regate-2026-08-13.md §3. Zero parameters added "
    "or changed; the free-parameter ledger is the keeper's unchanged."
)
_CARRY = (
    " CARRIED ONTO THE ercot-193 {TAG}: the re-gate A/B toggles only the "
    "measured zero-DOF AS SOC reservation (protocol SOC backing, a quantity "
    "mechanism, not a scarcity-formation mechanism) — the accepted model-class "
    "limitation is unchanged and the counts are re-measured on this run at full "
    "magnitude."
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
                f"> $200/MWh (re-measured on the ercot-193 {tag})"
            )
            exc["reason"] = re.sub(
                r"\s*CARRIED ONTO THE ercot-193.*$", "", exc.get("reason", "")
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
    _write(args.arm, keeper_attest, _ARM_ATTEST, "arm")


if __name__ == "__main__":
    main()
