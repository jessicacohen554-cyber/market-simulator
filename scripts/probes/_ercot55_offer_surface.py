"""ERCOT ercot55 keeper-config offer-surface runner (C2-fix basis).

Reconstructs the ``ercot53_hsl_930fill`` KEEPER's exact ``solve_and_persist``
call from its committed ``meta.json`` (the reliable path established by
``scripts/probes/_ercot49_offer_retune.py`` / ``_ercot50_offer_surface.py`` —
the curated ``calibration_flags`` subset omits ~30 non-default flags) and layers
ONLY the measured G-22 §8 heterogeneity-preserving condition-responsive offer
surface (``ercot_offer_surface_conditional``) on top. All surface parameters
come from the 60-Day DAM disclosure derivation
(``scripts/data/derive_dam_offer_hrmults.py --condition-binned`` →
``data/raw/_validation-source/offer_curve_dam_hrmults_condbinned.json``) —
zero fitted values. The keeper's ``offer_curve_overrides``/``deltas`` stand
(the surface reprices the peak-band RUNGS around the keeper's resolved peak,
superseding the single static height with the measured distribution, rule 19).

Delta vs the rejected ercot50 probe: the base config is the promoted ercot53
keeper (coal net-summer derate + ORDC cap-dual adder + 2024 HSL 930-fill, all
absent from ercot50's ercot46 basis), scored on rubric v2.4, and the solve
runs on the merged C2 gas-counting fix (EIA-930 long-format gap fill +
NG:OTH threading, PR #1929) — a code/data-level change needing no flag.

Single-year invocations are throwaway diagnostics (rule 16: only full
2023-2025 bundles may be registered on the dashboard).

Usage::

    python scripts/probes/_ercot55_offer_surface.py OUT_NAME \
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
KEEPER = ROOT / "ercot53_hsl_930fill"

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
        "ercot55: measured conditional offer surface on the ercot53 keeper "
        f"(ercot_offer_surface_conditional={bool(args.surface)}, years {args.years}) "
        "-- ercot53_hsl_930fill config reconstructed from meta.json verbatim; "
        "offer curves untouched; solved on the merged C2 gas-counting fix "
        "(EIA-930 long-format gap fill + NG:OTH, PR #1929)"
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
    print(f"DONE surface={args.surface} ablation={args.ablation} -> {out}")


if __name__ == "__main__":
    main()
