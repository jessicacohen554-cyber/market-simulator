#!/usr/bin/env python3
"""Write pjm-h19's governance attestation into the PJM ``demand_balance_screen`` composites.

The C6 governance gate reads ``<bundle>/calibration_attestation.json``. A
COMPOSED bundle does not inherit it (``pjm_h19_compose_span.py`` copies only
year-scoped files), so the parent writes it once, here, from the incumbent
keeper's own ledger (pjm-h15 correction #2).

Rule 21 ``[R-DOF]``: the DOF ledger is CARRIED FORWARD VERBATIM from
``hydro2_pjm_ror_span`` because this arm adds **zero** free parameters. The
screen's only constant is Tukey's published far-out multiplier (3), applied to
each BA-year's own hourly-ramp distribution, and its attribution leg is
EIA-930's own balance identity (Demand vs Net generation - Total interchange).

Usage: python3 scripts/gen_pjm_h19_attestation.py [bundle ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/hydro2_pjm_ror_span/calibration_attestation.json"
DEFAULT_OUT = [
    REPO / "results/calibration/pjm_h19_dbs_span",
    REPO / "results/calibration/pjm_h19_dbs_touchpoint",
]

ATTESTED_BY = (
    "pjm-h19 orchestrator (2026-09-23). The incumbent keeper recipe "
    "2026-09-22-pjm-hydro2-ror-span (hydro2_pjm_ror_span + "
    "hydro2_pjm_ror_touchpoint) replayed at pinned HEAD "
    "2d57aa2089d687d9251f229474f84601a3111059 via scripts/replay_keeper.py "
    "--set demand_balance_screen=true, ONE YEAR PER SHARD CONTAINER (rule 36 "
    "[R-YEAR-ISOLATION] (a)), ZERO LP MINUTES IN THE PARENT (rule 32 [R-SHARD] "
    "(a)), composed at zero LP by scripts/probes/pjm_h19_compose_span.py, "
    "benchmark rebuilt with run_calibration_full.py --rebuild-benchmark, and "
    "legitimacy_diagnostics.json REGENERATED over each composite. CONTROL = the "
    "committed keeper bundles (rule 29 [R-SCREEN] (b) form 4); G-DRIFT "
    "152c546a -> 2d57aa20 audited (LP INERT; ad42fe43 benchmark-builder change "
    "LIVE for scoring only, so the control is re-scored on the same HEAD "
    "benchmark) and recorded in docs/PRECOMMIT-pjm-h19-demand-balance-screen-"
    "2026-09-23.md BEFORE any solve. The bar and gates G0-G3 were fixed ex ante "
    "in that PRECOMMIT; bars v1/v2 were retired pre-solve with reasons stated "
    "there, and nothing was amended after a solve number landed."
)

NOTE = (
    "ONE CONFIG DELTA on the keeper's own recipe: demand_balance_screen False -> "
    "True. THE DEFECT: four EIA-930 PJM Demand readings are physically "
    "impossible - 2020 h5003 192.2 GW, h5031 176.1 GW, h5383 138.6 GW and a "
    "2024 h7787 dropout at 56.3 GW - each departing EIA-930's own balance "
    "measurement (Net generation - Total interchange) by 35-57 GW while that "
    "measurement stays smooth. The keeper served the first two by shedding "
    "28.2 GW and 13.5 GW at VOLL. The existing spike (2.5x median) and dropout "
    "(exactly 0 MW) screens miss all four. The screen repairs an hour only if "
    "its demand reverses by more than the BA-year's own Tukey far-out hourly "
    "ramp AND its |D - (NG - TI)| exceeds both neighbours'; census over every "
    "ISO-year 2018-2025 touches exactly these four hours in PJM's modelled "
    "span. Rule 14 [R-ACCURATE] source-data repair, ZERO FREE PARAMETERS "
    "(rules 21/24). Rule 1 [R-STRUCT]: scored criteria are reported at full "
    "magnitude; a wrong-way move keeps the repair and opens a root-cause "
    "question."
)


def build(src: dict) -> dict:
    """Attestation dict for the arm composites, derived from the keeper's."""
    return {
        "schema": src["schema"],
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": ATTESTED_BY,
            "note": NOTE,
        },
        "exceptions": src.get("exceptions", []),
        "free_parameters": src["free_parameters"],
        "delta_vs_incumbent": {
            "keeper": (
                "2026-09-22-pjm-hydro2-ror-span "
                "(results/calibration/hydro2_pjm_ror_span + "
                "hydro2_pjm_ror_touchpoint)"
            ),
            "config_deltas": ["demand_balance_screen: False -> True"],
            "n_config_deltas": 1,
            "code_deltas": [
                "4b66bc2d: data/eia930/demand.py::_screen_demand_balance + the "
                "default-off ScenarioConfig.demand_balance_screen (off path "
                "byte-identical; cache-key optional field)",
            ],
            "free_parameters_added": 0,
            "dof_ledger": {
                "n_entries": src["free_parameters"]["n_entries"],
                "n_residual": src["free_parameters"]["n_residual"],
                "carried": "VERBATIM from the incumbent keeper; zero entries added.",
            },
            "authorized_price_tuning": src["delta_vs_incumbent"].get(
                "authorized_price_tuning"
            ),
        },
    }


def main() -> None:
    """Write the attestation into each named (or default) composite bundle."""
    att = build(json.loads(SRC.read_text()))
    outs = [Path(a) for a in sys.argv[1:]] or DEFAULT_OUT
    for d in outs:
        if not d.is_dir():
            print(f"skip {d} (absent)")
            continue
        (d / "calibration_attestation.json").write_text(
            json.dumps(att, indent=1) + "\n"
        )
        print(f"wrote {d}/calibration_attestation.json")


if __name__ == "__main__":
    main()
