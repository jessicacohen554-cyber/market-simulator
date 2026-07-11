"""ERCOT ercot58 runner: the ercot57 JOINT ROUND (owner-sanctioned 2026-07-11).

Reconstructs the PROMOTED ercot56-nucwin keeper's exact ``solve_and_persist``
call from its committed ``meta.json`` (the ``_ercot57_ab.py`` reconstruction
path) and layers the THREE joint-round deltas the ERCOT-57 calibration-log
entry filed as the structurally-indicated completion:

* ``ercot_thermal_dam_availability`` — the measured 60-Day DAM disclosure
  class-day thermal availability rescale (built at ercot57; the June/Sep-2023
  phantom reserve-shortfall root-cause fix).
* ``ercot_online_capacity_envelope_measured`` — the G-22 on-line-capacity
  envelope RE-IDENTIFIED on the measured-fleet basis (share = committed HSL /
  measured AVAILABLE capacity for the disclosure-covered classes; LP basis =
  the fleet's finished availability). Identification gate PASSED 2026-07-11
  (binding +4/+0/−3%, pooled extreme tail −0.0%, coverage 2.10×;
  ``scripts/validate_ercot_online_capacity.py --measured``).
* ``ercot_ordc_only_scarcity`` — pre-RTC+B ORDC-only reserve-scarcity pricing
  (v2, realized-room RTORPA): per-product VOLL ladders → plan-hold epsilon;
  the in-LP ORDC total family is REMOVED (rule 19) and RTORPA is computed
  post-solve on the P1 realized envelope room (the published SCED-plus-adder
  settlement construction, ``scarcity.ercot_ordc_realized_adder``);
  ECRS_withheld keeps its rigid VOLL step. The v1 in-LP form (total family
  demanding the span inside the envelope) reproduced the ercot43 §7.4 defect
  on the honest fleet (62 GWh load shed, coal parked at the Aug-2023 peak) —
  the 2023-only rule-16 probe that adjudicated it is documented in the
  ERCOT-58 calibration-log entry.

Zero new fitted parameters: the availability series and the envelope share /
deliv tables are measured MW quantities (rule 13), and the ORDC-only design is
a market-design correction (rule 1), not a knob. Decomposition arms via
``--set KEY=BOOL`` (e.g. ``--set ercot_ordc_only_scarcity=false``).

Usage::

    python scripts/probes/_ercot58_ab.py OUT_NAME \
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
# as _ercot57_ab/_ercot55_ab: RENAMED map to differently-named kwargs;
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
        help="override one solve_and_persist boolean kwarg (decomposition arms)",
    )
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    # The THREE joint-round deltas vs the promoted keeper (ERCOT-57 filed path).
    kwargs["ercot_thermal_dam_availability"] = True
    kwargs["ercot_online_capacity_envelope_measured"] = True
    kwargs["ercot_ordc_only_scarcity"] = True
    # v2: the realized-room RTORPA replaces the keeper's in-LP ORDC total
    # family and its cap-dual adder (rule 19 — one RT reserve-scarcity price).
    kwargs["ercot_ordc_total_reserve"] = False
    kwargs["ercot_ordc_cap_dual_adder"] = False
    for ov in args.overrides:
        key, _, val = ov.partition("=")
        if key not in sig:
            raise ValueError(f"--set {key!r} is not a solve_and_persist kwarg")
        kwargs[key] = val.strip().lower() in ("1", "true", "yes", "on")
    kwargs["zero_forcing_ablation"] = args.ablation
    kwargs["ablation_of"] = args.ablation_of if args.ablation else None
    kwargs["note"] = (
        "ercot58: ercot56_nucwin keeper config reconstructed from meta.json + "
        "the ercot57 JOINT ROUND (owner-sanctioned 2026-07-11): measured "
        "thermal DAM availability + measured-fleet-basis on-line-capacity "
        "envelope (identification gate PASSED: binding +4/+0/-3%, pooled "
        "extreme tail -0.0%) + pre-RTC+B ORDC-only scarcity pricing "
        "(per-product VOLL ladders -> plan-hold epsilon; ORDC total curve is "
        "the sole RT reserve-scarcity price). Zero new fitted parameters "
        "(docs/DIAGNOSIS-ercot-june2023-scarcity-formation-2026-07.md; "
        "docs/handoffs/ercot-online-capacity-envelope-2026-07.md §7.4)"
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
