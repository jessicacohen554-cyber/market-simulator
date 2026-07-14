"""pjm-108 probe driver: the pjm-105 keeper recipe + the CC_LIKE mid-curve belt.

Leg B of the pjm-107/108/109 measured-tail cycle
(docs/handoffs/pjm-107-measured-tail-config-spec-2026-07.md). This replays the
``2026-07-13-pjm-105-symmetric-net`` keeper byte-faithfully (the
``_pjm105_symmetric_net_probe.py`` pattern: pjm-98 meta replay + the G-22 flag
set + symmetric-net virtuals) and applies EXACTLY ONE config override on top:

    ScenarioConfig.pjm_offer_midcurve_segments: ("LONG_RUN",) -> ("LONG_RUN", "CC_LIKE")

The already-live measured mid-curve floor (``pjm_offer_midcurve_conditional``,
P1-only ``mc_bid_adjust`` seam, floor-only, VOLL-capped) extended to the
CC_REGULAR econ rows. Row scoping is already rule-19-clean in code
(``fleet.py:_PJM_MIDCURVE_SEGMENT_OF`` + the ``is_target`` gate): CC **econ**
rows only — CT_FAST stays owned by the startup amortization, committed/must-run
rows by the passthrough/commitment structure, CC **peak** rungs stay
fitted-curve-owned (``is_target`` floors ``peak`` only for LONG_RUN). The
pjm-99 top surface stays retired; nothing stacks. The floor target rides the
measured HH-daily+basis gas-day normalizer (``fleet.py:3231-3236``), so leg B
is event-day-responsive by construction. Zero fitted scalars (rules 1/13/20/21:
the 36-month DataMiner2 submitted-offer corpus, frozen against residuals).

Usage:
    python scripts/probes/_pjm108_cc_belt_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm108_cc_belt] \
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
        default=REPO / "results" / "calibration" / "pjm108_cc_belt",
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
    # --- leg B delta: the ONLY override on top of the pjm-105 replay ----------
    kwargs["pjm_offer_midcurve_segments"] = ("LONG_RUN", "CC_LIKE")
    kwargs["note"] = (
        "PJM 108 probe (leg B): the pjm-105 symmetric-net keeper recipe with "
        "EXACTLY ONE override: pjm_offer_midcurve_segments ('LONG_RUN',) -> "
        "('LONG_RUN','CC_LIKE') — the measured mid-curve floor extended to the "
        "CC_REGULAR econ rows (floor-only, P1-only, VOLL-capped, riding the "
        "measured HH-daily+basis gas-day normalizer). CT_FAST stays "
        "startup-amortization-owned, committed/must-run rows stay "
        "passthrough/commitment-owned, CC peak rungs stay fitted-curve-owned "
        "(rule 19; the pjm-99 top surface stays retired). Zero fitted scalars "
        "in the delta (rules 1/13/20/21: 36-month DataMiner2 submitted-offer "
        "corpus, frozen against residuals)."
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
