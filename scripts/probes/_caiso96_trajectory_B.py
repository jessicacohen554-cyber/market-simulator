"""caiso-96 B-leg: the caiso-94 keeper recipe + the CC startup-trajectory extension.

WP-1 of the caiso-95 finding's chartered successor lane
(FINDING-caiso95-who-serves-the-day-2026-07-18.md §7): the metered CAISO CC
fleet re-commits its evening capacity through the EARLY afternoon (measured
run-starts peak hod 13-15) while the model's starts land ~3 h late (peak
17-18) — the whole hod 13-17 CC online-capacity deficit. This leg arms
``caiso_ra_startup_trajectory`` (the P1-native RA must-offer bridge's
startup-trajectory extension — same mechanism, wider physics, rule 19) on top
of the OTHERWISE RECIPE-IDENTICAL caiso-94 keeper config: every detected
run-start of a bridge-eligible merchant CC is preceded by its measured CAMPD
start-to-load ramp (per-plant p50, frozen CV/LOYO gates —
``scripts/derive_campd_cc_start_trajectory.py``).

Adjudicated A/B against the same-machine caiso-94 keeper repro
(``_caiso95_repro_A.py`` → ``caiso95_repro_A``; cross-machine HiGHS spread
0.5-1.2 TWh gas/yr, so the committed bundle is never the baseline —
FINDING-caiso92b protocol). Pre-registered report-back (caiso-96 charter):
C5a all 3 years; C1 grid holds 12/12; the caiso-93 overnight λ + share hold;
C3a belly hod 10-14 does NOT materially fall; evening hod 17-21 λ must not
deepen; C3c winter tail identical; C7/C8 pass; who-serves-day hod 13-17
online-cap gap closes and the starts histogram shifts toward 13-15.

Usage: python scripts/probes/_caiso96_trajectory_B.py
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
    overrides["caiso_ra_startup_trajectory"] = True  # caiso-96 (the WP-1 delta)
    out = ROOT / "caiso96_startup_trajectory"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-96 WP-1 -- caiso-94 keeper recipe + caiso_ra_startup_trajectory "
        "(measured CC start-to-load ramp-in on the RA bridge's own detected "
        "run-starts; CAMPD per-plant p50, frozen gates), 2023-2025"
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
    print(f"DONE trajectory B-leg -> {out}")


if __name__ == "__main__":
    main()
