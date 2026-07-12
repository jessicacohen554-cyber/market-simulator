"""ERCOT storage-cycling-lane runner: the ercot56-nucwin keeper reconstructed
from its meta.json + ONE delta, ``ercot_storage_as_deployment``.

The storage-cycling-lane mechanism
(docs/DIAGNOSIS-ercot-storage-cycling-lane-2026-07.md §5): measured-award
AS->energy co-participation, forcing the measured evening storage-AS-award
draw-down as a battery discharge floor on the net-load up-ramp
(``scarcity.ercot_storage_as_deployment_mw``). Zero new fitted parameters —
every term (the award series, net-load, daily median/peak-hour) is measured
(rule 13); the only new config is the ON/OFF gate + its from-year (rule 24).

Rule-16 2023-only probes (never registered) validated the mechanism
LP-healthy and price-neutral in both a flat year (2023) and the measured
battery-benchmark year (2025, hourly shape correlation 0.807->0.820) before
this full-span run.

Usage::

    python scripts/probes/_ercot_storage_deploy_ab.py OUT_NAME \
        [--years 2023 2024 2025] [--ablation --ablation-of NAME]
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
# derivation as _ercot58_ab.py / _ercot57_ab.py / _ercot55_ab.py.
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
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    # The ONE delta vs the promoted keeper: measured-award AS->energy
    # co-participation (storage-cycling-lane fix). Requires the keeper's
    # existing storage_as_commitment=True (already in meta.json).
    kwargs["ercot_storage_as_deployment"] = True
    kwargs["ercot_storage_as_deployment_from_year"] = 2023

    kwargs["zero_forcing_ablation"] = args.ablation
    kwargs["ablation_of"] = args.ablation_of if args.ablation else None
    kwargs["note"] = (
        "ercot-storage-deploy: ercot56_nucwin keeper config reconstructed from "
        "meta.json + ercot_storage_as_deployment=True (the storage-cycling-lane "
        "fix, docs/DIAGNOSIS-ercot-storage-cycling-lane-2026-07.md §5): forces "
        "the measured hourly storage-AS-award draw-down as a battery discharge "
        "floor on the net-load up-ramp (median-crossing to daily net-load peak "
        "hour), releasing exactly the MW storage_as_commitment reserves out of "
        "the discharge cap. Zero new fitted parameters (every term measured); "
        "2023-only + 2025 measured-year rule-16 probes validated LP-healthy and "
        "price-neutral (2025 load-weighted price byte-identical) with improved "
        "storage hourly shape correlation vs EIA-930 (0.807->0.820)."
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
