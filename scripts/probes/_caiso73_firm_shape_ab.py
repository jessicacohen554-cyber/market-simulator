"""caiso-73 probe: measured shaped firm import base on the caiso-72 recipe.

Single-delta A/B against caiso-72 (`scripts/probes/_caiso72_hydro_envelope_ab.py`):
the caiso-65 keeper config on the SP15-split topology with
``ct_netload_drag=False``, ``caiso_ra_bridge_startup_aware=True`` and
``hydro_dispatch_envelope=True``, plus ONE change:
``caiso_firm_import_shape=True`` — the firm/contracted import blocks' hourly
availability shaped by the measured revealed import base. Year LEVEL = the
published DMM annual RA-import capacity × MIC corridor split
(interchange_config.IMPORT_TRANCHES_BY_YEAR: 2023 total 2,323 MW, 2024/25
3,371 MW — sources in that comment block); SHAPE = the unit-mean per-(month ×
hod) median of measured total CISO corridor net imports
(eia_loader.measured_firm_import_shape, EIA-930 per-DIBA extract on the model
clock). Mean(w)=1, so annual firm energy capability equals the DMM sizing —
the measured series contributes only the shape (rules #13/#14; no fitted
haircut; an hour-varying pmax the LP clears below, never a price adder).

Motivation (FINDING-caiso72-hydro-envelope live lead #1;
FINDING-caiso72-step0 channel #2, TTC-diagnosis Tier-2): with the hydro hoard
capped, the deep-evening import deficit is the largest remaining evening
supply-side miss. The caiso-73 STEP-0 re-measure on the caiso-72 recipe
(results/calibration/caiso73_step0_diag2024) confirms it: model evening
(h19-22) imports 3.2-3.6 GW vs measured 4.6-5.6 GW (deficit -1.4..-2.2 GW,
all on the DSW corridor: model WECC_DSW->SP15_rest 1.5-1.9 GW vs measured
2.7-4.7 GW), while midday over-imports +2.3 GW at h14. The flat 3.37 GW firm
block cannot represent the measured 5.3-6.3 GW overnight / 0.2-1.3 GW midday
/ 5.4-6.2 GW evening profile. Shaped (2024): ~5.0 GW overnight / 1.0-1.5 GW
midday / 4.2-4.9 GW deep evening.

Pre-registered directions (rubric v2.4, all three train years):
  - Deep-evening (h19-22) imports rise toward the measured level (from
    -1.4..-2.2 GW deficit); midday over-import falls (h14 +2.3 GW down).
  - Evening C3a price level eases; CC_REGULAR falls (C1 2024 +9.0 TWh is the
    target); C5a CO2 falls with it.
  - CT_PEAKER: direction AMBIGUOUS by design — DISCLOSED RISK: the added
    evening import supply may displace the CT the hydro envelope just
    recovered. If CT falls, that is attribution evidence for the
    battery/commitment channel (queue leads #2/#3), NOT a reason to haircut
    imports (rules #1/#14).
  - 2023: firm level drops to the year's own DMM measurement (2,323 vs the
    static 3,371 MW the per-hub node carried) — less midday firm, similar
    evening; the spurious 2023 system tail may move either way (disclosed;
    does not gate the mechanism, rule 1).

Registered as PROBES (main + zero-forcing ablation twin), never a keeper —
promotion is a separate owner decision after LOYO scoring (rule 22).

Usage: python scripts/probes/_caiso73_firm_shape_ab.py {main|ablation}
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
    out = ROOT / ("caiso73_firm_shape" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # caiso-72 recipe (startup-aware bridge + hydro envelope) + THE caiso-73
    # DELTA, all via the generic scenario-override channel (caiso-66/70/72
    # precedent).
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True

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
        ablation_of=(out.parent / "caiso73_firm_shape").name if ablate else None,
        note=(
            f"caiso-73 shaped firm import base {mode} -- caiso-72 recipe + "
            "caiso_firm_import_shape=True single delta, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
