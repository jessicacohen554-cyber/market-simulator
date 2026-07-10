"""Driver: PJM 97 — pjm-96 recipe + measured internal interface limits (G-20 Phase-2).

pjm-94 keeper recipe (byte-faithful via ``replay_keeper.build_kwargs``, exactly
as ``run_pjm96_seam_ladder.py`` reads it) + the pjm-96 seam ladder, plus this
session's deltas:

* ``pjm_measured_interface_limits=True`` — the internal links whose static
  ``ttc_mw`` was seeded from the PJM Data Miner 2 transfer-limit postings
  follow the measured HOURLY series (transfer-interface-limits clean
  datatype, ``constants.PJM_INTERFACE_LINK_MAP``; min(pre, post) where both
  publish; forward direction only). Supersedes ``pjm_congestion``'s pooled
  medians on mapped links (same feed, hourly — rule 19).
* ``pjm_reserve_pergen=True`` + ``measured_ramp_capability=True`` — carried
  as retained structure per the pjm-81 owner recommendation (calibration-log
  2026-07-06: real market design, fit-neutral, memory-proven at the MISO
  class tier with the 10 GB swapfile convention).

Owner decision 2026-07-10: promoted to PJM keeper (rule 1 — most structurally
faithful; both transmission channels measured with zero fitted scalars).
``--ablation`` solves the D-3 zero-forcing ablation twin of the same recipe
(rule 21; lands in ``<run_dir>-ablation`` and records ``ablation_of``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
from run_calibration_full import _load_reference, report_run, solve_and_persist  # noqa: E402

PJM94_BUNDLE = REPO / "results" / "calibration" / "pjm94_stgas_netload_drag"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--ablation",
        action="store_true",
        help="solve the D-3 zero-forcing ablation twin (rule 21; lands in "
        "<run_dir>-ablation with ablation_of recorded)",
    )
    args = ap.parse_args()

    meta = json.loads((PJM94_BUNDLE / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)

    kwargs["pjm_seam_measured_ladder"] = True
    kwargs["pjm_measured_interface_limits"] = True
    kwargs["pjm_reserve_pergen"] = True
    kwargs["measured_ramp_capability"] = True
    kwargs["zero_forcing_ablation"] = bool(args.ablation)
    kwargs["run_dir"] = REPO / "results" / "calibration" / "pjm97_measured_interfaces"
    kwargs["note"] = (
        "PJM 97: pjm-96 recipe (pjm-94 keeper via replay_keeper.build_kwargs + "
        "pjm_seam_measured_ladder) + pjm_measured_interface_limits=True (the "
        "measured hourly Data Miner 2 internal interface limits replace the "
        "static ttc_mw / pjm_congestion medians on the seven mapped links, "
        "forward direction; transfer-interface-limits clean datatype, rule "
        "13/14 measured-physical input) + pjm_reserve_pergen + "
        "measured_ramp_capability carried per the pjm-81 owner recommendation. "
        "G-20 Phase-2 internal-interface arm; owner-directed keeper promotion "
        "2026-07-10 (rule 1). "
        + ("ZERO-FORCING ABLATION TWIN (rule 21/D-3)." if args.ablation else "")
    )

    reference = _load_reference()
    kwargs["reference"] = reference
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["hours"] = int(meta.get("hours", 8760))

    print(
        "=== pjm-97 solve kwargs (deltas vs pjm-96: pjm_measured_interface_limits, "
        f"pjm_reserve_pergen, measured_ramp_capability; ablation={args.ablation}) ==="
    )
    print(f"years={kwargs['years']} iso={kwargs['iso']} hours={kwargs['hours']}")
    print(f"out_dir={kwargs['run_dir']}")

    run_dir = solve_and_persist(**kwargs)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
