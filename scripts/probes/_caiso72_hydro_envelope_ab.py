"""caiso-72 probe: measured hydro deliverability envelope on the caiso-70 recipe.

Single-delta A/B against caiso-70 (`scripts/probes/_caiso_g61b_decrowd_ab.py`):
the caiso-65 keeper config on the SP15-split topology with
``ct_netload_drag=False`` and ``caiso_ra_bridge_startup_aware=True``, plus ONE
change: ``hydro_dispatch_envelope=True`` — the hydro fleet's hourly dispatch
capped at the measured per-(month x hod) p95 of EIA-930 NG:WAT
(constants.HYDRO_ENVELOPE_PERCENTILE; eia_loader.measured_hydro_hourly_envelope).

Motivation (FINDING-caiso72-step0-evening-displacement-2026-07-10): the
evening CT gap is displaced by the budget LP's perfect-foresight hydro hoard
(+1.4-1.6 GW over measured water through h19-21, -1.3 GW under in the h15-16
ramp; model evening p95 exceeds measured p95 by 1-2+ GW in 9 of 12 months of
2024) — not by WECC imports (model under-imports the deep evening 1.4-2.2 GW).

Pre-registered directions (rubric v2.4, all three train years):
  - CT_PEAKER rises from ~0.9 toward actual 4.56/5.24/3.09 TWh, with the D-1
    profile advancing into the h15-18 ramp where the actual CT lives.
  - Evening (h17-22) model water p95 falls toward the measured p95.
  - C1 fuelmix / C2 sysvol / C4 dispatch-corr / C5a CO2 move together (the
    keeper signal); pocket over-price eases or is unchanged.
  - DISCLOSED RISK: 2023 (wet year, spurious 540 h system tail) may see the
    tail worsen — the envelope removes ~1.5 GW of evening supply there too.
    Per rule 1 this does NOT gate the mechanism; a worsened 2023 tail is the
    existing system-scarcity root cause, to be chased, not buried.

Registered as PROBES (main + zero-forcing ablation twin), never a keeper —
promotion is a separate owner decision after LOYO scoring (rule 22).

Usage: python scripts/probes/_caiso72_hydro_envelope_ab.py {main|ablation}
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
    out = ROOT / ("caiso72_hydro_envelope" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # caiso-70 recipe (startup-aware bridge) + THE caiso-72 DELTA, both via
    # the generic scenario-override channel (caiso-66/70 precedent).
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True

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
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "caiso72_hydro_envelope").name if ablate else None,
        note=(
            f"caiso-72 hydro deliverability envelope {mode} -- caiso-70 "
            "recipe + hydro_dispatch_envelope=True single delta, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
