"""Write the caiso-205 adaptive-expectation A/B pair's governance attestations.

The caiso-205 build (`results/calibration/PRECOMMIT-caiso205-adaptive-ab-
2026-08-19.md`) arms ONE boolean on the caiso-200 keeper recipe with TWO
rule-23 frozen constants:

* ``caiso_storage_adaptive_expectation`` — the P1-only two-pass adaptive
  expectation offer, CAISO leg of the ercot-221 family: pass-1 solves on the
  keeper's own offers; the model's OWN daily CA demand-weighted P1 energy dual
  (pure lambda — CAISO's scored backcast price IS the energy-only dual,
  caiso-137b; zero measured content, rule 13) yields daily spike events
  (>= $200); their trailing EWMA frequency (half-life 30 d over a 120-d
  window, per-solve-year reset) x beta 0.5945, clipped to [0, 1], floors CAISO
  BATTERY discharge at max(vom, P_hat x $1,000 park cap) in hours h18-21 PT
  only, through the existing ``p1_storage_discharge_cost`` seam; pass 2 is THE
  scored pass.

Phase-0 (caiso-204) FAILED G-BOOT as pre-registered and stands recorded
unrewritten (``results/calibration/caiso204_adaptive_phase0.json``); Phase-1
was ENTERED ON OWNER ORDER over the recorded wall (caiso-205 charter branch 1
— the ercot-188/213/215/221 pattern). The C6 attestation NAMES that order.

``free_parameters`` is not edited here — it is rebuilt by
``scripts/build_dof_ledger.py`` afterwards (G-DOF reads that).

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso205_attestation.py \
        --arm results/calibration/caiso205_adaptive_B \
        --control results/calibration/caiso205_control_A \
        --still-failing 2023 2024 --control-still-failing 2023 2024
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
#: Actual RT hours > $200/MWh (C3c basis; caiso-204 finding §C / keeper ledger).
ACTUAL_TAIL = {2023: 47, 2024: 35, 2025: 8}
KEEPER = REPO / "results/calibration/caiso200_h1_memberpanel"

_OWNER_ORDER = (
    "owner order, caiso-205 charter (2026-08-19): branch 1 — PHASE-1 ENTRY "
    "over the caiso-204 recorded FAIL (the ercot-188/213/215/221 pattern), "
    "selected explicitly by the owner in-session from the charter's three "
    "branches"
)

_ATTEST_ARM = (
    "caiso-205 session (2026-08-19): the adaptive-expectation storage offer, "
    "CAISO leg (PRECOMMIT-caiso205-adaptive-ab-2026-08-19.md), ONE boolean on "
    "the caiso-200 keeper recipe (caiso_storage_adaptive_expectation) with "
    "TWO rule-23 frozen constants (caiso_adaptive_half_life_days = 30.0, "
    "caiso_adaptive_beta = 0.5945) identified in the pre-registered caiso-204 "
    "Phase-0 instrument on the MEASURED 2023-2025 daily evening storage offer "
    "surface (PUB_BID_DAM 585-date balanced subset, caiso-178 classifier; "
    "identification evidence is measured CONDUCT, never a price residual). "
    "PHASE-0 FAILED ITS PRE-REGISTERED G-BOOT GATE and stands recorded "
    "unrewritten (results/calibration/caiso204_adaptive_phase0.json: the "
    "keeper's own committed scored path holds 0/1/0 event days at $200 — the "
    "C3c-ledgered tail deficit — so the armed floor tops out at $14.5); "
    "Phase-1 was ENTERED ON OWNER ORDER over that recorded wall "
    "(" + _OWNER_ORDER + ") — an explicit owner act over a recorded "
    "mechanical kill, both records standing. Mechanism, armed path: two-pass "
    "P1 — pass 1 solves on the keeper's own offers; the model's OWN daily CA "
    "demand-weighted P1 energy dual (PURE lambda — CAISO's scored backcast "
    "price IS the energy-only dual, caiso-137b; ZERO measured content, rule "
    "13) yields daily events (day-max >= $200); their trailing EWMA frequency "
    "(half-life 30 d, 120-d window, per-solve-year reset) x beta, clipped to "
    "[0, 1], is P_hat(d); BATTERY discharge (pumped storage excluded per the "
    "caiso-204 S4 classifier) is floored at max(vom, P_hat x $1,000 park cap) "
    "in hours h18-21 PT ONLY through the existing p1_storage_discharge_cost "
    "seam; pass 2 is THE scored pass; P0 untouched; exactly one adaptation "
    "pass. Self-extinguishing where the model's own path is spike-free — the "
    "caiso-204 G-BOOT wall predicts byte-identical 2023/2025 and a "
    "near-inert 2024, so this A/B buys the honest full-magnitude stamp, not "
    "a gate move. Judged ONLY by the PRECOMMIT-caiso205 §4 direction-blind "
    "kill-gate table (caiso205_gates.json); the mechanical verdict is "
    "recorded unrewritten and promotion is a separate owner decision. C3a is "
    "inadmissible as acceptance evidence in either direction (caiso-203 "
    "owner ruling)."
)

_ATTEST_CTL = (
    "caiso-205 session (2026-08-19): CONTROL member of the "
    "adaptive-expectation A/B — the caiso-200 keeper recipe replayed "
    "byte-faithfully at HEAD (replay_keeper from the keeper bundle's "
    "meta.json, no --set), the G-REPRO base: every keeper hourly sidecar "
    "sha256-compared to this replay (caiso205_gates.json g_repro). The "
    "recipe, mechanisms and identification are the keeper's own; the "
    "attestation below is the keeper's, carried with magnitudes re-measured "
    "on this replay. caiso_storage_adaptive_expectation is at its default "
    "(off)."
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
        default=[2023, 2024],
        help="years whose C3c still FAILS on the ARM's own scorecard "
        "(default: 2023 2024 — the keeper's own ledger state; 2025 PASSES)",
    )
    ap.add_argument(
        "--control-still-failing",
        type=int,
        nargs="*",
        default=[2023, 2024],
        help="years whose C3c still FAILS on the CONTROL's scorecard",
    )
    args = ap.parse_args()
    _write(
        args.control,
        _ATTEST_CTL,
        args.control_still_failing,
        "the caiso-205 control replay",
    )
    _write(
        args.arm,
        _ATTEST_ARM,
        args.still_failing,
        "the caiso-205 adaptive-expectation arm",
    )


if __name__ == "__main__":
    main()
