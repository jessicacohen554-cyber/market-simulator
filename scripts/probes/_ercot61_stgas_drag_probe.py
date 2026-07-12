"""ERCOT-61 rule-16 throwaway: the ercot56-nucwin keeper reconstructed from
its meta.json with ZERO deltas, solved for 2023 only, to dump the per-unit
dispatch + drag-floor arrays behind the binding-regime ST_GAS question.

The ST_GAS binding-regime lane (ERCOT-58 §5 / ERCOT-60 §7.3): the keeper
serves +1.3 GW MORE top-30 %-net-load-hour load with ST_GAS than CAMPD gross
shows reality did (model 4,841 vs 3,555 MW), while `st_netload_drag` forces
25-33 % of class energy under an all-hours declared window. The decision this
probe feeds: do the binding-hour excess MWh sit ON the `st_netload_drag`
min-gen floor (defect = the hinge's high-net-load extrapolation — the hinge
was derived from OVERNIGHT CF vs net-load,
``docs/ercot-st-gas-netload-drag-2026-06.md``, but applies at ALL hours) or
ABOVE it economically (defect = the ST_GAS offer curve)? Analysis mask:
``scripts/probes/_ercot61_stgas_binding_mask.py`` over this bundle's
``dispatch/2023_P1.parquet`` + ``floors/2023_P1.npz`` + CAMPD shared input.

NEVER registered (CLAUDE.md rule 16 — single-year diagnostic probe).

Usage::

    python scripts/probes/_ercot61_stgas_drag_probe.py [OUT_NAME] [--years 2023]
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot56_nucwin"

# meta.json keys that are NOT real solve_and_persist kwargs — the same
# derivation as _ercot_storage_deploy_ab.py / _ercot58_ab.py.
RENAMED = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
DERIVED_ONLY = {
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
}
HANDLED = {"years", "iso", "hours", "commitment", "gas_prices", "passes"}
BOOKKEEPING = {"timestamp", "git_sha", "highspy_version", "shared_inputs"}


def build_kwargs(meta: dict, sig_params: set) -> dict:
    """Map the keeper's meta.json onto solve_and_persist kwargs."""
    kwargs = {}
    for k, v in meta.items():
        if k in HANDLED or k in DERIVED_ONLY or k in BOOKKEEPING:
            continue
        if k in RENAMED:
            kwargs[RENAMED[k]] = v
        elif k in sig_params:
            kwargs[k] = v
        else:
            raise ValueError(f"meta.json key {k!r} has no solve_and_persist home")
    return kwargs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "out_name",
        nargs="?",
        default="ercot61_stgas_drag_2023",
        help="throwaway bundle name under results/calibration/",
    )
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    # ZERO deltas vs the promoted keeper: this probe only dumps the keeper's
    # own per-unit dispatch + floors for the binding-hour mask analysis.
    kwargs["note"] = (
        "ercot61 rule-16 throwaway (NEVER register): ercot56_nucwin keeper "
        "config reconstructed from meta.json, zero deltas, 2023 only — dumps "
        "dispatch/floors for the binding-regime ST_GAS on-floor-vs-above-floor "
        "mask (ERCOT-58 §5 / ERCOT-60 §7.3 lane)."
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
    print(f"DONE -> {out}")


if __name__ == "__main__":
    main()
