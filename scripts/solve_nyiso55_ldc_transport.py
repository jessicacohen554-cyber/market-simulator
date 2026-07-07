"""G-13: re-ground the NYISO downstate CT offer on per-zone LDC transport gas.

Replays the nyiso-53 keeper recipe (nyiso-41 keeper meta.json at HEAD + the
PR-#1442 re-derived floors + ``nyiso_li_lcr_tsl`` + ``use_plant_emission_rates_v2``)
with the downstate CT-peaker gas re-grounded on the measured DAILY delivered
index (``nyiso_downstate_ct_gas_daily``). This is the nyiso-54 config verbatim —
the only change is the underlying ``nyiso-downstate-gas`` datatype, now schema v2:
each downstate CT_PEAKER unit's gas is SET to its **zone's** delivered index =
measured Transco Z6 NY pipeline-hub daily spot (the peaker's own commodity) +
measured monthly **LDC non-firm transportation delivery rate** (KEDNY SC-22 for
NYC, KEDLI SC-19 for Long Island; National Grid ``statnfdr`` statements).

This supersedes nyiso-54's statewide EIA-N3050NY3 firm-citygate premium with the
correct rate class (the interruptible peakers are transportation customers who
buy their own commodity and pay the LDC a non-firm transport charge) at the
correct per-zone boundary (the LI gas island and the NYC system carry materially
different delivery costs). Measured, forward-native, rule-13 admissible; nothing
fitted to a residual (CLAUDE.md rules #1/#11/#12/#13; gap register G-13). One
mechanism per phenomenon (rule 19) — the monthly adder stays OFF.

Two configs, selected by --config:

  * ``ldc``     — the candidate / keeper-candidate config.
  * ``ldc-abl`` — the D-3 zero-forcing ablation twin (rule 21): the candidate
                  recipe verbatim with every merchant floor/bridge zero-forced.

Usage:
  python scripts/solve_nyiso55_ldc_transport.py --config ldc     [--years 2023 2024 2025]
  python scripts/solve_nyiso55_ldc_transport.py --config ldc-abl [--years 2023 2024 2025]
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
    "ldc": REPO / "results" / "calibration" / "nyiso55_ldc_transport",
    "ldc-abl": REPO / "results" / "calibration" / "nyiso55_ldc_transport-ablation",
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
    # nyiso-53 recipe base; downstate CT gas grounded DAILY (one mechanism per
    # phenomenon, rule 19) on the per-zone LDC non-firm transport datatype (v2).
    overrides["nyiso_downstate_ct_gas_basis"] = False
    overrides["nyiso_downstate_ct_gas_daily"] = True
    overrides["nyiso_li_lcr_tsl"] = True
    overrides["use_plant_emission_rates_v2"] = True
    note = (
        "G-13: nyiso-53 recipe with the downstate CT-peaker gas re-grounded on "
        "the measured per-zone daily delivered index (nyiso_downstate_ct_gas_daily; "
        "nyiso-downstate-gas datatype v2: Transco Z6 NY daily commodity + monthly "
        "LDC non-firm transportation delivery rate, KEDNY SC-22 for NYC / KEDLI "
        "SC-19 for Long Island). Supersedes nyiso-54's statewide firm-citygate "
        "premium with the correct rate class + per-zone boundary (rules "
        "#1/#11/#12/#13). Keeps nyiso_li_lcr_tsl + use_plant_emission_rates_v2."
    )
    if args.config == "ldc-abl":
        kwargs["zero_forcing_ablation"] = True
        kwargs["ablation_of"] = "nyiso55_ldc_transport"
        note = (
            "D-3 zero-forcing ablation twin (rule 21) of the per-zone LDC-transport "
            "candidate: the candidate recipe verbatim with all merchant "
            "floors/bridges zero-forced."
        )
    kwargs["note"] = note

    print(f"solving {out.name} [{args.config}] years {kwargs['years']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()
