"""caiso-102 A-leg: same-machine repro of the caiso-101 KEEPER (no new mechanism).

The CAISO-102 lane (the caiso-101 handoff's chartered successor — the
inelastic-charge derive + the evening merit-stack diagnosis) is DERIVE-FIRST:
its priority-2 question ("who serves the measured evening the model prices too
cheap") needs the CURRENT keeper's hourly dispatch, and the committed
`caiso101_wp3_B` bundle is slim (no dispatch parquets) while cross-machine
HiGHS spread is 0.5-1.2 TWh gas/yr (FINDING-caiso92b). So the decomposition
runs on a SAME-MACHINE repro of the promoted caiso-101 keeper recipe. This
script is that repro: RECIPE-IDENTICAL to `_caiso101_wp3_B.py main` (the
promoted keeper config — the caiso-99 keeper recipe on the WP-3
`steam_level_cf` artifact, which is committed and needs no re-derive), with
ONLY the output directory changed to the gitignored `caiso106_binding_2024`
(un-registered per the FINDING-caiso92b same-machine-baseline protocol;
`*_repro_A/` ignore rule).

No new mechanism, no flag delta, nothing registered — a baseline solve of the
existing keeper for the derive step (the owner-gate applies to NEW-mechanism
solves, not to reproducing the promoted keeper).

Usage: python scripts/probes/_caiso106_binding_2024.py
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
    out = ROOT / "caiso106_binding_2024"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-102 A-leg baseline -- caiso-101 KEEPER recipe repro (same-machine "
        "baseline for the CAISO-102 evening-merit + inelastic-charge derive "
        "steps; un-registered per the FINDING-caiso92b protocol), 2023-2025"
    )

    solve_and_persist(
        [2024],  # SINGLE-YEAR diagnostic (model-import binding check; un-registered)
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
    print(f"DONE caiso-102 A-leg repro -> {out}")


if __name__ == "__main__":
    main()
