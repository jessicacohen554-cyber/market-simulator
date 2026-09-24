"""Emit the NWPP-49 calibration attestation for ``results/calibration/nwpp49_ror_span``.

NWPP-49 is the NWPP-47 keeper's frozen recipe plus **exactly one** solve-affecting
field, ``hydro_ror_split`` (owner ruling 2026-09-24, "RoR split, chain exempt":
adopt the hydro structure the other ISOs' keepers carry). The classifier
(``scripts/data/curate_hydro_plant_modes.py``) pins EHA run-of-river plants flat
at their own monthly water, EXCEPT the plants in the registered regulated-chain
table ``data/raw/nwpp-hydro/nwpp_hydro_chain.csv`` (rule 0 ``regulated_chain``),
whose inflow is an upstream release and whose hydraulics the cascade models.

**ZERO FREE PARAMETERS** (rules 21 / 24): a categorical external classifier and a
committed registry. Nothing transferred from another ISO (rule 25). Three
year-isolated shards (rule 36) via ``replay_keeper.py --set``, composed at zero
LP. Pre-registration ``docs/handoffs/PRECOMMIT-nwpp-49-ror-split-2026-09-24.md``;
evaluator ``scripts/probes/_nwpp49_gates.py --arm ror_chain_exempt`` (committed
before any leg launched). Verdict of that evaluator: INERT (I).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import update_attestation  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwpp49_ror_span"
KEEPER_BUNDLE = REPO / "results/calibration/nwpp47_gridwind_span"

#: This lane's arm.
_ARMED = ("hydro_ror_split",)

#: Inherited from the NWPP-46 keeper and unchanged; re-checked so a silent drift
#: cannot ride this attestation.
_INHERITED = {
    "nwpp_grid_carried_wind_served": True,
    "hydro_pondage_bound": False,
    "hydro_dispatch_envelope": True,
    "hydro_min_flow_floor": True,
    "hydro_cascade_coupling": True,
    "coal_takeorpay_from_data": True,
    "coal_committed_takeorpay_regulated": True,
    "measured_coal_heat_rates": True,
    "coal_prb_proxy_own_iso": True,
    "plant_level_fleet": True,
    "use_campd_bins": True,
    "mode": "backcast",
}


def _check_recipe(bundle: Path) -> None:
    """Refuse a bundle whose config is not the keeper recipe plus this arm."""
    sc = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    bad = [
        f"{f} = {sc.get(f)!r}, expected True" for f in _ARMED if sc.get(f) is not True
    ]
    bad += [
        f"{f} = {sc.get(f)!r}, expected {want!r} (inherited)"
        for f, want in _INHERITED.items()
        if sc.get(f) != want
    ]
    if bad:
        raise SystemExit(
            "gen_nwpp49_attestation refuses this bundle:\n  " + "\n  ".join(bad)
        )


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-49 attestation (after seeding the canonical DOF ledger)."""
    _check_recipe(bundle)
    update_attestation(bundle, "NWPP")
    att = json.loads((bundle / "calibration_attestation.json").read_text())
    keeper = json.loads((KEEPER_BUNDLE / "calibration_attestation.json").read_text())
    att["schema"] = "calibration-attestation/v1"
    att["lane"] = "NWPP-49"
    att["bundle"] = bundle.name

    switches = dict(keeper.get("switches", {}))
    switches["hydro_ror_split"] = {
        "value": True,
        "where": (
            "ScenarioConfig.hydro_ror_split, armed through replay_keeper --set "
            "(prb_overrides); consumed by data.hydro.build_hydro_fleet via "
            "data.hydro_modes.load_hydro_shapeable (hydro-plant-modes clean "
            "partition, NWPP)"
        ),
        "identification": "measured-physical",
        "source": (
            "ORNL EHA FY2024 operational Mode + the HILARRI completion rules "
            "(categorical, no threshold), with rule 0 regulated_chain: the 27 "
            "plants of data/raw/nwpp-hydro/nwpp_hydro_chain.csv are shapeable "
            "(CROHMS: the chain's EHA-RoR plants swing 372-421 MW within the day). "
            "157 / 154 / 154 plants pinned flat (2023 / 24 / 25; 2023 carries four "
            "backfilled ~8 MW RoR plants), all off the chain."
        ),
    }
    att["switches"] = switches

    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "authorized_price_tuning": None,
        "notes": (
            "levers_trace_to_measured_input: the arm is a categorical external "
            "plant-mode classification (EHA/HILARRI) plus a committed chain "
            "registry, the same mechanism five other ISOs' keepers carry; no "
            "magnitude, nothing swept. It was declared in PRECOMMIT-nwpp-49 with "
            "its prediction and kill limbs committed before any leg launched. "
            "no_fit_to_price_residuals: NWPP is PRICE UNSCORED (rubric v3.8); "
            "authorized_price_tuning is NONE. no_pinning_to_actuals: the flat level "
            "is each plant's own monthly budget, an input; it regenerates for any "
            "year. outage_filter_exogenous_net_load: unchanged from NWPP-47."
        ),
    }
    att["exceptions"] = []
    disc = att.setdefault("disclosures", {})
    disc["kill_condition_pre_registered"] = (
        "PRECOMMIT-nwpp-49-ror-split §4, coded in scripts/probes/_nwpp49_gates.py "
        "--arm ror_chain_exempt before any leg launched. The INERT limb FIRED in "
        "every year: hydro intra-day sd ratio 1.075 -> 1.074, 1.155 -> 1.153, "
        "1.169 -> 1.167 (ceiling 1.065 / 1.145 / 1.159). No OVERSHOOT limb fired: "
        "hydro annual energy moved 0.000 TWh; coal r 0.659 -> 0.660, 0.617 -> "
        "0.618, 0.638 -> 0.638."
    )
    disc["the_prediction_was_wrong_and_why"] = (
        "The pro-rata static clip predicted the ratio would fall to as low as "
        "0.997 / 1.066 / 1.082. It did not: the pinned plants are exactly flat, "
        "but the LP moves the same swing onto the shapeable reservoirs (Grand "
        "Coulee and the rest), which carry ample headroom. The fleet shape is "
        "set by the price signal and the reservoir envelope, not by which small "
        "plants shape."
    )
    disc["why_armed_anyway"] = (
        "Owner ruling 2026-09-24: adopt the hydro structure the other ISOs "
        "carry, chain exempt. Rule 1 [R-STRUCT]: a real mechanism is not judged "
        "by whether it moves the residual. Precedent: PJM's keeper carries "
        "hydro_budget_nameplate_aware at an I cell."
    )
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
