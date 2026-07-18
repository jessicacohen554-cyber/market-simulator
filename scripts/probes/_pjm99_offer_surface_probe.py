"""pjm-99 probe driver: pjm-98 keeper recipe + the measured PJM offer surface.

Single-delta A/B off the pjm-98 keeper (G-22 lever A,
docs/handoffs/pjm-summer-peak-price-formation-g22-2026-07.md §5): replay the
keeper's ``meta.json`` recipe byte-faithfully (``replay_keeper.build_kwargs``
— the only sanctioned recipe reconstruction) with exactly ONE change,
``pjm_offer_surface_conditional=True`` (the measured condition-binned
top-of-curve offer surface posted onto the CC_REGULAR + CT_PEAKER peak-band
rungs, P1-only; ``scripts/data/derive_pjm_offer_surface.py``).

The flag is threaded through ``solve_and_persist`` (not the generic
``prb_overrides`` ScenarioConfig channel) because ``backcast_config`` must
also perform the structural no-op peak-ladder split — a ``--set`` override
lands after that seam and would collapse the measured ladder onto a single
flat rung.

Usage:
    python scripts/probes/_pjm99_offer_surface_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm99_offer_surface] \
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
        default=REPO / "results" / "calibration" / "pjm99_offer_surface",
    )
    ap.add_argument("--years", nargs="*", type=int, default=None)
    ap.add_argument(
        "--zero-forcing-ablation",
        action="store_true",
        help="solve the D-3 zero-forcing ablation twin of the probe instead "
        "(rule 21); pairs the twin to the probe via ablation_of",
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
    kwargs["pjm_offer_surface_conditional"] = True
    kwargs["note"] = (
        "PJM 99 probe: pjm-98 keeper recipe (byte-faithful replay off its "
        "meta.json) + pjm_offer_surface_conditional=True — the G-22 lever-A "
        "measured PJM energy-offer surface (DataMiner2 energy_market_offers "
        "top-of-curve distribution, condition-binned by within-year net-load "
        "percentile) posted onto the CC_REGULAR + CT_PEAKER peak-band rungs, "
        "P1-only. Zero fitted scalars in the delta "
        "(scripts/data/derive_pjm_offer_surface.py; rules 13/20/21)."
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
