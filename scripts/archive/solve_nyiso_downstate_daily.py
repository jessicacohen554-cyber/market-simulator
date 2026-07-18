"""L-11 follow-up: re-ground the NYISO downstate CT offer on DAILY delivered gas.

Replays the nyiso-53 keeper recipe (nyiso-41 keeper meta.json at HEAD + the
PR-#1442 re-derived floors + ``nyiso_li_lcr_tsl`` + ``use_plant_emission_rates_v2``)
but SWAPS the downstate CT-peaker gas grounding from the MONTHLY city-gate
premium adder (``nyiso_downstate_ct_gas_basis``) to the DAILY delivered-gas
re-grounding (``nyiso_downstate_ct_gas_daily``): each downstate CT_PEAKER unit's
gas is SET to the curated ``nyiso-downstate-gas`` daily index (measured Transco
Z6 NY pipeline-hub daily spot + measured monthly LDC premium; free-data memo
§1.4). One mechanism per phenomenon (rule 19) — the monthly adder is turned OFF.

The daily Transco spot captures the cold-snap blowouts (Jan-2024 $23.90/MMBtu) on
the exact days the interruptible peakers run, which the monthly mean smears away
— a strictly more measured, forward-native grounding (rules #11/#13), never a
fitted band.

Two configs, selected by --config:

  * ``daily``     — the candidate / keeper-candidate config.
  * ``daily-abl`` — the D-3 zero-forcing ablation twin (rule 21): the candidate
                    recipe verbatim with every merchant floor/bridge zero-forced.

Usage:
  python scripts/archive/solve_nyiso_downstate_daily.py --config daily     [--years 2023 2024 2025]
  python scripts/archive/solve_nyiso_downstate_daily.py --config daily-abl [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "nyiso41_hubprices"
OUT_BY_CONFIG = {
    "daily": REPO / "results" / "calibration" / "nyiso54_downstate_daily",
    "daily-abl": REPO / "results" / "calibration" / "nyiso54_downstate_daily-ablation",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", choices=list(OUT_BY_CONFIG), required=True)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = args.years or [2023, 2024, 2025]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    out = Path(args.out_dir) if args.out_dir else OUT_BY_CONFIG[args.config]
    kwargs["run_dir"] = out

    overrides = kwargs.setdefault("prb_overrides", {})
    # nyiso-53 recipe base, but the downstate CT gas grounding is DAILY, not
    # monthly (one mechanism per phenomenon, rule 19).
    overrides["nyiso_downstate_ct_gas_basis"] = False
    overrides["nyiso_downstate_ct_gas_daily"] = True
    overrides["nyiso_li_lcr_tsl"] = True
    overrides["use_plant_emission_rates_v2"] = True
    note = (
        "L-11 follow-up: nyiso-53 recipe with the downstate CT-peaker gas "
        "re-grounded on the MEASURED DAILY delivered index "
        "(nyiso_downstate_ct_gas_daily, nyiso-downstate-gas datatype: Transco "
        "Z6 NY daily spot + monthly LDC premium) replacing the monthly premium "
        "adder (nyiso_downstate_ct_gas_basis=False); free-data memo §1.4, "
        "rules #11/#13. Keeps nyiso_li_lcr_tsl + use_plant_emission_rates_v2."
    )
    if args.config == "daily-abl":
        kwargs["zero_forcing_ablation"] = True
        kwargs["ablation_of"] = "nyiso54_downstate_daily"
        note = (
            "D-3 zero-forcing ablation twin (rule 21) of the daily-delivered-gas "
            "candidate: the candidate recipe verbatim with all merchant "
            "floors/bridges zero-forced."
        )
    kwargs["note"] = note

    print(f"solving {out.name} [{args.config}] years {kwargs['years']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
