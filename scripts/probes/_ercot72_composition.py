"""ERCOT-72 covered-CC / CT composition — full-span registered bundle.

Reconstructs the ERCOT-71 keeper configuration (the ercot66-storage-rebasis
recipe + LEG A ``ercot_noncampd_plant_availability``, the promoted
2026-07-16-ercot71-noncampd-availability base) and arms the ERCOT-72
composition mechanism:

* ``ercot_offer_surface_cleared_share`` — the measured DAM cleared-share
  boundary + above-boundary offer wall (scripts/data/derive_ercot_dam_cleared_share
  .py). Prices the merchant CC/CT econ capacity ABOVE the bin's measured DAM
  cleared share at the bin's measured offered-but-uncleared wall — the
  no-must-offer participation cliff the ERCOT-72 measurement named on the
  moderate May shoulders (8.6 GW of CC live HSL not offered at any price,
  63 MW of spinning AS, congestion secondary).

FULL-SPAN 2023-2025 bundle (rule 16) intended for the backcast dashboard
(rule 15). Keeper promotion is the OWNER's, never this script's.

Usage::

    python scripts/probes/_ercot72_composition.py \
        --years 2023 2024 2025 --out-name ercot72_cleared_share_fullspan
    # --base-only reproduces the ERCOT-71 leg-A base (no new mechanism)
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

LEG_A = "ercot_noncampd_plant_availability"  # the ERCOT-71 keeper base
LEG_CS = "ercot_offer_surface_cleared_share"  # the ERCOT-72 mechanism


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out-name", default="ercot72_cleared_share_fullspan")
    ap.add_argument("--base-only", action="store_true")
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    kwargs[LEG_A] = True
    kwargs[LEG_CS] = not args.base_only
    legs = [n for n, on in ((LEG_A, True), (LEG_CS, kwargs[LEG_CS])) if on]
    kwargs["note"] = (
        "ERCOT-72 covered-CC/CT COMPOSITION on the ERCOT-71 leg-A base "
        "(ercot66-storage-rebasis recipe + measured non-CAMPD per-plant "
        "availability). Legs: " + ", ".join(legs) + ". LEG CS = the measured "
        "DAM cleared-share offer boundary (no DAM must-offer: the merchant "
        "gas econ capacity above the bin's MEASURED cleared share of live "
        "capability is floored at the bin's MEASURED offered-but-uncleared "
        "wall; scripts/data/derive_ercot_dam_cleared_share.py, condition-binned by "
        "net-load percentile, zero fitted scalars — rules 13/14/26). "
        "Full-span 2023-2025 (rule 16)."
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
