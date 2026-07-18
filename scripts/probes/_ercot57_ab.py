"""ERCOT ercot57 runner: ercot56-nucwin keeper recipe + measured thermal availability.

Reconstructs the PROMOTED ercot56-nucwin keeper's exact ``solve_and_persist``
call from its committed ``meta.json`` (the ``_ercot55_ab.py`` reconstruction
path, pointed at the ercot56_nucwin bundle — whose meta already carries the
conditional offer surface and the window-grain measured nuclear availability)
and layers ONE measured-input delta: ``ercot_thermal_dam_availability`` — the
measured 60-Day DAM disclosure class-day thermal availability rescale
(CC_REGULAR + CT_PEAKER), the June/Sep-2023 scarcity-formation root-cause fix
(docs/DIAGNOSIS-ercot-june2023-scarcity-formation-2026-07.md). Zero new free
parameters: the class-day series is measured disclosure data
(scripts/data/derive_ercot_thermal_dam_availability.py, frozen deriver).

Usage::

    python scripts/probes/_ercot57_ab.py OUT_NAME \
        [--years 2023 2024 2025] [--ablation --ablation-of NAME] \
        [--set KEY=BOOL]
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

# meta.json keys that are NOT real solve_and_persist kwargs (same derivation
# as _ercot55_ab/_ercot49/_ercot50: RENAMED map to differently-named kwargs;
# DERIVED_ONLY are top-level echoes of values that really live inside
# ``coal_prb_sigmoid_overrides``; HANDLED are positional/explicit args;
# BOOKKEEPING is provenance).
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
    ap.add_argument("out_name", help="bundle name under results/calibration/")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--ablation-of", default=None, help="bundle name of the main run")
    ap.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=BOOL",
        help="override one solve_and_persist boolean kwarg (diagnostic probes only)",
    )
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    # THE one delta vs the promoted keeper: the measured class-day thermal
    # availability rescale (backcast-gated in the fleet application).
    kwargs["ercot_thermal_dam_availability"] = True
    for ov in args.overrides:
        key, _, val = ov.partition("=")
        if key not in sig:
            raise ValueError(f"--set {key!r} is not a solve_and_persist kwarg")
        kwargs[key] = val.strip().lower() in ("1", "true", "yes", "on")
    kwargs["zero_forcing_ablation"] = args.ablation
    kwargs["ablation_of"] = args.ablation_of if args.ablation else None
    kwargs["note"] = (
        "ercot57: ercot56_nucwin keeper config reconstructed from meta.json + "
        "ercot_thermal_dam_availability (measured 60-Day DAM disclosure "
        "class-day thermal availability, CC_REGULAR/CT_PEAKER rescale) — the "
        "June/Sep-2023 phantom reserve-shortfall root-cause fix; zero new "
        "free parameters (docs/DIAGNOSIS-ercot-june2023-scarcity-formation-"
        "2026-07.md)"
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
    print(f"DONE ablation={args.ablation} -> {out}")


if __name__ == "__main__":
    main()
