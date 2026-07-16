"""pjm-cong-1 probe driver: the pjm-113 keeper recipe + the measured EAST cut.

Replays the pjm-113 keeper (`2026-07-16-pjm-113-short-only`) via
replay_keeper.build_kwargs and applies EXACTLY ONE flag on top (via
prb_overrides):

    ScenarioConfig.pjm_east_interface_cut : False -> True

— the measured joint EMAAC-import cut: one one-sided hourly interface-group
row capping Flow(Central_PA->EMAAC) + Flow(SWMAAC->EMAAC) at the published
"Average Eastern" limit (PJM's Manual-03 EASTERN reactive transfer
interface, the real EMAAC import cut). Zero fitted scalars; the cap is the
measured series verbatim. The solve also carries the (unconditional,
primary-source-cited) 5004/5005 crosswalk correction on this code base —
the mis-attributed ComEd->AEP_Ohio entries removed from
constants.PJM_INTERFACE_LINK_MAP / PJM_MEASURED_INTERNAL_TTC.

Gate: docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §10.6, pre-committed
before any solve. docs probe: scripts/probes/_pjm_c3c_congestion_surface_
decomp.py (§10.4 MATERIAL adjudication, 13/22 tail hours, median +485 MW).

Usage:
    python scripts/probes/_pjmcong1_east_cut_probe.py \
        [--bundle results/calibration/pjm113_short_only] \
        [--out-dir results/calibration/pjmcong1_east_cut] \
        [--years 2023 2024 2025]
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
        default=REPO / "results" / "calibration" / "pjm113_short_only",
        help="base keeper bundle whose meta.json supplies the recipe",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=REPO / "results" / "calibration" / "pjmcong1_east_cut",
    )
    ap.add_argument("--years", nargs="*", type=int, default=None)
    args = ap.parse_args()

    meta = json.loads((args.bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in (args.years or meta["years"])]
    kwargs["hours"] = int(meta.get("hours", 8760))
    rcf.enforce_holdout_year_gate(kwargs["years"], kwargs["iso"], False)
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = args.out_dir
    # --- pjm-cong-1 delta: the measured EAST interface cut, nothing else. ---
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"]["pjm_east_interface_cut"] = True
    kwargs["note"] = (
        "PJM cong-1: the pjm-113 keeper recipe with EXACTLY the measured EAST "
        "interface cut armed — pjm_east_interface_cut (one one-sided hourly "
        "aggregate group capping the joint Central_PA->EMAAC + SWMAAC->EMAAC "
        "flow at PJM's published Average Eastern reactive-interface limit; "
        "Manual 03 §3.8 identity verified, diagnosis §10.3), on the corrected "
        "5004/5005 crosswalk (the mis-attributed ComEd->AEP entries removed — "
        "primary-source data-integrity fix). Zero fitted scalars; no constant "
        "touched. Gate pre-committed in diagnosis §10.6 before any solve."
    )

    print(f"solving {kwargs['iso']} {kwargs['years']} -> {kwargs['run_dir']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
