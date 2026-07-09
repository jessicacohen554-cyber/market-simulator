"""ERCOT ercot50 condition-responsive offer-surface probe runner.

Reconstructs the ercot46_clock_steamgas keeper's exact ``solve_and_persist`` call
from its committed ``meta.json`` (same approach as
``scripts/probes/_ercot49_offer_retune.py`` — the reliable path; the curated
``calibration_flags`` subset omits ~30 non-default flags) and layers ONLY the
new G-22 §8 heterogeneity-preserving condition-responsive offer surface
(``ercot_offer_surface_conditional``) on top. It does NOT touch the offer curves
(the keeper's ``offer_curve_overrides``/``deltas`` stand — the surface reprices
the peak-band RUNGS around the keeper's resolved peak, superseding the single
static height with the measured distribution, rule 19) and does NOT force the
rejected ``temp_dependent_derate`` (closed 2026-07-09).

Single-year invocations are throwaway diagnostics for finding the level (rule 16:
only full 2023-2025 bundles may be registered on the dashboard).

Usage::

    python scripts/probes/_ercot50_offer_surface.py OUT_NAME \
        [--years 2023 [2024 2025]] [--surface/--no-surface] [--ablation] \
        [--ablation-of NAME] [--set KEY=BOOL]
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot46_clock_steamgas"

# meta.json keys that are NOT real solve_and_persist kwargs (see
# _ercot48_tempderate_full.py / _ercot49_offer_retune.py for the derivation).
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
    ap.add_argument(
        "--surface",
        dest="surface",
        action="store_true",
        default=True,
        help="enable ercot_offer_surface_conditional (default on)",
    )
    ap.add_argument("--no-surface", dest="surface", action="store_false")
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

    kwargs["ercot_offer_surface_conditional"] = bool(args.surface)
    for ov in args.overrides:
        key, _, val = ov.partition("=")
        if key not in sig:
            raise ValueError(f"--set {key!r} is not a solve_and_persist kwarg")
        kwargs[key] = val.strip().lower() in ("1", "true", "yes", "on")
    kwargs["zero_forcing_ablation"] = args.ablation
    kwargs["ablation_of"] = args.ablation_of if args.ablation else None
    kwargs["note"] = (
        "G-22 §8 heterogeneity-preserving condition-responsive offer surface "
        f"(ercot_offer_surface_conditional={bool(args.surface)}, years {args.years}) "
        "-- ercot46_clock_steamgas config reconstructed from meta.json; "
        "offer curves and temp_dependent_derate unchanged"
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
    print(f"DONE surface={args.surface} -> {out}")


if __name__ == "__main__":
    main()
