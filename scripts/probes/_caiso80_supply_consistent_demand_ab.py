"""caiso-80 probe: supply-consistent honest demand on the caiso-78 keeper recipe.

RECIPE-IDENTICAL to the caiso-78 keeper
(`scripts/probes/_caiso78_cc_hr_basis_ab.py`, which is the caiso-77 keeper
recipe on the fleet_to_bins HR fix): same flags, same measured inputs, zero
new free parameters. The single delta is ``caiso_supply_consistent_demand=
True`` — the owner-signed caiso-80 Option A
(FINDING-caiso80-demand-basis-wedge-2026-07-13 §6): the CISO EIA-930 Demand
cell carries the same fabricated solar-shaped block as the corrupt NG cell
(Demand = NetGen + TI identity, onset 2024-05) plus the CHP host-accounting
wedge and the chronic identity gap — +10.4/+11.6/+18.5 TWh/yr the real grid
fleet never served. The demand input becomes the derived measured series
demand(t) = 930 NetGen(t) − NG_cell(t) + CEMS bench-gas grid(t) + cogen flat
+ fold-in flat − TI(t) (207.40/212.19/205.59 TWh), the exact honest basis the
run is scored against. Supersedes caiso_demand_clock_realign by construction.

PRE-REGISTERED directions (FINDING §6): C1 CC_REGULAR over-run shrinks toward
the honest actuals (largest 2025); C2 over-print shrinks; C3a falls with the
year-gradient (2025 most; 2023 tight months ~unchanged — already correct);
C3b NRMSE improves; C4-2025 r improves; C5a CO2 over falls; h16-18 demand
RISES ~1-2.7 GW so evening gas/CT move UP (the surviving CT deficit the
approved local-commitment driver sizes against shrinks); model imports fall
toward the measured TI; solar curtailment rises toward actual. C6/C7/C8 must
hold. DISCLOSED risk: the 2023 May/Jun soft-month overprice may not fully
close (its wedge share is the less-identifiable flat component).

Registered as PROBES (main + zero-forcing ablation twin), LOYO within
2023-2025 before any promotion.

Usage: python scripts/probes/_caiso80_supply_consistent_demand_ab.py {main|ablation}
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
    out = ROOT / ("caiso80_supply_consistent_demand" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-78 keeper recipe, unchanged, plus the SINGLE caiso-80 delta:
    # the supply-consistent honest demand input (owner-signed Option A).
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True  # THE caiso-80 delta

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
        ablation_of=(
            (out.parent / "caiso80_supply_consistent_demand").name if ablate else None
        ),
        note=(
            f"caiso-80 supply-consistent honest demand {mode} -- caiso-78 keeper "
            "recipe + caiso_supply_consistent_demand=True (owner-signed Option A, "
            "FINDING-caiso80-demand-basis-wedge-2026-07-13), 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
