"""Integration check: caiso_locational_as_families builds a valid design.

Calls the REAL get_reserve_design with the flag on, prints the family names +
zone masks + requirement means, and runs build_reserve_dispatch_kwargs to
confirm the multi-family pergen layout accepts the zone-masked families. Aborts
before the LP.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "caiso65_seam_envelope_clock"


class _Done(Exception):
    pass


def main():
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "_caiso71_fam_tmp"
    out.mkdir(parents=True, exist_ok=True)
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides.update(
        energy_reserve_coopt=True,
        caiso_reserve_coopt=True,
        caiso_commitment_posture=True,
        caiso_scarcity_pricing=False,
        caiso_locational_as_families=True,
    )

    import market_sim.config.reserve_config as rc

    orig = rc.get_reserve_design

    def patched(config, fleet_arrays, hours, zone_names, **kw):
        design = orig(config, fleet_arrays, hours, zone_names, **kw)
        znames = list(zone_names)
        print("\n===== caiso_locational_as_families design =====")
        for fam in design.families:
            zs = [znames[i] for i in np.flatnonzero(fam.zone_mask)]
            print(
                f"  {fam.name:28s} req_mean={fam.requirement.mean():7.1f} MW zones={zs}"
            )
        kwbuild = rc.build_reserve_dispatch_kwargs(design)
        zm = kwbuild.get("reserve_balance_zone_mask")
        print(
            f"  n_families={len(design.families)}  balance_zone_mask shape="
            f"{None if zm is None else zm.shape}"
        )
        print(
            f"  pergen_gen_idx n={None if design.pergen_gen_idx is None else design.pergen_gen_idx.size}"
            f"  posture_pools n={0 if design.posture_pools is None else design.posture_pools.size}"
        )
        print("  build_reserve_dispatch_kwargs OK")
        print("================================================\n")
        raise _Done()

    rc.get_reserve_design = patched
    try:
        solve_and_persist(
            [2024],
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
            note="caiso-71 families check (aborts before LP)",
        )
    except _Done:
        print("aborted before LP as designed.")
    finally:
        rc.get_reserve_design = orig


if __name__ == "__main__":
    main()
