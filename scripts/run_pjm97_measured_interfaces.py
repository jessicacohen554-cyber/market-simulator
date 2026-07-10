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

Hypothesis to score (task brief): Dominion/EMAAC/SWMAAC CC+CT recover toward
actuals (C1), CT per-plant capture rises, and the nested MAD reserve family
starts binding in the 2025 heat-wave hours so the C3c tail prices via in-LP
reserve duals — the NYISO G-20c pattern, no derate, no fitted parameters.

Diffed against pjm-96 (seam-only arm): the interface-limit effect is the
attributable delta; pergen+ramp were shown dispatch-neutral standalone
(pjm-81), so any interaction shows up as reserve duals, not volume moves.
"""

from __future__ import annotations

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
    meta = json.loads((PJM94_BUNDLE / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)

    kwargs["pjm_seam_measured_ladder"] = True
    kwargs["pjm_measured_interface_limits"] = True
    kwargs["pjm_reserve_pergen"] = True
    kwargs["measured_ramp_capability"] = True
    kwargs["run_dir"] = REPO / "results" / "calibration" / "pjm97_measured_interfaces"
    kwargs["note"] = (
        "PJM 97: pjm-96 recipe (pjm-94 keeper via replay_keeper.build_kwargs + "
        "pjm_seam_measured_ladder) + pjm_measured_interface_limits=True (the "
        "measured hourly Data Miner 2 internal interface limits replace the "
        "static ttc_mw / pjm_congestion medians on the seven mapped links, "
        "forward direction; transfer-interface-limits clean datatype, rule "
        "13/14 measured-physical input) + pjm_reserve_pergen + "
        "measured_ramp_capability carried per the pjm-81 owner recommendation. "
        "G-20 Phase-2: targets the eastern phantom-supply channel (b) — "
        "Dominion CC -78/-42/-11%, Dominion CT -90/-86/-72%, EMAAC CT -80%, "
        "SWMAAC CC -46/-88% vs actual in pjm-94 — and the C3b/C3c scarcity "
        "structure (model never tight: ~10x requirement as free online "
        "headroom vs PJM's real ~3 GW posture, pjm-81)."
    )

    reference = _load_reference()
    kwargs["reference"] = reference
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["hours"] = int(meta.get("hours", 8760))

    print(
        "=== pjm-97 solve kwargs (deltas vs pjm-96: pjm_measured_interface_limits, "
        "pjm_reserve_pergen, measured_ramp_capability) ==="
    )
    print(f"years={kwargs['years']} iso={kwargs['iso']} hours={kwargs['hours']}")
    print(f"out_dir={kwargs['run_dir']}")

    run_dir = solve_and_persist(**kwargs)
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
