"""pjm-105 probe driver: pjm-104 recipe on the SYMMETRIC net DA-virtual form.

The pjm-104 determination (docs/FINDING-pjm-midmerit-level-2026-07.md §5b):
the mid-merit offer LEVEL is exhausted — every mid-merit class sits on a
measured/cited offer basis and cleared virtual demand is within ~1 TWh/yr of
the actual-DA-price equilibrium — yet C1 2024 CC_REGULAR misses at +9.07 TWh
because the committed net-DEC form CLAMPS the net-negative (INC-dominated)
tail to zero: +10.3/+14.8/+17.2 TWh/yr of one-sided phantom demand clears at
actual DA prices while the real annual net position is ≈ 0 (−0.6/−0.9/+1.3
TWh). Three probes proved the phantom re-routes to whichever class is left
cheapest (CT+coal → coal → CC); no measured offer level can absorb it.

OWNER DECISION (2026-07-13): the clamped form is NOT keeper-eligible — it
was diagnostic scaffolding, and its diagnostic work is done. This probe runs
the identical pjm-104 recipe on the replacement SYMMETRIC net form
(``data.virtual_bids``, pjm-105): the whole measured per-hour
``net(λ) = Σ DEC≥λ − Σ INC≤λ`` curve rendered as DEC-form withdrawal rungs
(``net > 0``) PLUS INC-form net-supply rungs (``net < 0``), endogenous
clearing on both sides — the LP finds the crossing. The supply side is
bounded by the measured NET position (≈ 0 annual), enters at measured
submitted prices, and displaces off-peak generation exactly where the real
DA market scheduled less physical generation than RT load (rule 13; the
module docstring documents why this is not the condemned pjm-101 gross-INC
construction).

Delta vs pjm-104: NONE in the flag set — the symmetric form replaces the
clamp inside ``pjm_da_virtual_bids`` itself. Zero fitted scalars (rules
1/13/20/21).

Usage:
    python scripts/probes/_pjm105_symmetric_net_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm105_symmetric_net] \
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
        default=REPO / "results" / "calibration" / "pjm105_symmetric_net",
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
    kwargs["pjm_da_virtual_bids"] = True
    kwargs["tranche_startup_amortization"] = True
    kwargs["tranche_startup_measured_runs"] = True
    kwargs["tranche_startup_conditional_runs"] = True
    kwargs["pjm_offer_midcurve_conditional"] = True
    kwargs["pjm_offer_midcurve_segments"] = ("LONG_RUN",)
    kwargs["note"] = (
        "PJM 105 probe: the pjm-104 recipe (pjm-98 keeper recipe + net DA "
        "virtual depth + CT fast-start startup amortization v3/v4 on "
        "CAMPD-measured run horizons + the measured LONG_RUN top-of-curve "
        "floor) with the DA-virtual layer in its SYMMETRIC net form "
        "(pjm-105): the whole measured per-hour net(λ) = Σ DEC≥λ − Σ INC≤λ "
        "curve rendered as DEC-form withdrawal rungs (net>0) plus INC-form "
        "net-supply rungs (net<0), endogenous clearing on both sides — "
        "replacing the one-sided clamp whose +10-17 TWh/yr phantom demand "
        "was the adjudicated C1 blocker (owner decision 2026-07-13: the "
        "clamp was diagnostic scaffolding, not keeper-eligible). The supply "
        "side is bounded by the measured NET position (≈0 annual at actual "
        "DA prices), enters at measured submitted offer prices, and is not "
        "the condemned pjm-101 gross-INC construction. Zero fitted scalars "
        "in the delta (rules 1/13/20/21: submitted ex-ante measured curves, "
        "frozen against residuals)."
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
