"""caiso-78 probe: corrected CC heat-rate basis on the caiso-77 keeper recipe.

RECIPE-IDENTICAL to the caiso-77 keeper
(`scripts/probes/_caiso77_firm_selfschedule_ab.py`): same flags, same measured
inputs, zero new free parameters. The single delta is CODE-LEVEL — the
`fleet_to_bins` heat-rate/capacity-basis fix
(FINDING-caiso78-cc-hr-basis-2026-07-12.md §3): under
``cc_nameplate_summer_derate`` the plant base heat rate was divided by the
nameplate-rescaled capacity instead of the net-summer basis its weights were
accumulated on, deflating every CC plant's offer by its own
net-summer/nameplate ratio (Moss Landing −27 %, Otay Mesa −17 %, La Paloma
−13 %, AES ECs −10/−11 %; CAISO CC median −9 %). The deflation was
DIFFERENTIAL, scrambling the within-CC merit order — the C1 CC-over cluster is
five deflated plants over-running with Pastoria (the least-deflated peer)
under-running −1.7 TWh/yr.

THE TARGET is the C1-2023 CC_REGULAR +4.50 TWh residual and the within-class
plant scramble. Pre-registered directions (FINDING §4): C1 CC falls all years
with the plant table compressing; CT_PEAKER rises modestly (the class-margin
CC-vs-CT ordering does NOT flip — measured post-fix; the CT gap stays owned by
the local-commitment lane); C5a CO2 falls; C4 gas r rises. DISCLOSED
counter-moves: C3a/C3b print WORSE (the corrected marginal CC offer is ~10 %
higher — the deflated HR was silently compensating the body overprice; rules
1/14 the accurate input stays), and the 930-family C2 rows may print further
under while the CEMS same-fleet truth improves (adjudicated per the caiso-77
§5 posture).

Registered as PROBES (main + zero-forcing ablation twin).

Usage: python scripts/probes/_caiso78_cc_hr_basis_ab.py {main|ablation}
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
    out = ROOT / ("caiso78_cc_hr_basis" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-77 keeper recipe, unchanged (the caiso-78 delta is the
    # fleet_to_bins heat-rate-basis code fix, not a flag).
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True

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
        ablation_of=(out.parent / "caiso78_cc_hr_basis").name if ablate else None,
        note=(
            f"caiso-78 corrected CC heat-rate basis {mode} -- caiso-77 keeper "
            "recipe on the fleet_to_bins HR/capacity-basis fix "
            "(FINDING-caiso78-cc-hr-basis-2026-07-12.md), 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
