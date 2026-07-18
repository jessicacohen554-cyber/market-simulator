"""caiso-97 B-leg: caiso-94 keeper recipe + evening hod-trim + trajectory carry.

WP-2 of the caiso-95/96 lane (the C5a evening-mass charter). The owner ruled
(2026-07-18, session-logged): (1) the caiso-94 evening-window WATCH is TRIPPED
— three-legged evidence (+1.9/+2.1/+2.2 TWh/yr excess model evening import
hod 17-21 vs EIA-930; CT_PEAKER −1.1..−2.0 Mt/yr of C5a; evening λ
−6.6/−5.0/−2.4 pp) plus the caiso-96 demonstration that commitment forcing
alone cannot recover the mass — authorizing the FINDING-caiso94 §7
pre-registered fix: trim the ``caiso_dsw_daytime_clean`` tranche window
hod 6-21 → 6-17 (``caiso_dsw_daytime_evening_trim``, depth re-derived over
the trimmed window: 4,994/5,563/5,770 MW, frozen gates CV 0.060 / LOYO
≤13.5 %); and (2) ``caiso_ra_startup_trajectory`` CARRIES into the recipe
(the caiso-96 zero-parameter measured-conduct extension — this leg solves the
COMPOSITION).

Adjudicated A/B against the same-machine fresh ``caiso95_repro_A`` re-solve
(FINDING-caiso92b protocol — cross-machine HiGHS spread 0.5-1.2 TWh/yr, so
committed bundles are never the baseline). Pre-registered report-back
(CAISO-97 charter): evening hod 17-21 λ must RISE toward actual (the
−6.6/−5.0/−2.4 gap closes); evening net import falls toward the measured
5.95/6.14/7.04 TWh; CT_PEAKER energy/CO2 recovers; C3a belly must NOT worsen
(the trim is evening-scoped); C1 12/12, overnight λ, C3c identical, C7/C8
PASS. Registered whatever the result (rule 15).

Usage: python scripts/probes/_caiso97_hodtrim_B.py
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
    out = ROOT / "caiso97_hodtrim_B"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-97 WP-2 -- caiso-94 keeper recipe + evening hod-trim of the "
        "daytime clean tranche (6-21 -> 6-17, trimmed-window depth, "
        "FINDING-caiso94 s7 pre-registered fix, owner TRIPPED ruling) + "
        "caiso_ra_startup_trajectory carried (owner ruling), 2023-2025"
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
        note=note,
    )
    print(f"DONE hod-trim B-leg -> {out}")


if __name__ == "__main__":
    main()
