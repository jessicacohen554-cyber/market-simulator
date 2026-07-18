"""ERCOT-73 commitment-STATE conditioned cleared-share wall — full-span bundle.

Reconstructs the ERCOT-71 keeper configuration (the ercot66-storage-rebasis
recipe + LEG A ``ercot_noncampd_plant_availability``, the promoted
2026-07-16-ercot71-noncampd-availability base) and arms the ERCOT-73
state-conditional composition mechanism:

* ``ercot_offer_surface_cleared_share`` — the ERCOT-72 measured DAM
  cleared-share boundary + above-boundary offer wall (frozen artifact,
  scripts/data/derive_ercot_dam_cleared_share.py).
* ``ercot_offer_surface_cleared_share_state`` — the ERCOT-73 measured
  commitment-loading state weight (frozen artifact,
  scripts/data/derive_ercot_commitment_loading_state.py): each walled row-hour's
  markup scales by w = clip((online_cap - gross)/(online_cap - cleared), 0, 1)
  — the unloaded fraction of the class's above-DA-position online capability.
  Moderate regimes keep the proven composition wall; regimes where reality
  RUC/self-commits the un-offered capacity online near cost stand it down
  (the static form's rejected tight-regime arm, resolved at hour grain).

FULL-SPAN 2023-2025 bundle (rule 16) intended for the backcast dashboard
(rule 15). Keeper promotion is the OWNER's, never this script's.

Usage::

    python scripts/probes/_ercot73_state_wall.py \
        --years 2023 2024 2025 --out-name ercot73_state_wall_fullspan
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
LEG_CS = "ercot_offer_surface_cleared_share"  # the ERCOT-72 wall
LEG_STATE = "ercot_offer_surface_cleared_share_state"  # the ERCOT-73 state


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out-name", default="ercot73_state_wall_fullspan")
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    kwargs[LEG_A] = True
    kwargs[LEG_CS] = True
    kwargs[LEG_STATE] = True
    kwargs["note"] = (
        "ERCOT-73 commitment-STATE conditioned cleared-share wall on the "
        "ERCOT-71 leg-A base (ercot66-storage-rebasis recipe + measured "
        "non-CAMPD per-plant availability). LEG CS = the ERCOT-72 measured "
        "DAM cleared-share offer boundary; LEG STATE = the ERCOT-73 measured "
        "commitment-loading state weight w = clip((online_cap - gross)/"
        "(online_cap - cleared), 0, 1) per class-hour (CAMPD CEMS envelope/"
        "gross x DAM awards; scripts/data/derive_ercot_commitment_loading_state.py"
        ", frozen rule 23, zero fitted scalars) — the wall prices the DA "
        "participation cliff only in proportion to the measured unloaded "
        "share of the above-DA online capability; RUC/self-commitment "
        "regimes stand it down (rules 13/14/26). Full-span 2023-2025 "
        "(rule 16)."
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
    print(f"DONE -> {out} (years: {args.years})")


if __name__ == "__main__":
    main()
