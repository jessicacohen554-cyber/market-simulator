"""caiso-75 probe: measured 2023 demand-clock realignment on the caiso-73 recipe.

Single-delta A/B against caiso-73 (`scripts/probes/_caiso73_firm_shape_ab.py`):
the caiso-65 keeper config on the SP15-split topology with
``ct_netload_drag=False``, ``caiso_ra_bridge_startup_aware=True``,
``hydro_dispatch_envelope=True`` and ``caiso_firm_import_shape=True``, plus ONE
change: ``caiso_demand_clock_realign=True`` — the measured source-data clock
correction to the CAISO demand input
(FINDING-caiso75-demand-clock-2026-07-11.md): the EIA-930 CISO `Demand`
column rides +1 h LATE vs the extract's own wall-true generation frame for
local dates before 2023-11-01 (monthly best-lag −1 at r 0.984-0.997 against
the extract's balance identity; the OASIS SLD TAC actual corroborates at
0.9953), then flips to aligned. Rule-14 reconciled real data: a clock fix
derived only from the source series' internal identity — annual energy
conserved to +0.1 MW on the mean, no level rescale, zero fitted parameters
(guard: scripts/validate_caiso_demand_clock.py).

NOTE: caiso_storage_as_reservation (caiso-74) is NOT carried: the caiso-74
probe measured it ex-ante inert on the zone-aggregate battery fleet (LP
discharge peaks 3.7-6 GW below the nameplate cap, so the 0.7-2.8 GW award
derate never binds — dispatch identical to caiso-73 to 0.01 TWh). The
caiso-71 locational-AS precedent applies: available, documented, default-off.

Pre-registered directions (rubric v2.4, all three train years; §3 of the
FINDING):
  - 2023 ONLY — 2024/2025 byte-identical by construction (window ends
    2023-11-01).
  - The 2023 evening ramp re-overlaps the last solar hours → the spurious
    2023 system tail (480 h > $200 zonal-max vs 21 RT actual) FALLS;
    C3a-2023 (+23.5 %) eases.
  - 2023 CT/CC afternoon dispatch shifts ~1 h earlier with the ramp;
    CT_PEAKER 2023 volume direction AMBIGUOUS (disclosed); D-1 shape holds
    or improves.
  - C5a-2023 CO2 (+7.1 % CAVEAT) follows gas volume — ambiguous, disclosed.
  - DISCLOSED RISK: the 2023 tail may not close fully (other caiso-49-era
    drivers open); a partial move keeps the fix in regardless (rule 14).

Registered as PROBES (main + zero-forcing ablation twin), never a keeper —
promotion per the session's pre-authorized conditions is evaluated after
scoring. The clock fix is a measured input correction and survives the
zero-forcing ablation by construction.

Usage: python scripts/probes/_caiso75_demand_clock_ab.py {main|ablation}
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
    out = ROOT / ("caiso75_demand_clock" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # caiso-73 recipe (startup-aware bridge + hydro envelope + firm import
    # shape) + THE caiso-75 DELTA, all via the generic scenario-override
    # channel (caiso-66/70/72/73/74 precedent).
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True

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
        # from calibration_flags (caiso-69/70/73/74 script docstrings).
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
        ablation_of=(out.parent / "caiso75_demand_clock").name if ablate else None,
        note=(
            f"caiso-75 measured 2023 demand-clock realignment {mode} -- "
            "caiso-73 recipe + caiso_demand_clock_realign=True single "
            "delta, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
