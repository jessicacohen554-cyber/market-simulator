"""pjm-109 probe driver: the composite measured-tail keeper candidate.

The composite of legs A and B of the pjm-107/108/109 measured-tail cycle
(docs/handoffs/pjm-107-measured-tail-config-spec-2026-07.md), solved ONLY when
both legs individually clear their pre-committed gates. This replays the
``2026-07-13-pjm-105-symmetric-net`` keeper byte-faithfully (the
``_pjm105_symmetric_net_probe.py`` pattern) and applies BOTH deltas on top:

    ScenarioConfig.gas_daily_shape: False -> True            (leg A)
    ScenarioConfig.pjm_offer_midcurve_segments:
        ("LONG_RUN",) -> ("LONG_RUN", "CC_LIKE")             (leg B)

Both are existing, gated, default-off measured mechanisms; zero fitted scalars
(rules 1/13/20/21). The measured HH daily gas shape (mean-preserving; solved on
the G-A1-fixed gas_daily_shape_factors that renormalizes the calendar-day
factors to mean exactly 1.0, so the monthly delivered mean is preserved to
<$0.001/MMBtu) plus the measured CC_REGULAR econ-row mid-curve floor. Register
the zero-forcing ablation twin alongside (rule 21, ``--zero-forcing-ablation``).

Usage:
    python scripts/probes/_pjm109_measured_tail_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm109_measured_tail] \
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
        default=REPO / "results" / "calibration" / "pjm109_measured_tail",
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
    # --- composite deltas: BOTH legs on top of the pjm-105 replay -------------
    kwargs["pjm_offer_midcurve_segments"] = ("LONG_RUN", "CC_LIKE")  # leg B
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"]["gas_daily_shape"] = True  # leg A
    kwargs["note"] = (
        "PJM 109 probe (composite measured-tail keeper candidate): the pjm-105 "
        "symmetric-net keeper recipe with BOTH measured-tail overrides — "
        "gas_daily_shape False->True (leg A: measured HH daily within-month "
        "shape, mean-preserving, F923 re-carried) AND "
        "pjm_offer_midcurve_segments ('LONG_RUN',)->('LONG_RUN','CC_LIKE') "
        "(leg B: measured mid-curve floor extended to CC_REGULAR econ rows). "
        "Both existing gated default-off measured mechanisms; zero fitted "
        "scalars in the delta (rules 1/13/20/21). Solved only after both legs "
        "cleared their pre-committed gates (spec Sec 2)."
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
