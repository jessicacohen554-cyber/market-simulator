"""Driver: D-3 zero-forcing ablation twin of the nyiso-53 keeper (rule 21).

The nyiso-53 recipe (``solve_nyiso_litsl_v2.py --config litsl_v2``) VERBATIM —
nyiso-41 keeper meta replayed at HEAD + ``nyiso_downstate_ct_gas_basis`` +
``nyiso_li_lcr_tsl`` + ``use_plant_emission_rates_v2`` — solved with
``zero_forcing_ablation=True``: every merchant floor/bridge neutralized via
``ScenarioConfig.as_zero_forcing_ablation`` (off-list from the D-2 mechanism
registry), keeping only the structural protected set (nuclear must-run, CHP
steam, coal take-or-pay). The keeper-vs-twin per-class delta quantifies what
each remaining floor buys (post-#1345 that is the PR-#1442 windowed
temperature ramps — the selfsupply channel is already deleted from the keeper
config itself). No parameter differs from the keeper config.

Distinct from ``nyiso53_litsl_v2off`` (the §9.6 v2 ATTRIBUTION twin, which
isolates the v2 rate flip and satisfies nothing under rule 21).
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
OUT = REPO / "results" / "calibration" / "nyiso53_litsl_v2-ablation"


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
    kwargs["ablation_of"] = "nyiso53_litsl_v2"
    kwargs["note"] = (
        "D-3 zero-forcing ablation twin of 2026-07-06-nyiso-53-li-tsl "
        "(rule 21): the keeper recipe verbatim with all merchant "
        "floors/bridges zero-forced."
    )
    print(f"solving {OUT.name} years {kwargs['years']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
