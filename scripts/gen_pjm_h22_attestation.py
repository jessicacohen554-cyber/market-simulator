#!/usr/bin/env python3
"""Write pjm-h22's governance attestation into the PJM Card E (RGGI) composites.

The C6 governance gate reads ``<bundle>/calibration_attestation.json``. A
COMPOSED bundle does not inherit it, so the parent writes it once, here, from
the incumbent keeper's own ledger (pjm-h15 correction #2).

Rule 21 ``[R-DOF]``: the incumbent ledger is carried VERBATIM and ONE entry is
appended — the RGGI allowance price, identification ``measured-external``
(published auction clearing prices; exactly as pjm-146 ledgered it, 18 -> 19
with ``n_residual`` unchanged). It adds zero free parameters: nothing is chosen
by this session. ``offer_curve_by_group`` is untouched, so the rules-1/13
authorized price-tuning channel is not used.

Usage: python3 scripts/gen_pjm_h22_attestation.py [bundle ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/pjm_h19_dbs_span/calibration_attestation.json"
DEFAULT_OUT = [
    REPO / "results/calibration/pjm_h22_rggi_span",
    REPO / "results/calibration/pjm_h22_rggi_touchpoint",
]
PIN = "d58121c34e0b79259ae3d4103fe4ee828080c79e"

ATTESTED_BY = (
    "pjm-h22 orchestrator (2026-09-24). The incumbent keeper recipe "
    "2026-09-23-pjm-h19-dbs-span (pjm_h19_dbs_span + pjm_h19_dbs_touchpoint) "
    f"replayed at pinned HEAD {PIN} via scripts/replay_keeper.py --set "
    "pjm_rggi_allowance_pricing=true, ONE YEAR PER SHARD CONTAINER (rule 36 (a)), "
    "ZERO LP MINUTES IN THE PARENT (rule 32 (a)), composed at zero LP by "
    "scripts/probes/pjm_h22_compose_span.py, benchmark rebuilt with "
    "run_calibration_full.py --rebuild-benchmark, legitimacy_diagnostics.json "
    "REGENERATED over each composite. CONTROL = the committed keeper bundles "
    "(rule 29 (b) form 4); G-DRIFT 2d57aa20 -> pin audited (all hunks INERT for "
    "the PJM control) and recorded in docs/PRECOMMIT-pjm-h22-card-e-rggi-six-"
    "years-2026-09-24.md BEFORE any solve, with gates and predictions fixed ex "
    "ante; nothing was amended after a solve number landed."
)

NOTE = (
    "ONE CONFIG DELTA on the keeper's own recipe (Card E): "
    "pjm_rggi_allowance_pricing False -> True. RGGI-member fossil units (exact "
    "per-plant EIA-860 state test; NJ/MD/DE 2020-2025, VA 2021-2023) are charged "
    "the published RGGI auction clearing price, annual mean, metric-converted "
    "(7.07/10.44/14.84/14.87/22.83/24.35 $/t for 2020-2025) times their own "
    "emission rate. 2020-2022 inputs landed this lane, zero LP. Rule 13: an "
    "input a forward allowance-price path regenerates. ZERO FREE PARAMETERS "
    "(rules 21/24). Rule 1 [R-STRUCT]: scored criteria are reported at full "
    "magnitude."
)

RGGI_ENTRY = {
    "name": "PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE (pjm_rggi_allowance_pricing) — "
    "published RGGI quarterly auction clearing prices, annual mean, metric-converted",
    "where": "run_config.scenario_config.pjm_rggi_allowance_pricing + "
    "src/market_sim/config/fuel_trajectories.py::PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE + "
    "capacity_market.py::RGGI_MEMBER_STATES_BY_YEAR / PJM_RGGI_ZONE_SHARE",
    "identification": "measured-external",
    "source": "RGGI, Inc. Allowance Prices and Volumes (auctions A47-A70), "
    "data/raw/policy/carbon-auction-results/carbon-auction-results.csv; "
    "identical to the NEISO metric series; re-derived per year by "
    "tests/unit/policy/test_cap_and_trade.py. Membership: published RGGI "
    "participating-states list.",
    "free_parameters_added": 0,
    "why_zero": "Nothing is chosen by this session: prices are published, "
    "membership is legal fact, emission rates are the fleet's own. No residual "
    "selected the lever (owner charter, FINDING-pjm-h21 §6.1).",
}


def build(src: dict) -> dict:
    """Attestation dict for the arm composites, derived from the keeper's."""
    fp = dict(src["free_parameters"])
    fp["entries"] = list(fp["entries"]) + [RGGI_ENTRY]
    fp["n_entries"] = int(src["free_parameters"]["n_entries"]) + 1
    fp["n_residual"] = int(src["free_parameters"]["n_residual"])
    assert fp["n_entries"] == len(fp["entries"])
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
        "free_parameters": fp,
        "delta_vs_incumbent": {
            "keeper": (
                "2026-09-23-pjm-h19-dbs-span "
                "(results/calibration/pjm_h19_dbs_span + pjm_h19_dbs_touchpoint)"
            ),
            "config_deltas": ["pjm_rggi_allowance_pricing: False -> True"],
            "n_config_deltas": 1,
            "code_deltas": [
                "RGGI 2020-2022 input rows (membership, zone share, price); "
                "read only under the flag"
            ],
            "free_parameters_added": 0,
            "dof_ledger": {
                "n_entries": fp["n_entries"],
                "n_residual": fp["n_residual"],
                "carried": "VERBATIM from the incumbent keeper plus ONE "
                "measured-external entry (the RGGI price); n_residual unchanged.",
            },
            "authorized_price_tuning": {
                "used": False,
                "note": "NO band multiplier was touched; offer_curve_by_group is "
                "carried byte-identical from the incumbent keeper.",
            },
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
