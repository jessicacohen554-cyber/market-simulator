"""Write the ercot-204 rule-26 re-solve bundle's governance attestation.

The ercot-204 Part-B deletion
(``docs/PRECOMMIT-ercot204-rtorpa-gate-and-rule26-successor-2026-08-15.md``)
adds ZERO parameters and REMOVES one field: the transitional boolean
``ercot_faststart_pool_plant_physics`` and the pre-repair row-grain branch it
selected are deleted outright (rule 26 ``[R-DELETE]``), leaving the ercot-186
plant-grain rule-18 physics gate unconditional. The keeper already ran with
that flag armed, so the recipe is unchanged in substance — there is no scalar
to add to the ledger and none to remove.

The attestation is therefore the keeper's, deep-copied with:

* ``governance.attested_by`` set to this session's statement;
* the C3c exceptions-ledger magnitudes re-measured on this bundle's own hourly
  sidecars, on the SCORER'S max-zonal basis (the ``gen_ercot192_attestation.py``
  pattern — the demand-weighted basis was the ercot-192-filed defect);
* one carry sentence appended to each C3c entry's reason.

``free_parameters`` is untouched by construction — n_entries and n_residual are
asserted equal to the keeper's, not edited. A deletion cannot add a degree of
freedom, and this one removes no identified parameter either: the flag carried
zero DOF.

Usage::

    PYTHONPATH=.:src ./.venv/bin/python scripts/gen_ercot204_attestation.py \
        --bundle results/calibration/ercot204_rule26_delete
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

_ATTEST = (
    "ercot-204 session (2026-08-15): the RULE-26 [R-DELETE] SUCCESSOR named by "
    "the ercot-202 keeper — the same keeper recipe re-solved with the "
    "transitional flag ercot_faststart_pool_plant_physics DELETED and the "
    "ercot-186 plant-grain rule-18 [R-PHYSICS] licensing gate made "
    "UNCONDITIONAL, together with the pre-repair row-grain branch it selected. "
    "Deleted rather than defaulted-on: a deprecated parameter that still "
    "parses is a re-armable answer key. The re-solve exists so that no bundle "
    "references the flag — ScenarioConfig.with_overrides raises on an unknown "
    "key, which is precisely why ercot-202 could not discharge the obligation "
    "in place. ZERO fitted scalars, ZERO new fields, one field REMOVED; the "
    "bound FASTSTART_POOL_MIN_DOWN_HOURS = 2.0 is untouched and the "
    "free-parameter ledger is the keeper's unchanged. Per "
    "docs/PRECOMMIT-ercot204-rtorpa-gate-and-rule26-successor-2026-08-15.md "
    "Part B."
)
_CARRY = (
    " CARRIED ONTO THE ercot-204 RULE-26 RE-SOLVE: this run deletes a "
    "transitional flag and a dead code branch, changing WHICH ROWS ARE "
    "LICENSED to read a frozen offer artifact not at all (the keeper already "
    "ran the armed path) — it is a governance deletion, not a scarcity-"
    "formation mechanism. The accepted model-class limitation is that an LP on "
    "competitive/measured offers cannot form ERCOT's realized RT tail "
    "equilibrium, and nothing in a code deletion changes that. The counts are "
    "re-measured on this run and reported at full magnitude."
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


def main() -> None:
    """Write the re-solve bundle's attestation from the ercot-202 keeper's."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument(
        "--keeper",
        type=Path,
        default=REPO / "results/calibration/ercot202_plantphysics_B",
    )
    args = ap.parse_args()

    keeper_attest = json.loads(
        (args.keeper / "calibration_attestation.json").read_text()
    )
    att = json.loads(json.dumps(keeper_attest))  # deep copy
    # audit_keepers E10: the inherited attestations carry no schema tag.
    # Stamp it on regeneration, as that check asks. Nothing reads it for a
    # determination (calibration_verdict never looks), so this is a
    # provenance label, not a behaviour change.
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST

    fp = att["free_parameters"]
    assert fp["n_entries"] == keeper_attest["free_parameters"]["n_entries"]
    assert fp["n_residual"] == keeper_attest["free_parameters"]["n_residual"]

    counts = _tail_counts(args.bundle)
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") == "price_tail" and year in counts:
            exc["magnitude"] = (
                f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
                f"> $200/MWh (re-measured on the ercot-204 rule-26 re-solve)"
            )
            exc["reason"] = (
                re.sub(
                    r"\s*CARRIED ONTO THE ercot-20[0-9].*$", "", exc.get("reason", "")
                )
                + _CARRY
            )

    path = args.bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; ledger unchanged: "
        f"n_entries {fp['n_entries']}, n_residual {fp['n_residual']})"
    )


if __name__ == "__main__":
    main()
