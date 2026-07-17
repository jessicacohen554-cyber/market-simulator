"""ERCOT-77 steam participation cliff — full-span bundle on the ercot73 keeper.

Reconstructs the promoted ERCOT keeper (2026-07-16-ercot73-state-wall) from its
bundle meta.json and arms the single ERCOT-77 delta:

* ``ercot_offer_surface_cleared_share_steam`` — the steam (ST_GAS) extension
  of the measured DAM cleared-share wall: ST_GAS committed + econ* tranche
  rows whose within-plant midpoint exceeds the hour's bin's MEASURED steam
  cleared share (the "ST" block of the frozen artifact — GSREH/GSNONR/GSSUP,
  scripts/derive_ercot_dam_cleared_share.py) are floored at the bin's MEASURED
  steam offer wall, scaled by the measured steam commitment-loading state
  weight (the "ST" block of scripts/derive_ercot_commitment_loading_state.py;
  the keeper's state flag is already armed). The ERCOT-73 leg-c finding: live
  steam HSL 5.9 GW vs 1.2 GW DA-cleared on the May-2024 shoulder family while
  the model's flat committed rungs (~$30) hand the LP several GW of steam
  reality priced $57-100 beyond its DA position.

Rule-19 reconcile (recorded in the ScenarioConfig field comment): the cliff
owns the ABOVE-DA-position ST_GAS offer levels (committed + econ*); the drag
keeps the min-gen QUANTITY scaffolding; peak rungs stay with
``ercot_offer_surface_conditional``.

FULL-SPAN 2023-2025 bundle (rule 16) intended for the backcast dashboard
(rule 15). Keeper promotion is the OWNER's, never this script's.

Usage::

    uv run python scripts/probes/_ercot77_steam_cliff.py \
        --years 2023 2024 2025 --out-name ercot77_steam_cliff_fullspan
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from replay_keeper import build_kwargs  # noqa: E402
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot73_state_wall_fullspan"

LEG_ST = "ercot_offer_surface_cleared_share_steam"  # the ERCOT-77 delta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out-name", default="ercot77_steam_cliff_fullspan")
    args = ap.parse_args()

    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    kwargs[LEG_ST] = True
    kwargs["note"] = (
        "ERCOT-77 steam participation cliff on the ercot73-state-wall keeper "
        "base (single delta ercot_offer_surface_cleared_share_steam=True). "
        "The ST_GAS extension of the measured DAM cleared-share wall: "
        "committed + econ* steam rows above the bin's MEASURED ST cleared "
        "share floor at the bin's MEASURED steam offer wall (GSREH/GSNONR/"
        "GSSUP, 60-Day DAM disclosure), scaled by the measured ST commitment-"
        "loading state weight (CAMPD CEMS envelope/gross x DAM awards). "
        "Rule-19 reconcile: the cliff owns above-DA-position ST offer levels; "
        "the drag keeps min-gen quantity scaffolding; peak rungs stay with "
        "the conditional surface. Zero fitted scalars (rules 13/14/23/26). "
        "Full-span 2023-2025 (rule 16)."
    )

    out = ROOT / args.out_name
    out.mkdir(parents=True, exist_ok=True)
    kwargs["years"] = [int(y) for y in args.years]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = _load_reference()
    kwargs["run_dir"] = out
    solve_and_persist(**kwargs)
    print(f"DONE -> {out} (years: {args.years})")


if __name__ == "__main__":
    main()
