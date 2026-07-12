"""pjm-102 probe driver: pjm-98 keeper recipe + the NET DA virtual-bid layer.

The keeper-path fix for the pjm-101 INC phantom-supply defect
(docs/FINDING-pjm-da-depth-midcurve-2026-07.md §5). Replay the pjm-98
keeper's ``meta.json`` recipe byte-faithfully (``replay_keeper.build_kwargs``)
with the DA virtual-bid layer rebuilt to a SINGLE per-hour NET virtual-demand
curve (``Σ DEC≥λ − Σ INC≤λ``, rendered entirely as DEC-form withdrawal
blocks; ``src/market_sim/data/virtual_bids.py``). Unlike pjm-100/101, no INC
MW enters the LP as physical supply, so the DA-depth price effect is preserved
while real peaker dispatch is no longer displaced (C1 CT_PEAKER recovers).

Solved as the combination the price-formation halves require
(``--with-offer-surface --with-midcurve`` on by default here): the measured
mid-curve floor (A′, ``pjm_offer_midcurve_conditional``) prices the econ body
and the frozen pjm-99 top-of-curve surface (``pjm_offer_surface_conditional``)
prices the CC/CT peak rungs the deepened margin now reaches (rule 19: disjoint
row ownership).

Usage:
    python scripts/probes/_pjm102_net_virtual_bids_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm102_net_virtual_bids] \
        [--years 2023 2024 2025] [--no-offer-surface] [--no-midcurve] \
        [--zero-forcing-ablation]
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
        default=REPO / "results" / "calibration" / "pjm102_net_virtual_bids",
    )
    ap.add_argument("--years", nargs="*", type=int, default=None)
    ap.add_argument(
        "--no-offer-surface",
        action="store_true",
        help="disable the frozen pjm-99 top-of-curve offer surface (on by default)",
    )
    ap.add_argument(
        "--no-midcurve",
        action="store_true",
        help="disable the measured mid-curve offer floor (on by default)",
    )
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
    kwargs["pjm_da_virtual_bids"] = True
    note = (
        "PJM 102 probe: pjm-98 keeper recipe (byte-faithful replay off its "
        "meta.json) + pjm_da_virtual_bids=True in the NET DA-virtual-demand "
        "form (the keeper-path fix for the pjm-101 INC phantom-supply defect, "
        "docs/FINDING-pjm-da-depth-midcurve-2026-07.md §5). The measured "
        "hourly SUBMITTED INC/DEC curves (DataMiner2 hrl_da_incs_decs) enter "
        "as a SINGLE per-hour net-demand curve net(λ)=Σ DEC≥λ − Σ INC≤λ, "
        "rendered ENTIRELY as DEC-form withdrawal blocks (net-negative tail "
        "clamped to zero). No INC MW is injected as physical supply, so the "
        "DA-depth price effect is preserved while real peaker dispatch is no "
        "longer displaced. ENDOGENOUS clearing; zero fitted scalars in the "
        "delta (rules 13/20/21: submitted ex-ante inputs, cleared volumes and "
        "prices stay LP outputs)."
    )
    if not args.no_offer_surface:
        kwargs["pjm_offer_surface_conditional"] = True
        note += (
            " PLUS the frozen pjm-99 measured top-of-curve offer surface "
            "(pjm_offer_surface_conditional=True) — prices the CC/CT peak "
            "rungs the deepened DA margin now reaches."
        )
    if not args.no_midcurve:
        kwargs["pjm_offer_midcurve_conditional"] = True
        note += (
            " PLUS the measured MID-CURVE offer floor "
            "(pjm_offer_midcurve_conditional=True, G-22 lever A') — the "
            "price-forming level of the econ body (rule 19: disjoint row "
            "ownership from the top surface)."
        )
    kwargs["note"] = note
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
