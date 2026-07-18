"""pjm-100 probe driver: pjm-98 keeper recipe + the DA virtual-bid layer.

Single-delta A/B off the pjm-98 keeper (G-22 lever B,
docs/FINDING-pjm-offer-surface-noop-2026-07.md §Re-scoped levers): replay
the keeper's ``meta.json`` recipe byte-faithfully
(``replay_keeper.build_kwargs`` — the only sanctioned recipe
reconstruction) with exactly ONE change, ``pjm_da_virtual_bids=True`` (the
measured hourly SUBMITTED INC/DEC virtual bid curves posted into the LP as
pseudo-units with endogenous clearing;
``src/market_sim/data/virtual_bids.py``).

``--with-offer-surface`` additionally re-arms the frozen pjm-99 measured
top-of-curve offer surface (``pjm_offer_surface_conditional=True``) — the
combination test the pjm-99 finding prescribes: the top-of-curve wall was
byte-identical-inert because demand never reached it; once the DA depth
pushes the margin deeper, the wall may bind (re-test in combination, never
as a stacked fit).

Usage:
    python scripts/probes/_pjm100_da_virtual_bids_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm100_da_virtual_bids] \
        [--years 2023 2024 2025] [--with-offer-surface] \
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
        default=REPO / "results" / "calibration" / "pjm100_da_virtual_bids",
    )
    ap.add_argument("--years", nargs="*", type=int, default=None)
    ap.add_argument(
        "--with-offer-surface",
        action="store_true",
        help="also arm the frozen pjm-99 measured top-of-curve offer surface "
        "(combination re-test: the wall can only bind once the DA depth "
        "reaches it)",
    )
    ap.add_argument(
        "--with-midcurve",
        action="store_true",
        help="also arm the measured MID-CURVE offer floor (G-22 lever A', "
        "pjm_offer_midcurve_conditional) — the depth sweep showed the "
        "too-cheap econ body caps the dual, so depth (B) and the mid-curve "
        "level (A') are complementary halves of one price-formation fix",
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
        "PJM 100 probe: pjm-98 keeper recipe (byte-faithful replay off its "
        "meta.json) + pjm_da_virtual_bids=True — the G-22 lever-B DA "
        "procurement depth: measured hourly SUBMITTED INC/DEC virtual bid "
        "curves (DataMiner2 hrl_da_incs_decs) as LP pseudo-units with "
        "ENDOGENOUS clearing (src/market_sim/data/virtual_bids.py). Zero "
        "fitted scalars in the delta (rules 13/20/21: submitted ex-ante "
        "inputs, cleared volumes and prices stay LP outputs)."
    )
    if args.with_offer_surface:
        kwargs["pjm_offer_surface_conditional"] = True
        note += (
            " PLUS the frozen pjm-99 measured top-of-curve offer surface "
            "(pjm_offer_surface_conditional=True) — the prescribed "
            "combination re-test: the wall binds only once the DA depth "
            "reaches it."
        )
    if args.with_midcurve:
        kwargs["pjm_offer_midcurve_conditional"] = True
        note += (
            " PLUS the measured MID-CURVE offer floor "
            "(pjm_offer_midcurve_conditional=True, G-22 lever A': "
            "scripts/data/derive_pjm_offer_midcurve.py) — the depth sweep showed "
            "+10 GW of depth buys only +$2-4/MWh on the model's too-cheap "
            "econ body, so the measured mid-curve level is the "
            "price-forming half of the fix."
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
