"""caiso-98 B-leg: caiso-97 keeper recipe + measured EIA-860 per-vintage storage.

CAISO-98 Mechanism A (FINDING-caiso98 §7): the keeper runs a FLAT 8 GW battery
fleet (`storage_vintage_ramp=False`, STORAGE_BASE_FLEET_MW[CAISO]["mid"]) while
the real CAISO fleet roughly triples 2023->2025 (EIA-930 NG:OTH discharge
4.0->11.3 TWh; EIA-860 commissioned ~3.0 GW during 2023, ~3.6 GW during 2024).
The decomposition (`_caiso_storage_timing.py`) showed the C3a-2025 belly
over-price lives ENTIRELY in the model's storage-charging hours and the evening
under-price tracks storage over-discharge -- both driven by the oversized flat
fleet in 2023/2024.

This B-leg is the rule-11 measured-input correction: the SAME caiso-97 keeper
recipe with `storage_vintage_ramp=True` -- the EIA-860 backcast battery fleet
ramped month-by-month from each unit's COD (already plumbed through
`solve_and_persist`). NOT a new timing/floor mechanism; a measured fleet
replacing a flat guess. Adjudicated A/B against the same-machine
`caiso98_repro_A` (FINDING-caiso92b protocol -- committed bundles are never the
baseline). Pre-registered report-back (FINDING-caiso98 §7 Mechanism A gates):
2023 belly over-charge/over-price shrink toward measured; evening under-price
toward 0; 2025 ~unchanged (fleet already ~measured); C1 12/12 holds; overnight
lambda unchanged; C3c unchanged; C7/C8 PASS; C5a improves or holds; NO overshoot.
Registered whatever the result (rule 15).

Usage: python scripts/probes/_caiso98_vintage_ramp_B.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _caiso95_repro_A import BASE, _keeper_overrides  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"


def main() -> None:
    cf = json.loads((BASE / "run_config.json").read_text())["calibration_flags"]
    overrides = _keeper_overrides(cf)
    overrides["caiso_ra_startup_trajectory"] = True  # caiso-96 (owner carry ruling)
    overrides["caiso_dsw_daytime_evening_trim"] = True  # caiso-97 (the WP-2 delta)
    out = ROOT / "caiso98_vintage_ramp_B"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-98 Mechanism A -- caiso-97 KEEPER recipe + storage_vintage_ramp "
        "(measured EIA-860 per-vintage battery fleet replacing the flat 8 GW "
        "base; rule-11 measured-input correction, FINDING-caiso98 s7), 2023-2025"
    )

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
        caiso_offer_surface_measured=True,
        caiso_offer_surface_conditional=True,
        storage_vintage_ramp=True,  # caiso-98 Mechanism A (the ONLY delta vs the A-leg)
        note=note,
    )
    print(f"DONE vintage-ramp B-leg -> {out}")


if __name__ == "__main__":
    main()
