"""caiso-102 B-leg: the caiso-101 KEEPER recipe on the +1h frame-defect fix.

The CAISO-102 evening merit-stack diagnosis found the model's 2025 solar
profile lagged one hour (model hod-18 = measured hod-17; cross-correlation
lag −1 r=0.9997 vs lag 0 r=0.9525), traced to
``eia_loader._eia_hourly_frame_filled`` anchoring the reconstructed year on
the HOUR-ENDING ``Local time`` stamp as if it were interval-beginning — every
gap-bridged BA-year (CISO-2025 8751 rows, PJM-2023, MISO-2025) came back one
hour late, rotating the model's whole exogenous 2025 world (solar/wind
profiles via the HSL parquet, the caiso-80 supply-consistent demand, runtime
interchange fallbacks) one hour late against the unrotated LMP actuals it is
scored on. Rule-14 measured-input defect — fix the root cause, never bury it.

RECIPE-IDENTICAL to `_caiso102_repro_A.py` (the caiso-101 keeper recipe; no
flag delta, no new mechanism). The A/B delta is the DATA/LOADER fix only:
  1. ``_eia_hourly_frame_filled`` interval-beginning anchor (eia_loader.py);
  2. rebuilt ``data/raw/caiso-hsl/caiso_2025_hsl_hourly.parquet``;
  3. re-derived ``caiso_supply_consistent_demand_2025.csv`` (rule 23: cites
     the loader defect, not a residual; 2023/2024 artifacts byte-identical).

Pre-registered gates (committed before adjudication, FINDING-caiso102 §6):
2023/2024 solve outputs BYTE-IDENTICAL to the A-leg (strict-path years must
not move); 2025 model solar hod profile aligns with measured at lag 0;
C1 holds 12/12; C7/C8 PASS. 2025 ladder/C3a/C3c/C5a movements are REPORTED,
not gated (the rotation realigns demand and supply simultaneously — no
directional prediction is honest). Registered whatever the result (rule 15).

Usage: python scripts/probes/_caiso102_hourfix_B.py
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
    overrides["caiso_storage_shape_anchor"] = True  # caiso-99 (the keeper delta)
    out = ROOT / "caiso102_hourfix_B"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-102 B-leg -- caiso-101 KEEPER recipe on the +1h "
        "_eia_hourly_frame_filled interval-beginning fix (rebuilt 2025 HSL "
        "profile + re-derived 2025 supply-consistent demand; 2023/2024 "
        "byte-identity pre-registered as a hard gate), 2023-2025"
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
    print(f"DONE caiso-102 B-leg -> {out}")


if __name__ == "__main__":
    sys.exit(main())
