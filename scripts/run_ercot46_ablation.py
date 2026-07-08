"""Solve the zero-forcing ablation twin of the ercot46 clock+steamgas keeper-candidate.

Rule 21 (CLAUDE.md): every keeper carries a DOF ledger and an ablation twin.
Reuses ``replay_keeper.build_kwargs`` to reconstruct the ercot46 recipe from its
``meta.json``, then solves with ``zero_forcing_ablation=True`` (every merchant
floor/bridge neutralized via ``ScenarioConfig.as_zero_forcing_ablation`` —
D-3, ``floor_mechanisms.MECH_ABLATION_FIELDS``), recording ``ablation_of`` so
the bundle is traceable to its base keeper-candidate.

Usage:
    python scripts/run_ercot46_ablation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import run_calibration_full as rcf  # noqa: E402
from replay_keeper import build_kwargs  # noqa: E402

BASE = REPO / "results" / "calibration" / "ercot46_clock_steamgas"
OUT = REPO / "results" / "calibration" / "ercot46_clock_steamgas_ablation"


def main() -> None:
    meta = json.loads((BASE / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = OUT
    kwargs["zero_forcing_ablation"] = True
    kwargs["ablation_of"] = "ercot46_clock_steamgas"
    kwargs["note"] = (
        "ercot46 zero-forcing ablation twin (rule 21): every merchant "
        "floor/bridge neutralized (reliability_floor, ct_netload_drag, "
        "gas_st_netload_drag, ra_mustoffer_bridge, ...) via "
        "ScenarioConfig.as_zero_forcing_ablation, on the identical "
        "clock-corrected data + ST_GAS startup-cost commitment physics as "
        "the ercot46 base. Quantifies what the floors buy vs the base keeper."
    )

    print(f"solving ablation twin of {BASE.name} ({meta['iso']} {meta['years']}) ...")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
