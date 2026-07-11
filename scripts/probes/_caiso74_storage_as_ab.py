"""caiso-74 probe: measured battery AS-award reservation on the caiso-73 recipe.

Single-delta A/B against caiso-73 (`scripts/probes/_caiso73_firm_shape_ab.py`):
the caiso-65 keeper config on the SP15-split topology with
``ct_netload_drag=False``, ``caiso_ra_bridge_startup_aware=True``,
``hydro_dispatch_envelope=True`` and ``caiso_firm_import_shape=True``, plus ONE
change: ``caiso_storage_as_reservation=True`` — the measured CAISO battery
AS-award MW reserved out of the battery fleet's dispatch headroom
(model/storage.reserve_caiso_storage_as_power + caiso_storage_as_soc_min;
data = the CAISO Daily Energy Storage Report quarterly series curated to the
``storage-as-awards`` clean datatype; DA/IFM LESR awards: total 1,010/1,484/
1,652 MW avg 2023/24/25, matching the DMM-published 1,040/1,500 MW to ~1 %).
Two legs: (a) upward award (reg-up+spin+non-spin; peaks 1.2-1.5 GW h12-16 in
2024/25) subtracted from battery power pro-rata — the exact ERCOT
storage_as_commitment pattern; (b) SOC floored at the tariff 30-min sustain of
the spin/non-spin award (CAISO_AS_SUSTAIN_DURATION_H = 0.5 h, the reserve
co-opt's own constant). ZERO new fitted parameters (rule 23).

Motivation (FINDING-caiso72-step0 channel #1; FINDING-caiso73 live lead #1):
LP perfect-foresight batteries discharge h15-17 (real fleet still charging /
AS-committed) and h21-23 (real fleet SOC-spent), covering ~2.1-2.5 GW of the
deep-evening hours reality serves with gas+imports. The honest mechanism is
rule 13's own worked example — a measured AS power reservation.

Pre-registered directions (rubric v2.4, all three train years):
  - CT_PEAKER rises toward actual (4.56/5.24/3.09 TWh): the reserved battery
    power (largest exactly in the h12-17 award peak) can no longer serve the
    afternoon ramp the real fleet meets with CT.
  - Battery dispatch shape moves toward measured: phantom h15-17 discharge
    falls; the h21-23 over-stretch falls (power + SOC-sustain legs); C5b
    storage throughput falls toward actual.
  - 2023 effect weaker than 2024/25 by construction (award mean 439 vs
    741/842 MW) — directionally identical.
  - DISCLOSED RISK: C3a mean-LMP may RISE, especially evenings, as withheld
    battery supply re-prices the top hours (the award is real market
    structure; a structurally-real mechanism stays in whatever the residual
    does — rule 1).
  - DISCLOSED AMBIGUITY: evening CC may pick up displaced battery energy, so
    CC_REGULAR (C1 2024 +7.64 TWh) may move either way.

Registered as PROBES (main + zero-forcing ablation twin), never a keeper —
promotion is a separate decision per the session's pre-authorized conditions.
Both reservation legs are measured capability bounds, so they survive the
zero-forcing ablation by construction (the caiso-72/73 envelope precedent).

Usage: python scripts/probes/_caiso74_storage_as_ab.py {main|ablation}
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
    out = ROOT / ("caiso74_storage_as" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # caiso-73 recipe (startup-aware bridge + hydro envelope + firm import
    # shape) + THE caiso-74 DELTA, all via the generic scenario-override
    # channel (caiso-66/70/72/73 precedent).
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_storage_as_reservation"] = True

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
        # from calibration_flags (caiso-69/70/73 script docstrings).
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
        ablation_of=(out.parent / "caiso74_storage_as").name if ablate else None,
        note=(
            f"caiso-74 measured battery AS-award reservation {mode} -- "
            "caiso-73 recipe + caiso_storage_as_reservation=True single "
            "delta, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
