"""caiso-72 STEP-0 diagnostic: what serves SoCal evening load instead of CT?

Throwaway 2024-only solve on the caiso-70 MAIN recipe (caiso-65 keeper config
on the SP15-split topology, ``ct_netload_drag=False``,
``caiso_ra_bridge_startup_aware=True``) — NEVER registered on the dashboard
(rule 16: single-year solves are diagnostic probes only). Purpose: quantify,
from the persisted ``dispatch/2024_P1.parquet`` + ``flows.parquet`` +
``storage.parquet``, the SoCal (LA_BASIN + SDGE + SP15_rest) evening (h17-22)
supply stack by source and per-link import flows, in the hours reality runs
CT peakers (actual CT_PEAKER 5.24 TWh evening-loaded in 2024 vs model ~0.9).

Usage: python scripts/probes/_caiso72_step0_diag.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "caiso65_seam_envelope_clock"


def main() -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso72_step0_diag2024"
    out.mkdir(parents=True, exist_ok=True)

    # caiso-70 main recipe: startup-aware bridge via the generic override
    # channel (caiso-66 precedent), all other flags identical.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True

    solve_and_persist(
        [2024],  # DIAGNOSTIC ONLY — single train year, never registered
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
        # CAISO-specific structural flags carried by the keeper but absent
        # from calibration_flags (caiso-69/70 script docstrings).
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
            "caiso-72 STEP-0 diagnostic: 2024-only throwaway on the caiso-70 "
            "main recipe; SoCal evening supply-stack attribution. NOT for "
            "registration."
        ),
    )
    print(f"DONE -> {out}")


if __name__ == "__main__":
    main()
