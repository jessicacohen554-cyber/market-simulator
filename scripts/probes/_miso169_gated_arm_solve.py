"""Solve the miso-169 ARM: the keeper recipe + miso_reserve_online_gated=True.

The PREREG-miso167 §5 arm invocation, built the same way the §5 control was
run: the keeper bundle's ``meta.json`` through ``replay_keeper.build_kwargs``
(the sanctioned recipe channel — byte-identical solve kwargs to the control),
with EXACTLY ONE delta: ``miso_reserve_online_gated=True``. Years 2023-2025
sequential in one invocation (rules 12/16); cross-year warm-start pinned OFF
exactly as ``replay_keeper`` pins it, so the arm's solve path matches the
control's. A NEW run (fresh timestamp/run id), never a keeper repair — the
``replay_keeper`` display-date restoration is deliberately not used.

Usage:
    python scripts/probes/_miso169_gated_arm_solve.py \
        results/calibration/miso160_wefor_B --out-dir results/calibration/miso169_gated_B
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# Same reproducibility pin as replay_keeper (basis-independence of the A/B).
os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"

from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration_full as rcf  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bundle", help="the KEEPER bundle carrying the recipe meta.json")
    ap.add_argument("--out-dir", required=True, help="the arm's output bundle dir")
    args = ap.parse_args()

    meta = json.loads((Path(args.bundle) / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["run_dir"] = Path(args.out_dir)
    # THE single delta vs the zero-delta control (PREREG-miso167 §2/§5).
    kwargs["miso_reserve_online_gated"] = True
    kwargs["note"] = (
        "miso-169 ARM: miso_reserve_online_gated=True — THE SINGLE DELTA vs "
        "the same-recipe zero-delta control miso169_gated_A (PREREG-miso167 "
        "§2/§5, executed per the miso-168 corrected order). Reg+Spin split "
        "into an online-gated product (coupling row, measured CAMPD rho via "
        "data.online_reserve_rho — NOTE the RHO_CLIP 0.5 floor binds over "
        "the measured 0.1764, the standing nyiso-144 owner escalation) and "
        "an ungated Supplemental product; nested measured Reg+Spin family "
        "priced on the published Schedule-28 $65/$98 two-step curve."
    )
    print(
        f"ARM solve: {kwargs.get('iso')} years {kwargs.get('years')} -> "
        f"{args.out_dir} with miso_reserve_online_gated=True"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"wrote arm bundle to {run_dir}")


if __name__ == "__main__":
    main()
