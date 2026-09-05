"""Write the ercot-221 adaptive-expectation A/B pair's governance attestations.

The ercot-221 build (`docs/PRECOMMIT-ercot221-adaptive-expectation-2026-08-18.md`
incl. Amendments 1-4) arms ONE boolean on the ercot-215 keeper recipe with TWO
rule-23 frozen constants:

* ``ercot_storage_adaptive_expectation`` — the P1-only two-pass adaptive
  expectation offer: pass-1 solves on the keeper's own offers; the model's OWN
  daily settled-price analogue (demand-weighted P1 lambda + its own
  decontaminated anchored scarcity-adder mirror — Amendment 4; zero measured
  content, rule 13) yields daily deep-scarcity events (>= $1,000); their
  trailing EWMA frequency (half-life 30 d over a 120-d window, per-solve-year
  reset) x beta 3.0077, clipped to [0, 1], floors ERCOT storage discharge at
  max(vom, P_hat x ordc_voll) in hours h17-20 CST only, through the existing
  ``p1_storage_discharge_cost`` seam; pass 2 is THE scored pass.

Phase-0 (v1 and v2) FAILED as pre-registered and stands recorded unrewritten
(``results/calibration/ercot221_adaptive_phase0.json``); Phase-1 was ENTERED ON
OWNER INSTRUCTION over the recorded screen-fail (the ercot-188/213/215
pattern). The C6 attestation NAMES that instruction, per the precommit.

``free_parameters`` is not edited here — it is rebuilt by
``scripts/build_dof_ledger.py`` afterwards (G-DOF reads that).

Usage::

    PYTHONPATH=.:src python scripts/gen_ercot221_attestation.py \
        --arm results/calibration/ercot221_adaptive_B \
        --control results/calibration/ercot221_control_A \
        --still-failing 2023 2024 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}
KEEPER = REPO / "results/calibration/ercot215_decontam_B"

_OWNER_INSTRUCTION = (
    'owner instruction, verbatim, 2026-08-18: "I want you to do the adaptive '
    'battery fix for sure"'
)

_ATTEST_ARM = (
    "ercot-221 session (2026-08-19): the adaptive-expectation storage offer "
    "(PRECOMMIT-ercot221-adaptive-expectation-2026-08-18.md incl. Amendments "
    "1-4), ONE boolean on the ercot-215 keeper recipe "
    "(ercot_storage_adaptive_expectation) with TWO rule-23 frozen constants "
    "(ercot_adaptive_half_life_days = 30.0, ercot_adaptive_beta = 3.0077) "
    "identified in the pre-registered Phase-0 v2 instrument on the MEASURED "
    "2023 daily evening storage offer surface (delivery-2023 60-Day SCED "
    "corpus, ERCOT-154/161 population discipline; identification evidence is "
    "measured CONDUCT, never a price residual, the ercot-210/211/218 "
    "instrument class). PHASE-0 v1 AND v2 BOTH FAILED THEIR PRE-REGISTERED "
    "GATES and stand recorded unrewritten "
    "(results/calibration/ercot221_adaptive_phase0.json: v2 fails the G-ID "
    "daily-correlation leg 0.447 vs 0.6, G-DECAY on the Oct->Nov cliff, and "
    "G-SAFE-2024 by 0.0011); Phase-1 was ENTERED ON OWNER INSTRUCTION over "
    "that recorded screen-fail (" + _OWNER_INSTRUCTION + ") under the "
    "ercot-188/213/215 pattern — an explicit owner act over a recorded "
    "mechanical kill, both records standing. Mechanism, armed path: two-pass "
    "P1 — pass 1 solves on the keeper's own offers; the model's OWN daily "
    "settled-price analogue (demand-weighted P1 energy dual PLUS its own "
    "decontaminated anchored scarcity-adder mirror, Amendment 4 — both duals "
    "of the model's own pass-1 LP, ZERO measured content, rule 13; the "
    "measured RTORDPA overlay is EXCLUDED) yields daily events "
    "(day-max >= $1,000); their trailing EWMA frequency (half-life 30 d, "
    "120-d window, per-solve-year reset) x beta, clipped to [0, 1], is "
    "P_hat(d); storage discharge is floored at max(vom, P_hat x ordc_voll) "
    "in hours h17-20 CST ONLY through the existing ercot-219 stage-3 "
    "p1_storage_discharge_cost seam; pass 2 is THE scored pass; P0 untouched; "
    "exactly one adaptation pass. Self-extinguishing where the model's own "
    "path is spike-free. Judged ONLY by the PRECOMMIT-ercot221 §4 "
    "direction-blind kill-gate table (ercot221_gates.json); the mechanical "
    "verdict is recorded unrewritten and promotion is a separate owner "
    "decision."
)

_ATTEST_CTL = (
    "ercot-221 session (2026-08-19): CONTROL member of the "
    "adaptive-expectation A/B — the ercot-215 keeper recipe replayed "
    "byte-faithfully at HEAD (replay_keeper from the keeper bundle's "
    "meta.json, no --set), the G-REPRO base: 12/12 hourly sidecars "
    "sha256-identical to the keeper. The recipe, mechanisms and "
    "identification are the keeper's own; the attestation below is the "
    "keeper's, carried with magnitudes re-measured on this replay. "
    "ercot_storage_adaptive_expectation is at its default (off)."
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
) -> None:
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = attested_by
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
        "the ercot-221 control replay",
    )
    _write(
        args.arm,
        _ATTEST_ARM,
        args.still_failing,
        "the ercot-221 adaptive-expectation arm",
    )


if __name__ == "__main__":
    main()
