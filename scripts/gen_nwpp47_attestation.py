"""Emit the NWPP-47 calibration attestation for ``results/calibration/nwpp47_gridwind_span``.

NWPP-47 is the NWPP-46 keeper's frozen recipe plus **exactly one** solve-affecting
field, ``nwpp_grid_carried_wind_served`` (owner ruling on FINDING-nwpp-45 §8 =
framing 1, the plant-level attribution intake). The NWPP served interchange
removes GRID's PNM / SRP / WALC legs as Desert-Southwest resources the fleet
does not own; plant-level evidence shows the PNM leg IS GRID's own EIA-930
``NG: WND`` (max |diff| <= 2 MW every hour, 2023-2025), and that wind is carried
in the model supply from the pool frame. Armed, its export leg is served, so the
energy is no longer removed from the requirement while still supplied.

**ZERO FREE PARAMETERS** (rules 21 / 24): one measured series already in the
pool frame, no magnitude, nothing swept. Nothing is transferred from another ISO
(rule 25). Three year-isolated shards (rule 36) through ``replay_keeper.py
--set`` against the keeper's own ``meta.json``, composed by the parent at zero
LP. Evidence: ``docs/handoffs/FINDING-nwpp-47-2026-09-22.md``; pre-registration
``docs/handoffs/PRECOMMIT-nwpp-47-2026-09-22.md``; evaluator
``scripts/probes/_nwpp47_gates.py`` (committed before any leg landed).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import update_attestation  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwpp47_gridwind_span"
KEEPER_BUNDLE = REPO / "results/calibration/nwpp46_hydroenv_span"

#: This lane's arm.
_ARMED = ("nwpp_grid_carried_wind_served",)

#: Inherited from the NWPP-46 keeper and unchanged; re-checked so a silent drift
#: cannot ride this attestation.
_INHERITED = {
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
            "gen_nwpp47_attestation refuses this bundle:\n  " + "\n  ".join(bad)
        )


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-47 attestation (after seeding the canonical DOF ledger)."""
    _check_recipe(bundle)
    update_attestation(bundle, "NWPP")
    att = json.loads((bundle / "calibration_attestation.json").read_text())
    keeper = json.loads((KEEPER_BUNDLE / "calibration_attestation.json").read_text())
    att["schema"] = "calibration-attestation/v1"
    att["lane"] = "NWPP-47"
    att["bundle"] = bundle.name

    switches = dict(keeper.get("switches", {}))
    switches["nwpp_grid_carried_wind_served"] = {
        "value": True,
        "where": (
            "ScenarioConfig.nwpp_grid_carried_wind_served, armed through "
            "replay_keeper --set (prb_overrides); consumed by "
            "data.eia930.demand.load_demand -> envelopes.nwpp_net_interchange("
            "grid_carried_wind_served=True) + _nwpp_grid_pool_carried_wind"
        ),
        "identification": "measured-physical",
        "source": (
            "GRID's own EIA-930 NG: WND from the screened pool member frame the "
            "renewable supply sums. The GRID -> PNM interchange leg equals it to "
            "within 2 MW in every hour of 2023-2025 (2.073 / 2.179 / 2.002 TWh). "
            "LP demand moves +2.074 / +2.171 / +2.002 TWh; nothing else in the LP "
            "input moves."
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
            "levers_trace_to_measured_input: the arm is a boundary reconciliation of "
            "the served interchange to the pool's own renewable definition (rule 14), "
            "identified by an hourly identity in EIA-930, not a magnitude. It was "
            "declared in PRECOMMIT-nwpp-47 with its demand delta computed exactly "
            "before any solve, and the kill limbs were coded and committed before the "
            "first leg landed. no_fit_to_price_residuals: NWPP is PRICE UNSCORED "
            "(rubric v3.8); no offer_curve_by_group band is touched; "
            "authorized_price_tuning is NONE. no_pinning_to_actuals: the arm changes "
            "an interchange input, never an output; it regenerates for any year the "
            "EIA-930 pool frame exists (rule 13 forward test). The residual ~7-10 TWh "
            "930-vs-plant under-book (FINDING-nwpp-47 §3) is NOT absorbed by any "
            "lever here. outage_filter_exogenous_net_load: outage_source='historic', "
            "unchanged from NWPP-46."
        ),
    }
    att["exceptions"] = []
    disc = att.setdefault("disclosures", {})
    disc["kill_condition_pre_registered_and_survived"] = (
        "PRECOMMIT-nwpp-47 §5, coded in scripts/probes/_nwpp47_gates.py and committed "
        "before any leg landed. PLUMBING: P1 demand delta +2.074 / +2.171 / +2.002 "
        "TWh equals the pre-registered value exactly; generation moved +2.065 / "
        "+2.169 / +2.008. OVERSHOOT: no pinned class moved > 0.005 TWh; no class "
        "moved > 1.6 TWh. No limb fired. Self-test against the keeper reads INERT."
    )
    disc["the_prediction_was_made_ex_ante_and_landed"] = (
        "CC_REGULAR absorbed 0.69 / 0.73 / 0.78 of the added energy (pre-registered "
        "0.5-1.0); coal 0.16 / 0.08 / 0.03 (<= 0.3). 2023 C1 CC_REGULAR -8.641 -> "
        "-7.213 TWh vs actual, inside the pre-registered [-7.60, -6.57]."
    )
    disc["what_it_does_not_close"] = (
        "Rule 1 [R-STRUCT]: C1's 2023 CC_REGULAR row now sits inside its band as a "
        "CONSEQUENCE of a partial fix, not as the reason for it. The system gap "
        "remains -7.6 / -10.0 / -7.1 TWh: EIA-930 books only 0.53-0.66 of the "
        "CEMS-measured gas output of PGE / BPAT / PACW plants (0 for PACW in "
        "2023-24) while control BAs read 0.95-1.03, and no neighbouring BA carries "
        "it. Closing it requires measured plant generation in the requirement "
        "(FINDING-nwpp-45 §8 framing 2), an open owner decision. C4 is untouched."
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
