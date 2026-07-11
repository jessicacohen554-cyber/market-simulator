"""Observation-only: reconstruct the ercot56-nucwin keeper config and solve a
single year, writing the bundle so we can inspect storage discharge shape.

NOT a registered run (rule 16 throwaway). Mirrors _ercot58_ab.py's meta.json ->
solve_and_persist mapping but layers NO deltas — the pure keeper config.
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
    ap = argparse.ArgumentParser()
    ap.add_argument("out_name")
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    ap.add_argument(
        "--set", dest="overrides", action="append", default=[], metavar="KEY=VAL"
    )
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    for ov in args.overrides:
        key, _, val = ov.partition("=")
        if key not in sig:
            raise ValueError(f"--set {key!r} is not a solve_and_persist kwarg")
        low = val.strip().lower()
        if low in ("1", "true", "yes", "on"):
            kwargs[key] = True
        elif low in ("0", "false", "no", "off"):
            kwargs[key] = False
        else:
            try:
                kwargs[key] = float(val)
            except ValueError:
                kwargs[key] = val
    kwargs["zero_forcing_ablation"] = False
    kwargs["ablation_of"] = None
    kwargs["note"] = "observation throwaway (keeper config), not registered"

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
