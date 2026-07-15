"""caiso-85 probe: scarcity-overlay import-headroom on the caiso-80 keeper recipe.

RECIPE-IDENTICAL to the caiso-80 keeper
(`scripts/probes/_caiso80_supply_consistent_demand_ab.py`) — same flags, same
measured inputs, zero new free parameters. The single delta is
``caiso_scarcity_import_headroom=True``: the CAISO post-solve scarcity overlay
(caiso_scarcity_pricing, on in the recipe) gains the hourly unloaded must-offer
import capability in its LOLP reserve measure — min( Σ import-tranche
pmax·availability − import dispatch, the measured WECC corridor import cap −
import dispatch ). RA imports are must-offer and must exhaust before CAISO's
power-balance penalty prices fire (CPUC D.20-06-028), so the overlay should not
price scarcity while the LP still holds unloaded sub-VOLL import supply
(FINDING-caiso-winter-gas-level-2026-07-15 §3).

Post-solve overlay ONLY: dispatch, volumes and C1/C2/C4 are byte-identical to
the caiso-80 keeper (the bundle's tripwire — verify the invariance); only the
scarcity adder (hence C3a/C3c) moves. PRE-REGISTERED directions: C3c falls, most
in non-January hours where corridor headroom exists (January binding hours move
little); C3a slightly down; C6/C7/C8 hold.

Registered as a PROBE, all three years in one invocation (rule 16), NO
zero-forcing ablation twin (rule 21 as amended 2026-07-14). Year-invariant
code-level change (the caiso-78 precedent): no per-year LOYO needed.

Usage: python scripts/probes/_caiso85_scarcity_import_headroom_ab.py main
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "caiso65_seam_envelope_clock"


def main(mode: str) -> None:
    if mode != "main":
        raise SystemExit(
            "caiso-85 carries no ablation twin (rule 21 amended 2026-07-14); "
            "run with 'main'."
        )
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso85_scarcity_import_headroom"
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-80 keeper recipe, unchanged, plus the SINGLE caiso-85 delta:
    # the import-headroom reserve measure in the scarcity overlay.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True
    overrides["caiso_scarcity_import_headroom"] = True  # THE caiso-85 delta

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
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
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
        note=(
            "caiso-85 scarcity import-headroom main -- caiso-80 keeper recipe + "
            "caiso_scarcity_import_headroom=True (unloaded must-offer import in the "
            "overlay LOLP reserve measure, FINDING-caiso-winter-gas-level-2026-07-15 "
            "S3), 2023-2025"
        ),
    )
    print(f"DONE main -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
