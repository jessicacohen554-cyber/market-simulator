"""caiso-82 probe: hydro run-of-river/min-flow floor on the caiso-80 keeper recipe.

RECIPE-IDENTICAL to the caiso-80 keeper
(`scripts/probes/_caiso80_supply_consistent_demand_ab.py` — the caiso-78
keeper recipe + the owner-signed supply-consistent honest demand). The single
delta is ``hydro_dispatch_floor=True``: per-unit hourly min_gen at the
measured per-(month x hod) p05 of EIA-930 NG:WAT
(constants.HYDRO_FLOOR_PERCENTILE), pro-rata to each unit's monthly budget
share — the min-flow mirror of the armed p95 envelope (caiso-72). Zero new
fitted values; mechanism MECH_HYDRO_MINFLOW (non-thermal must-flow, ablated
in the twin).

Evidence + PRE-REGISTERED directions:
`results/calibration/FINDING-caiso82-soft-month-margin-2026-07-14.md` §4 —
hydro trough dispatch rises onto the measured min-flow band (the workflow
tripwire) and the twin drops back; C3a ~NEUTRAL (the disclosed 2023
single-year smoke showed the budget reallocation nets out at the mean, so
the promotion case is rule-1 STRUCTURAL FIDELITY with all gates holding —
the caiso-72 envelope precedent — not fit improvement); C1/C2/C4/C5a/C6/
C7/C8 hold within their current bands.

Registered as PROBES (main + zero-forcing ablation twin), all three years in
one invocation (rule 16).

Usage: python scripts/probes/_caiso82_hydro_minflow_ab.py {main|ablation}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "caiso65_seam_envelope_clock"


def main(mode: str) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    ablate = mode == "ablation"
    out = ROOT / ("caiso82_hydro_minflow" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-80 keeper recipe, unchanged, plus the SINGLE caiso-82 delta:
    # the measured hydro min-flow floor.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True
    overrides["hydro_dispatch_floor"] = True  # THE caiso-82 delta

    solve_and_persist(
        cf["years"],  # all three years in one call (rule 16)
        cf["iso"],
        cf["hours"],
        _load_reference(),
        commitment=cf["commitment"],
        screen_coal=cf["commitment_screen_coal"],
        run_dir=out,
        coal_lignite_mustrun=cf["coal_lignite_mustrun"],
        coal_prb_mustrun=cf["coal_prb_mustrun"],
        coal_prb_passthrough=cf["coal_prb_passthrough"],
        outage_source=cf["outage_source"],
        coal_prb_passthrough_sigmoid=cf["coal_prb_passthrough_sigmoid"],
        coal_mustrun_per_plant=cf["coal_mustrun_per_plant"],
        retiree_cems_cap=cf["retiree_cems_cap"],
        ct_mustrun_per_plant=cf["ct_mustrun_per_plant"],
        ct_mustrun_floor_frac=cf["ct_mustrun_floor_frac"],
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=overrides,
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],
        ercot_dam_as_overlay=cf["ercot_dam_as_overlay"],
        ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
        ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={
            "offer_curve_smoothing_n": 6,
            "offer_curve_smoothing_exp": 1.0,
            "offer_curve_smoothing_mid": None,
        },
        priced_interchange=cf["priced_interchange"],
        # Standing measured hydro budget correction (caiso-76, rules 1/14).
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
        # CAISO-specific structural flags carried by the keeper but absent
        # from calibration_flags (caiso-69/70/73/74/75/76/77 script docstrings).
        capacity_deliverability_limits=True,
        caiso_ra_mustoffer=True,
        caiso_ra_min_load_frac=0.26,
        caiso_ra_startup_bridge=True,
        caiso_ra_bridge_decommit=True,
        caiso_gas_floor_frac=0.8,
        caiso_solar_deliverability=True,
        caiso_solar_endogenous_spill=True,
        caiso_per_hub_intertie=True,
        caiso_perhub_firm_base=True,
        caiso_corridor_flow_limit=True,
        temp_dependent_derate=True,
        ct_netload_drag=False,
        zero_forcing_ablation=ablate,
        ablation_of=((out.parent / "caiso82_hydro_minflow").name if ablate else None),
        note=(
            f"caiso-82 hydro min-flow floor {mode} -- caiso-80 keeper recipe + "
            "hydro_dispatch_floor=True (measured p05 month x hod NG:WAT, "
            "FINDING-caiso82-soft-month-margin-2026-07-14 pre-registration), "
            "2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
