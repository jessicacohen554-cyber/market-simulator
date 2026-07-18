#!/usr/bin/env python3
"""Replay an ERCOT backcast bundle with an optional CC_REGULAR peak-band patch.

The grid-serving combined cycles miss their observed >90% CF hours because the
duct-firing **peak band** (top `pct_peaking`% of nameplate at `peak`× base HR)
is a separate flat scarcity tranche above the econ ramp — see
`docs/cc-high-cf-investigation.md`. This script reproduces a keeper bundle's
exact configuration from its `run_config.json` (so the only thing that moves is
the lever under test) and re-solves with the CC_REGULAR `peak` multiplier and
`pct_peaking` share overridden to a target, into a fresh out-dir.

It drives `run_calibration_full.solve_and_persist` directly with the saved
`calibration_flags`, so every coal/CT/ST knob, sigmoid, overlay and curve-shape
setting is carried verbatim; `run_year`'s ERCOT presets
(`cc_committed_per_plant`, `cc_peaking_per_plant=False` under `cc_duct_peaking`,
…) apply exactly as in the original run.

    # validation: reproduce the baseline (no patch) and diff vs the original
    uv run python scripts/archive/cc_peak_band_probe.py \
        --base results/calibration/run115b_ccduct_prb73_relief06 \
        --years 2023 --out-dir results/calibration/_probe_repro

    # peak-band probe: cheapen + shrink the CC duct-firing band
    uv run python scripts/archive/cc_peak_band_probe.py \
        --base results/calibration/run115b_ccduct_prb73_relief06 \
        --years 2023 2024 2025 --peak 1.6 --pct-peaking 5 \
        --out-dir results/calibration/_probe_ccpeak16
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# Base default CC_REGULAR offer curve (scenarios.py); the saved run deltas are
# relative to this, so a target resolved value maps to delta = target - base.
_BASE_CC_PEAK = 2.25
_BASE_CC_PCT_PEAKING = 8.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--base",
        type=Path,
        required=True,
        help="keeper bundle to replay (reads its run_config.json)",
    )
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--peak",
        type=float,
        default=None,
        help="target resolved CC_REGULAR peak HR multiplier "
        "(e.g. 1.6). Omit to keep the baseline.",
    )
    ap.add_argument(
        "--pct-peaking",
        type=float,
        default=None,
        help="target resolved CC_REGULAR peaking share, %% of "
        "nameplate (e.g. 5). Omit to keep the baseline.",
    )
    ap.add_argument(
        "--capacity-reconcile",
        action="store_true",
        help="raise understated CC capacities to their demonstrated "
        "CAMPD peak (ScenarioConfig.cc_capacity_reconcile)",
    )
    args = ap.parse_args()

    from scripts.run_calibration_full import solve_and_persist, _load_reference

    cfg = json.loads((args.base / "run_config.json").read_text())
    flags = cfg["calibration_flags"]
    sc = cfg["scenario_config"]

    # Reconstruct the offer-curve deltas, then patch CC_REGULAR's peak band to
    # the target resolved values (delta = target - base default).
    deltas = json.loads(json.dumps(flags.get("offer_curve_deltas") or {}))
    cc = deltas.setdefault("CC_REGULAR", {})
    if args.peak is not None:
        cc["peak"] = round(args.peak - _BASE_CC_PEAK, 4)
    if args.pct_peaking is not None:
        cc["pct_peaking"] = round(args.pct_peaking - _BASE_CC_PCT_PEAKING, 4)

    resolved_peak = _BASE_CC_PEAK + cc.get("peak", 0.0)
    resolved_pct = _BASE_CC_PCT_PEAKING + cc.get("pct_peaking", 0.0)
    print(f"replay base: {args.base.name}")
    print(
        f"CC_REGULAR peak band -> peak {resolved_peak:.3f}× base HR, "
        f"pct_peaking {resolved_pct:.1f}%  (deltas {cc})"
    )
    print(f"years {args.years} -> {args.out_dir}")

    # prb_overrides is the generic ScenarioConfig override channel; the saved
    # `coal_prb_sigmoid_overrides` is exactly the non-None subset main() built.
    prb_overrides = dict(flags.get("coal_prb_sigmoid_overrides") or {})
    bit_overrides = dict(flags.get("coal_bit_sigmoid_overrides") or {})
    if args.capacity_reconcile:
        prb_overrides["cc_capacity_reconcile"] = True
        print("CC capacity reconcile: ON (raise to demonstrated CAMPD peak)")

    solve_and_persist(
        args.years,
        flags["iso"],
        int(flags.get("hours", 8760)),
        _load_reference(),
        commitment=bool(flags.get("commitment", False)),
        screen_coal=bool(flags.get("commitment_screen_coal", True)),
        run_dir=args.out_dir,
        coal_lignite_mustrun=flags.get("coal_lignite_mustrun"),
        coal_prb_mustrun=flags.get("coal_prb_mustrun"),
        coal_prb_passthrough=float(flags.get("coal_prb_passthrough", 1.0)),
        outage_source=flags.get("outage_source", "historic"),
        coal_prb_passthrough_sigmoid=bool(
            flags.get("coal_prb_passthrough_sigmoid", False)
        ),
        coal_mustrun_per_plant=bool(flags.get("coal_mustrun_per_plant", False)),
        ct_mustrun_per_plant=bool(flags.get("ct_mustrun_per_plant", False)),
        ct_mustrun_floor_frac=float(flags.get("ct_mustrun_floor_frac", 1.0)),
        coal_drop_pof=bool(flags.get("coal_drop_pof", False)),
        coal_prb_passthrough_tiered=bool(
            flags.get("coal_prb_passthrough_tiered", False)
        ),
        prb_overrides=prb_overrides,
        coal_bit_sigmoid=bool(flags.get("coal_bit_passthrough_sigmoid", False)),
        bit_overrides=bit_overrides,
        offer_curve_overrides=flags.get("offer_curve_overrides") or {},
        offer_curve_deltas=deltas,
        curve_smoothing={
            "offer_curve_smoothing_n": sc.get("offer_curve_smoothing_n", 6),
            "offer_curve_smoothing_exp": sc.get("offer_curve_smoothing_exp", 1.0),
            "offer_curve_smoothing_mid": sc.get("offer_curve_smoothing_mid"),
        },
        priced_interchange=bool(flags.get("priced_interchange", False)),
    )
    print(f"done -> {args.out_dir}")


if __name__ == "__main__":
    main()
