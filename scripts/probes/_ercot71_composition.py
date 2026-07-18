"""ERCOT-71 availability/offer-belt COMPOSITION — full-span registered bundle.

Reconstructs the promoted ERCOT keeper (2026-07-15-ercot66-storage-rebasis)
from its meta.json and applies the two ERCOT-71 composition deltas, moved
TOGETHER (the ERCOT-67 coupling clause, quantified by ERCOT-70):

* LEG A -- ``ercot_noncampd_plant_availability`` (measured per-plant
  availability for the CAMPD-blind gas fleet: Kiamichi/Hidalgo/AVR, from the
  60-Day DAM disclosure per-plant live HSL + EIA-923 zero months). Removes the
  +1.2-1.7 GW phantom CC the ERCOT-70 supply-mix decomposition named on the
  moderate-tightness under-priced hours.
* LEG B -- ``ercot_offer_surface_midcurve_conditional`` (the ERCOT-69 measured
  DAM mid-curve offer belt, 18-22x at within-unit shares 0.95-0.99). Prices the
  covered CC fleet's committed shares once leg A pushes them into the belt.

Unlike the rule-16 ladder probe (``_ercot68_ladder_probe.py``, single-year
throwaways), this is the FULL-SPAN 2023-2025 bundle (rule 16) intended for the
backcast dashboard (rule 15). Keeper promotion is the OWNER's, never this
script's.

Usage::

    python scripts/probes/_ercot71_composition.py \
        --years 2023 2024 2025 --out-name ercot71_composition_availbelt
    # single delta for the full-span leg isolation: --legA-only / --legB-only
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ercot61_stgas_drag_probe import build_kwargs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot66_storage_rebasis_measuredas"

LEG_A = "ercot_noncampd_plant_availability"
LEG_B = "ercot_offer_surface_midcurve_conditional"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out-name", default="ercot71_composition_availbelt")
    ap.add_argument("--legA-only", action="store_true")
    ap.add_argument("--legB-only", action="store_true")
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    kwargs[LEG_A] = not args.legB_only
    kwargs[LEG_B] = not args.legA_only
    legs = [n for n, on in ((LEG_A, kwargs[LEG_A]), (LEG_B, kwargs[LEG_B])) if on]
    kwargs["note"] = (
        "ERCOT-71 availability/offer-belt COMPOSITION on the ercot66-storage-"
        "rebasis keeper. Legs: " + ", ".join(legs) + ". LEG A = measured "
        "per-plant availability for the CAMPD-blind gas fleet (Kiamichi/Hidalgo/"
        "AVR; 60-Day DAM disclosure live HSL + EIA-923 zero months, "
        "scripts/data/derive_ercot_noncampd_availability.py) -- removes the ERCOT-70 "
        "+1.2-1.7 GW phantom CC. LEG B = ERCOT-69 measured DAM mid-curve offer "
        "belt (ercot_offer_midcurve_condbinned.json). Both zero-DOF measured "
        "(rules 13/14/23). Full-span 2023-2025 (rule 16)."
    )

    out = ROOT / args.out_name
    out.mkdir(parents=True, exist_ok=True)
    solve_and_persist(
        args.years,
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        run_dir=out,
        **kwargs,
    )
    print(f"DONE -> {out} (legs: {legs}, years: {args.years})")


if __name__ == "__main__":
    main()
