"""Driver: D-3 zero-forcing ablation twin of the nyiso-56 keeper (rule 21).

Identical to :mod:`run_nyiso53_ablation_twin` (the nyiso-53 recipe VERBATIM with
``zero_forcing_ablation=True``) — the only difference is that nyiso-56 dispatches
on the **measured** per-zone hourly load shapes (``load_zonal_shares`` raw
fallback, G-20c) rather than the static Gold-Book shares. That is a code-level
data-source change, not a config flag, so this twin is byte-for-byte the nyiso-53
ablation recipe re-solved at HEAD; it writes to its own bundle and records
``ablation_of = "nyiso56_measuredshares"`` so it links to the nyiso-56 keeper.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

KEEPER_META = REPO / "results" / "calibration" / "nyiso41_hubprices" / "meta.json"
OUT = REPO / "results" / "calibration" / "nyiso56_measuredshares-ablation"


def main() -> None:
    meta = json.loads(KEEPER_META.read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [2023, 2024, 2025]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = OUT
    overrides = kwargs.setdefault("prb_overrides", {})
    overrides["nyiso_downstate_ct_gas_basis"] = True
    overrides["nyiso_li_lcr_tsl"] = True
    overrides["use_plant_emission_rates_v2"] = True
    kwargs["zero_forcing_ablation"] = True
    kwargs["ablation_of"] = "nyiso56_measuredshares"
    kwargs["note"] = (
        "D-3 zero-forcing ablation twin of 2026-07-07-nyiso-56-measured-zonal "
        "(rule 21): the nyiso-56 recipe verbatim (measured per-zone load shares, "
        "G-20c) with all merchant floors/bridges zero-forced."
    )
    print(f"solving {OUT.name} years {kwargs['years']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
