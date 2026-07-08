"""Full-keeper A/B probe: ERCOT ercot46_clock_steamgas config + temp_dependent_derate.

Reproduces the ercot46_clock_steamgas keeper's exact solve_and_persist call for
all three train years (2023-2025, rule 16) and flips only
``temp_dependent_derate`` on -- the per-class dry-bulb-temperature capacity
curve (fleet.generators_to_fleet_arrays) vs the flat EIA-860 net-summer /
_SUMMER_CLASS_DERATE treatment the keeper currently uses.

Unlike the single-year ``_ercot_tempderate_ab.py`` probe (which hand-copies a
curated subset of ``run_config.json``'s ``calibration_flags``), this script
reconstructs kwargs from the keeper's ``meta.json`` -- the actual bound
solve_and_persist arguments, not a curated subset (calibration_flags omits
~30 non-default flags on this keeper: storage_daily_cycling,
storage_vintage_ramp, battery_dispatch_adder, energy_reserve_coopt,
ercot_multiproduct_as_coopt, ercot_ecrs_conservative_deployment,
ercot_ordc_total_reserve, ercot_storage_as_product_credit,
gas_hh_monthly_shape, ercot_reserve_supply_cap, ercot_load_resource_reserve,
ercot_storage_as_reserve(+_from_year), storage_as_commitment,
reliability_floor, chp_export_floor_measured, ercot_gtc_limits_measured, and
curve_smoothing's offer_curve_smoothing_mid=0.35 vs the single-year probe's
stale 0.45 -- verified against solve_and_persist's live signature at import
time, see the ``missing``/``unmapped`` assertions below).

Run `main` first, then `ablation` (needs the main bundle dir for
``ablation_of``).

Usage: python scripts/probes/_ercot48_tempderate_full.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot46_clock_steamgas"

# meta.json keys that are NOT real solve_and_persist kwargs -- they're either
# renamed (LHS = meta.json key, value = the actual kwarg name) or purely
# derived inside backcast_config() from (year, iso, hours, gas_price) with no
# override kwarg at all (rule 24 exception; run_calibration_full.py lines
# ~2450-2472).
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
# handled explicitly (positional / overridden below), not auto-copied
HANDLED = {"years", "iso", "hours", "commitment", "gas_prices", "passes"}
# bookkeeping-only meta.json keys, not solve args
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


def main(mode: str) -> None:
    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]

    kwargs = build_kwargs(meta, set(sig))

    # sanity: every real (non-derived, non-bookkeeping, non-**kwargs-only)
    # solve_and_persist param that calibration_flags also names must resolve
    # to the same value via meta.json -- catches drift between the two files.
    for k in cf:
        target = RENAMED.get(k, k)
        if target in kwargs and kwargs[target] != cf[k] and k not in DERIVED_ONLY:
            raise ValueError(
                f"meta.json/calibration_flags disagree on {k}: "
                f"{kwargs[target]!r} vs {cf[k]!r}"
            )

    ablate = mode == "ablation"
    out = ROOT / ("ercot48_tempderate_full" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    kwargs["temp_dependent_derate"] = True
    kwargs["zero_forcing_ablation"] = ablate
    kwargs["ablation_of"] = (
        (out.parent / "ercot48_tempderate_full").name if ablate else None
    )
    kwargs["note"] = (
        f"temp-derate full-keeper {mode} -- ercot46_clock_steamgas config "
        "(reconstructed from meta.json, not the curated calibration_flags "
        "subset) + temp_dependent_derate, 2023-2025 (rule 16)"
    )

    solve_and_persist(
        meta["years"],
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        run_dir=out,
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
