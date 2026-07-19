"""caiso-100 B-leg: caiso-99 keeper recipe + the DERIVED battery cycling cost.

Owner-GRANTED 2026-07-19 (ask `docs/handoffs/caiso-100-charge-econ-ask-2026-07-19.md`,
re-opening the caiso-76 no-change ruling on moved evidence). The ONLY delta vs
the same-machine `_caiso100_repro_A.py` baseline is
``battery_dispatch_adder = 14.25`` — the DERIVED li-ion cycling-degradation
cost per MWh discharged (NREL ATB 2024 capex $285/kWh x 1000 / 5,000 LFP
warranty cycles x 0.25 replacement fraction — the identical
`storage._degradation_cost_per_mwh` construction the storage entry screen
already prices, `constants.py:4128`). NOT a tuned value: no sweep, no residual
fit (rule 25); ERCOT's tuned $10 does not cross the ISO boundary (rule 25).

Mechanism (FINDING-caiso100 §3-§5): the zero-cost LP's charge bid is nearly its
full evening-implied value, so charging rides up the supply curve to a
charge-weighted lambda $5.8-12.2 above the measured glut floor where the real
fleet buys the SAME volume; the fleet's revealed margin conduct cost
($11-17/MWh) brackets the derived $14.25, while the keeper's own margin prices
only its efficiency-loss floor (c* ~ $7). A per-MWh throughput cost lowers the
bid so charging clears at the floor. CAISO's own DEB design prices exactly this
term (DMM 2024 Eq 2.11.1 rho).

Pre-registered gates (FINDING-caiso100 §6, BINDING): belly falls all years, no
overshoot; evening toward 0, no cross, 2025 evening dis within 0.3 TWh of
measured; two-sided +-15 % battery-only NG:OTH throughput guard + belly chg >=
measured belly; C1 12/12; overnight no new under-price; C3c unchanged/toward
tail; C7/C8 PASS; C5a improves/holds. Registered whatever the result (rule 15);
promotion only on no-status-regression.

Usage: python scripts/probes/_caiso100_cycling_B.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _caiso95_repro_A import BASE, _keeper_overrides  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"

# The DERIVED cycling-degradation cost, $/MWh discharged (FINDING-caiso100 §3;
# storage._degradation_cost_per_mwh construction, constants.py:4128). Rule 25:
# derived, never swept.
CYCLING_COST_DERIVED = 14.25


def main() -> None:
    cf = json.loads((BASE / "run_config.json").read_text())["calibration_flags"]
    overrides = _keeper_overrides(cf)
    overrides["caiso_ra_startup_trajectory"] = True  # caiso-96 (owner carry ruling)
    overrides["caiso_dsw_daytime_evening_trim"] = True  # caiso-97 (the WP-2 delta)
    overrides["caiso_storage_shape_anchor"] = True  # caiso-99 (the keeper delta)
    overrides["battery_dispatch_adder"] = (
        CYCLING_COST_DERIVED  # caiso-100 (the ONLY delta vs _caiso100_repro_A)
    )
    out = ROOT / "caiso100_cycling_B"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-100 B-leg -- caiso-99 KEEPER recipe + battery_dispatch_adder=14.25 "
        "(DERIVED li-ion cycling-degradation cost per MWh discharged, NREL ATB "
        "2024 capex / 5000 LFP cycles x 0.25 replacement; owner-granted "
        "2026-07-19, FINDING-caiso100 s6 pre-registered gates), 2023-2025"
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
    print(f"DONE caiso-100 cycling B-leg -> {out}")


if __name__ == "__main__":
    main()
