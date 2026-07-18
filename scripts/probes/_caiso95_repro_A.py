"""caiso-95 A-leg: same-machine repro of the caiso-94 KEEPER (no new mechanism).

The CAISO-95 lane (the caiso-94 promotion's chartered successor — the C5a
CC-underproduction root-cause lane) is DERIVE-FIRST: before any new mechanism
is authorized, it needs a "who serves the DAY" decomposition of the CURRENT
keeper's dispatch against the metered fleet (CEMS/EIA-930). The committed
keeper bundle is slim (no dispatch parquets) and cross-machine HiGHS spread is
0.5-1.2 TWh gas/yr (FINDING-caiso92b), so the decomposition runs on a
SAME-MACHINE repro of the promoted caiso-94 keeper recipe. This script is that
repro: RECIPE-IDENTICAL to `_caiso94_daytime_clean_ab.py main` (the promoted
keeper config, `caiso_dsw_daytime_clean=True` included), with ONLY the output
directory changed to the gitignored `caiso95_repro_A` (un-registered per the
FINDING-caiso92b same-machine-baseline protocol; `*_repro_A/` ignore rule).

No new mechanism, no flag delta, nothing registered — a baseline solve of the
existing keeper for the derive step (the owner-gate applies to NEW-mechanism
solves, not to reproducing the promoted keeper).

Usage: python scripts/probes/_caiso95_repro_A.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
# Base calibration_flags source — the same source the caiso-93/94 probes read.
BASE = ROOT / "caiso65_seam_envelope_clock"


def _keeper_overrides(cf: dict) -> dict:
    """The caiso-94 KEEPER prb_overrides stack (recipe-identical)."""
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True
    overrides["caiso_citygate_spot_level"] = True  # caiso-84
    overrides["caiso_dsw_surplus_clean"] = True  # caiso-87
    overrides["chp_steam_floor_p25"] = True  # caiso-89
    overrides["caiso_citygate_flow_date"] = True  # caiso-90
    overrides["caiso_dsw_overnight_clean"] = True  # caiso-93
    overrides["caiso_dsw_daytime_clean"] = True  # caiso-94 (the keeper delta)
    return overrides


def main() -> None:
    cf = json.loads((BASE / "run_config.json").read_text())["calibration_flags"]
    overrides = _keeper_overrides(cf)
    out = ROOT / "caiso95_repro_A"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-95 A-leg baseline -- caiso-94 KEEPER recipe repro (same-machine "
        "baseline for the CAISO-95 who-serves-the-day derive step; "
        "un-registered per the FINDING-caiso92b protocol), 2023-2025"
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
    print(f"DONE repro -> {out}")


if __name__ == "__main__":
    main()
