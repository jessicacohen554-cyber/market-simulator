"""Write the ercot-219 Option-B A/B pair's governance attestations.

The ercot-219 build (`docs/PRECOMMIT-ercot219-option-b-phase1-2026-08-18.md`,
`docs/DECISION-CARD-ercot218b-artificial-shortage-structural-2026-08-18.md`)
arms THREE booleans on the ercot-215 keeper recipe with **zero fitted
scalars** — the Option-B structural artificial-shortage mechanism:

* ``ercot_capability_reconciliation`` — the B-1 measured aggregate-capability
  reconciliation (NP6-905 quantity columns only);
* ``ercot_exhaustion_expectation`` — the within-day exhaustion expectation
  from the model's own post-reconciliation state through the registered
  LOLP machinery;
* ``ercot_storage_reservation_offer`` — the P1-only storage reservation-price
  offer, max(vom_base, P_exhaust x ordc_voll).

B-1's own condition (card §1): runs carrying the reconciliation are marked
``capability-reconciled`` on their attestation and determination basis, and
the C6 governance attestation must NAME the signature. This generator does
both for the ARM; the CONTROL carries the keeper's attestation forward with a
replay note (its recipe is the keeper's, unchanged).

``free_parameters`` is not edited here — it is rebuilt by
``scripts/build_dof_ledger.py`` afterwards (G-DOF reads that).

Usage::

    PYTHONPATH=.:src python scripts/gen_ercot219_attestation.py \
        --arm results/calibration/ercot219_optionb_B \
        --control results/calibration/ercot219_control_A \
        --still-failing 2023 2024 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}
KEEPER = REPO / "results/calibration/ercot215_decontam_B"

_B1_SIGNATURE = "B-1 SIGNED (owner, by dispatch of ERCOT-219, 2026-08-18)"

_ATTEST_ARM = (
    "ercot-219 session (2026-08-18): the Option-B Phase-1 build of "
    "DECISION-CARD-ercot218b (the structural model of ERCOT-2023's ECRS "
    "artificial-shortage price formation), executed under "
    + _B1_SIGNATURE
    + " — appended verbatim at the card's foot, constituted by the owner's "
    "dispatch per the card's closing clause and the X-1/X-2 precedent. THREE "
    "booleans on the ercot-215 keeper recipe, ZERO fitted scalars, ZERO new "
    "numeric values (PRECOMMIT-ercot219 §1-§2 pin every convention with "
    "citations; the card-§3 DOF table is the identification ledger): "
    "(1) ercot_capability_reconciliation — THIS RUN IS capability-reconciled "
    "PER B-1: merchant-thermal availability carries a single hourly "
    "tighten-only scalar reconciling the model's aggregate online "
    "dispatchable capability to the published NP6-905 rtolhsl aggregate net "
    "of the measured wind/solar HSL + storage-capability series (quantity "
    "columns ONLY — the no-price-input audit is in "
    "results/calibration/ercot219_seamproof.json), CHP boundary excluded "
    "both sides on the measured -4.05 GW cogen/PUN population offset "
    "(ercot219_basis_phase0.json, corr 0.9957), telemetry-artifact hours "
    "inert per precommit Amendment 1; applied consistently across all three "
    "backcast years under rule 14's reconciled-real-data clause as the ONE "
    "scoped B-1 exception to the ERCOT-159/163 aggregate adjudications "
    "(every per-unit and per-price form stays closed; item 11 Q-B FINAL). "
    "(2) ercot_exhaustion_expectation — P_exhaust(t) = max over "
    "[t..end-of-day] of the registered LOLP curve (resolve_lolp_params, "
    "ordc_lolp_mu_mw/sigma/mcl — existing cited constants, entering as an "
    "EXPECTATION input; ercot-206 B0 untouched, no price channel changed) at "
    "H = post-reconciliation capability - load - the armed *_withheld AS "
    "families' LP requirement rows (measured ASPLANNP433, already keeper "
    "inputs). (3) ercot_storage_reservation_offer — P1-only, at the "
    "pipeline.solve P0->P1 seam: storage discharge offered at "
    "max(vom_base, P_exhaust x ordc_voll) — the textbook reservation price "
    "of stored energy, raise-only, self-extinguishing as P_exhaust -> 0 "
    "(post-reform/RTC+B); P0 untouched by construction and by seam proof. "
    "Judged ONLY by the card-§4 direction-blind kill-gate table "
    "(ercot219_gates.json); the mechanical verdict is recorded unrewritten "
    "and promotion is a separate owner decision."
)

_ATTEST_CTL = (
    "ercot-219 session (2026-08-18): CONTROL member of the Option-B A/B — "
    "the ercot-215 keeper recipe replayed byte-faithfully at HEAD "
    "(replay_keeper from the keeper bundle's meta.json, no --set), the "
    "G-REPRO base. The recipe, mechanisms and identification are the "
    "keeper's own; the attestation below is the keeper's, carried with "
    "magnitudes re-measured on this replay. NOT capability-reconciled (the "
    "three ercot-219 fields are at their defaults)."
)


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year on the scorer's max-zonal basis."""
    out: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        out[year] = int((df.groupby("hour")["price"].max() > 200.0).sum())
    return out


def _write(
    bundle: Path,
    attested_by: str,
    still_failing: list[int],
    run_label: str,
    capability_reconciled: bool,
) -> None:
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = attested_by
    att["governance"]["capability_reconciled"] = capability_reconciled
    if capability_reconciled:
        att["governance"]["capability_reconciled_signature"] = _B1_SIGNATURE
    counts = _tail_counts(bundle)
    kept = []
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") != "price_tail":
            kept.append(exc)
            continue
        if year not in still_failing:
            continue  # band met on this bundle — a spent caveat is dropped
        exc["magnitude"] = (
            f"model {counts.get(year, '?')} h vs actual RT "
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on {run_label})"
        )
        kept.append(exc)
    att["exceptions"] = kept
    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; ledger years "
        f"{[e['year'] for e in kept if e.get('criterion') == 'price_tail']}; "
        "free_parameters left to build_dof_ledger.py)"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument(
        "--still-failing",
        type=int,
        nargs="*",
        default=list(YEARS),
        help="years whose C3c still FAILS on the ARM's own scorecard "
        "(default: all three — the keeper's own ledger state)",
    )
    ap.add_argument(
        "--control-still-failing",
        type=int,
        nargs="*",
        default=list(YEARS),
        help="years whose C3c still FAILS on the CONTROL's scorecard",
    )
    args = ap.parse_args()
    _write(
        args.control,
        _ATTEST_CTL,
        args.control_still_failing,
        "the ercot-219 control replay",
        capability_reconciled=False,
    )
    _write(
        args.arm,
        _ATTEST_ARM,
        args.still_failing,
        "the ercot-219 Option-B arm",
        capability_reconciled=True,
    )


if __name__ == "__main__":
    main()
