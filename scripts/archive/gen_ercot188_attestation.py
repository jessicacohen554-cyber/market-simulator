"""Write the ercot-188 A/B pair's `calibration_attestation.json` files.

Derived from the ercot185 keeper's attestation, which is the correct base
because the ercot-188 arm is a **single slicing-resolution delta on that recipe**
and adds **ZERO free parameters** — so the DOF ledger (`free_parameters`) is
carried verbatim, which is itself the G-DOF evidence. Only
`governance.attested_by` and the carried C3c `exceptions` magnitudes are
re-written per run.

Usage::

    python scripts/gen_ercot188_attestation.py \
        --base results/calibration/ercot188_topfine_ctl_A \
        --arm  results/calibration/ercot188_topfine_arm_B \
        --keeper results/calibration/ercot185_shapedarm_B
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}

_CONTROL_ATTEST = (
    "ercot-188 2026-08-11 — the A/B CONTROL: a same-HEAD replay of the "
    "2026-08-09-ercot185-shaped-partial keeper recipe with the ercot-188 gate "
    "at its DEFAULT (ercot_econ_curve_top_refine=false), i.e. each plant's "
    "economic ramp still cut into offer_curve_smoothing_n = 6 EQUAL-WIDTH MW "
    "blocks. It exists because the ERCOT keeper is known not to reproduce "
    "byte-for-byte at current main (ercot-173 §5, carried through "
    "ercot-174/185/186), so every ercot-188 gate is scored on a same-HEAD pair "
    "rather than against the committed keeper's ledgered numbers. No mechanism "
    "is armed and no free parameter is added; the DOF ledger is the keeper's, "
    "verbatim. docs/PRECOMMIT-ercot188-cliff-offer-curve-refinement-2026-08-11.md"
)

_ARM_ATTEST = (
    "ercot-188 2026-08-11 — the control plus ONE delta: "
    "ercot_econ_curve_top_refine=true (scripts/replay_keeper.py --set), SCHEME "
    "R1 of the (c2) cliff-resolving offer-curve refinement, built under the "
    "OWNER'S option (B) BUILD ANYWAY on the MEMO-ercot184 §8 card as a "
    "STRUCTURAL-FIDELITY purchase (rule 1 [R-STRUCT]). *** THE MEMO'S OWN "
    "RECOMMENDATION WAS (A) CLOSE THE LANE AND IT IS NOT REWRITTEN: ercot-184 "
    "measured (c2)'s reach across the WHOLE FAMILY of MW-preserving "
    "re-slicings at +$1.99/MWh against the +$14.44 bar (13.8 %), failing its "
    "pre-registered G-REACH bar of +$5.00 by 2.5x, because the LP clears at "
    "ladder position ~0.70 and re-slicing moves it only +0.055 (ceiling 0.833 "
    "vs reality's 0.9976). A result near +$1.99/MWh is this lane's EXPECTED "
    "outcome, not a failure of it. *** THE OBJECT: the equal-width form's "
    "finest expressible within-plant position is 1/n of the econ ramp, so the "
    "model's supply-curve top is a 6-block approximation that CANNOT express a "
    "cliff — while reality's marginal price forms inside the top 0.24 % of the "
    "marginal resource's own submitted curve (q_act p50 0.9976, ercot-180). "
    "THE MECHANISM: the ramp's TOP block is re-sliced n ways with the body's "
    "n-1 blocks left expression-for-expression identical (2n-1 = 11 slices, "
    "top sliver 2.778 % of the ramp, total curve MW preserved EXACTLY — "
    "measured deviation 0.000000 MW). ZERO NEW SCALARS (rule 23): the split "
    "point is 1 - 1/n, the boundary the ramp is ALREADY sliced at, and the "
    "sub-slice count is the same n — both the registered "
    "offer_curve_smoothing_n — so the DOF ledger is the keeper's verbatim and "
    "n_residual does not grow; the structural grounding is two measurements "
    "that PREDATE the build (MEMO §4.2/§4.3) and never a residual. "
    "ERCOT-GATED because the slicer is not (rule 25): SP-2 proves all five "
    "non-ERCOT ISOs byte-identical with the gate ARMED. *** THE ACCEPTED COST, "
    "STATED NOT HIDDEN: this writes heat rates into the BASE fleet, i.e. the "
    "P0 objective, so unlike every ERCOT offer-surface mechanism since "
    "ERCOT-86 it does NOT ride the P1-only mc_bid_adjust seam — it BREACHES "
    "that seam, PERMANENTLY FORFEITS the family's P0 bit-identity proof, and "
    "reprices ~16.5 GW of committed gas through the P1 startup-amortization "
    "channel. That cost was costed (MEMO §3.3) and accepted by the owner as "
    "the price of the structural fidelity. "
    "docs/PRECOMMIT-ercot188-cliff-offer-curve-refinement-2026-08-11.md"
)


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year, on the SCORER'S OWN basis.

    **This must reproduce ``ordc.hoursGt200.model``**, the quantity
    ``calibration_verdict.score_price_tail`` gates C3c on: the energy-only P1
    dual, maxed across zones within the hour. Originally written here as a
    DEMAND-WEIGHTED mean — a basis the scorer never uses — which ercot-192
    filed as an open defect (its own copy fixed, this one not): the two bases
    disagree (2023 max-zonal 58 h vs demand-weighted 57 h on the ercot-192
    arm), so an attestation regenerated from this script would quote a
    magnitude the scored record contradicts. Re-pointed at ercot-193 to the
    scorer's max-zonal basis, mirroring ``gen_ercot192_attestation.py``.
    """
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
    """Write ``bundle``'s attestation from the keeper's, re-measuring C3c."""
    att = json.loads(json.dumps(keeper_attest))  # deep copy
    att["governance"]["attested_by"] = attested_by
    counts = _tail_counts(bundle)
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") == "price_tail" and year in counts:
            exc["magnitude"] = (
                f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
                f"> $200/MWh (re-measured on the ercot-188 {tag})"
            )
            exc["reason"] = re.sub(
                r"\s*CARRIED ONTO THE ercot-18[68].*$", "", exc.get("reason", "")
            ) + (
                " CARRIED ONTO THE ercot-188 "
                f"{tag.upper()}: the (c2) refinement changes the RESOLUTION at "
                "which the model can quote its own supply curve, not the offer "
                "conduct the measured surfaces represent, and the exhaustion "
                "record is unchanged — ercot-184 measured the whole family of "
                "MW-preserving re-slicings at a +$1.99/MWh ceiling because the "
                "LP's clearing position is a QUANTITY fact; the counts are "
                "re-measured on this run and reported at full magnitude."
            )
    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(f"wrote {path} (tail counts {counts})")


def main() -> None:
    """Write both bundles' attestations from the keeper's."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument(
        "--keeper",
        type=Path,
        default=REPO / "results/calibration/ercot185_shapedarm_B",
    )
    args = ap.parse_args()

    keeper_attest = json.loads(
        (args.keeper / "calibration_attestation.json").read_text()
    )
    _write(args.base, keeper_attest, _CONTROL_ATTEST, "control")
    _write(args.arm, keeper_attest, _ARM_ATTEST, "arm")


if __name__ == "__main__":
    main()
