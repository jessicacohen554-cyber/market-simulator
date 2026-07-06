"""L-11 full-span probe solves: Zone-K LCR/TSL mechanism + v2 plant CO2 rates.

Replays the nyiso-41 keeper meta.json at HEAD (inheriting HEAD's de-leaked
offer curve and the PR-#1442 re-derived floors on disk — i.e. the nyiso-52
recipe including ``nyiso_downstate_ct_gas_basis=True``) with the lane-L-11
mechanisms:

  * ``nyiso_li_lcr_tsl=True`` (issue #1345): the published Zone-K locality
    import limit caps the NYC->Long_Island link in the HB14-21 window,
    REPLACING the Long_Island 0.45 self-supply energy floor — LI reliability
    energy clears economically, so the rule-20 D-2 forced share for the class
    must FALL, not be re-hidden.
  * ``use_plant_emission_rates_v2=True`` (G-39 ride-along, emissions plan
    §9.6): NYISO's first measured plant-specific CO2 rates in backcast; NYISO
    is RGGI-priced so the flip is dispatch-affecting and rides along with
    this keeper-quality re-solve per the L-8 decision memo.
  * ``nyiso_dynamic_reserve_requirements`` stays OFF — the #1344 channel is
    built but hard-blocked on the Ask-B measured requirement intake
    (docs/handoffs/nyiso-data-asks-2026-07.md).

Two configs, selected by --config (the §9.6 ablation-resolve attribution
split; run both, ≤2 concurrent heavy solves per CLAUDE.md rule 12):

  * ``litsl_v2``    — both mechanisms (the probe / keeper-candidate config).
  * ``litsl_v2off`` — identical but v2 OFF: isolates the v2 flip's own
                      contribution as (litsl_v2 − litsl_v2off).

Usage:
  python scripts/solve_nyiso_litsl_v2.py --config litsl_v2    [--years 2023 2024 2025]
  python scripts/solve_nyiso_litsl_v2.py --config litsl_v2off [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "nyiso41_hubprices"
OUT_BY_CONFIG = {
    "litsl_v2": REPO / "results" / "calibration" / "nyiso53_litsl_v2",
    "litsl_v2off": REPO / "results" / "calibration" / "nyiso53_litsl_v2off",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", choices=list(OUT_BY_CONFIG), required=True)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = args.years or [int(y) for y in meta["years"]]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    out = Path(args.out_dir) if args.out_dir else OUT_BY_CONFIG[args.config]
    kwargs["run_dir"] = out

    overrides = kwargs.setdefault("prb_overrides", {})
    # The nyiso-52 recipe base (PR #1442 recommended config).
    overrides["nyiso_downstate_ct_gas_basis"] = True
    # Issue #1345: Zone-K LCR/TSL import cap replaces the LI 0.45 floor.
    overrides["nyiso_li_lcr_tsl"] = True
    note = (
        "L-11 probe: nyiso-52 recipe + Zone-K LCR/TSL import cap "
        "(nyiso_li_lcr_tsl, issue #1345 — replaces the LI 0.45 self-supply "
        "floor; published locality import limit, HB14-21 window)"
    )
    if args.config == "litsl_v2":
        # G-39 ride-along (emissions plan §9.6): measured plant CO2 rates,
        # dispatch-affecting under NYISO's RGGI price.
        overrides["use_plant_emission_rates_v2"] = True
        note += " + use_plant_emission_rates_v2=True (§9.6 ride-along)."
    else:
        note += (
            " ; v2 OFF (the §9.6 ablation-resolve twin isolating the v2 "
            "flip's contribution)."
        )
    kwargs["note"] = note

    print(f"solving {out.name} [{args.config}] years {kwargs['years']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
