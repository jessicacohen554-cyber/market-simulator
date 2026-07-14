"""pjm-107 probe driver: the pjm-105 keeper recipe + the measured gas DAILY shape.

Leg A of the pjm-107/108/109 measured-tail cycle
(docs/handoffs/pjm-107-measured-tail-config-spec-2026-07.md). This replays the
``2026-07-13-pjm-105-symmetric-net`` keeper byte-faithfully (the
``_pjm105_symmetric_net_probe.py`` pattern: pjm-98 meta replay + the G-22 flag
set + symmetric-net virtuals) and applies EXACTLY ONE config override on top:

    ScenarioConfig.gas_daily_shape: False -> True

The measured Henry Hub *daily* within-month shape (``fuel.gas_daily_shape_factors``,
mean-preserving per month), including the re-carry onto every F923-overwritten
gas plant-month (``fuel.py:3803-3817``) so plant-level monthly pricing keeps the
daily swing. This cycle's G-A1 pre-check caught that the shared HH factors were
NOT exactly mean-preserving (bare np.interp resampling overshot the mean in
gas-spike months — Jan-2024 +$0.10/MMBtu pre-fix); the owner-authorized fix
renormalizes the calendar-day factors to mean exactly 1.0 (matching the per-hub
daily variants), so the monthly delivered mean is now preserved to numerical
noise (verified <$0.001/MMBtu). The fix also changes the CAISO/MISO/NEISO/NYISO
keepers built on the old behavior — owner re-run prompts accompany this cycle.
The override rides the generic ``prb_overrides`` ScenarioConfig channel
(``gas_daily_shape`` has no dedicated solve_and_persist kwarg); run_year's
backcast_config and the run_config recorder both apply it via ``with_overrides``,
so scenario_config records exactly what the LP solves with. Zero fitted scalars
(rules 1/13/20/21: the daily HH prints are ex-ante measured, frozen against
residuals; the mechanism is forecast-native — a forward monthly level times a
representative daily shape).

Usage:
    python scripts/probes/_pjm107_gas_daily_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm107_gas_daily] \
        [--years 2023 2024 2025] [--zero-forcing-ablation]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle",
        type=Path,
        default=REPO / "results" / "calibration" / "pjm98_cc_mustrun",
        help="base keeper bundle whose meta.json supplies the recipe",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=REPO / "results" / "calibration" / "pjm107_gas_daily",
    )
    ap.add_argument("--years", nargs="*", type=int, default=None)
    ap.add_argument(
        "--zero-forcing-ablation",
        action="store_true",
        help="solve the D-3 zero-forcing ablation twin instead (rule 21); "
        "pairs the twin to the probe via ablation_of",
    )
    args = ap.parse_args()

    meta = json.loads((args.bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in (args.years or meta["years"])]
    kwargs["hours"] = int(meta.get("hours", 8760))
    rcf.enforce_holdout_year_gate(kwargs["years"], kwargs["iso"], False)
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = args.out_dir
    # --- pjm-105 keeper recipe (the symmetric-net G-22 stack), byte-faithful ---
    kwargs["pjm_da_virtual_bids"] = True
    kwargs["tranche_startup_amortization"] = True
    kwargs["tranche_startup_measured_runs"] = True
    kwargs["tranche_startup_conditional_runs"] = True
    kwargs["pjm_offer_midcurve_conditional"] = True
    kwargs["pjm_offer_midcurve_segments"] = ("LONG_RUN",)
    # --- leg A delta: the ONLY override on top of the pjm-105 replay ----------
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"]["gas_daily_shape"] = True
    kwargs["note"] = (
        "PJM 107 probe (leg A): the pjm-105 symmetric-net keeper recipe "
        "(pjm-98 keeper recipe + net DA virtual depth [symmetric form] + CT "
        "fast-start startup amortization on CAMPD-measured run horizons + the "
        "measured LONG_RUN top-of-curve floor) with EXACTLY ONE override: "
        "gas_daily_shape False->True — the measured Henry Hub daily "
        "within-month shape injected onto the gas price series, mean-preserving "
        "per month (the F923 plant-month re-carry keeps the daily swing on every "
        "overwritten gas plant-month). Solved on the G-A1-fixed "
        "gas_daily_shape_factors: the calendar-day factors are renormalized to "
        "mean exactly 1.0, so the monthly delivered mean is preserved to <$0.001/"
        "MMBtu (bare np.interp overshot by +$0.10/MMBtu in Jan-2024 pre-fix). "
        "Zero fitted scalars in the delta (rules 1/13/20/21: ex-ante measured "
        "daily HH prints, frozen against residuals; forecast-native)."
    )
    if args.zero_forcing_ablation:
        kwargs["zero_forcing_ablation"] = True
        kwargs["ablation_of"] = args.out_dir.name
        kwargs["run_dir"] = args.out_dir.with_name(f"{args.out_dir.name}-ablation")

    print(f"solving {kwargs['iso']} {kwargs['years']} -> {kwargs['run_dir']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
