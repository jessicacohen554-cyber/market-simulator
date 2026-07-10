"""caiso-70 probe: G-61b startup-aware RA-bridge de-crowding on the SP15 split.

Single-delta A/B against the caiso-69 SP15-split probe
(scripts/probes/_caiso_sp15split_ab.py): same recipe -- the caiso-68 recipe
(caiso65_seam_envelope_clock keeper config + ``temp_dependent_derate=True``,
owner default) on the LA_BASIN/SDGE/SP15_rest split topology with
``ct_netload_drag=False`` as the per-run override -- plus ONE change:
``caiso_ra_bridge_startup_aware=True`` (gap G-61 path (b), the
startup-aware P0 run detection that drops phantom micro-run bridging;
measured -38 to -43% RA-bridge forced energy on caiso-63/66).

Why re-test a mechanism that was held back (caiso-66): the hold-back
rationale -- "the belly wants MORE committed gas" (seam-tz FINDING §4.3,
belly-commitment probe item 3) -- predates both the SP15 split topology and
the caiso-69 crowding-out evidence. caiso-69's zero-forcing ablation clears
MORE CT_PEAKER than its main run (2.02/1.41/0.98 vs 0.90/0.91/0.79 TWh):
the un-gated RA bridge's forced CC min-gen (~3.2-3.8 TWh at
min_load_frac 0.26 across the midday gap) occupies the pocket energy
balance and crowds peakers out of the very pockets whose import-limited
links should call them. The A/B question: does releasing the phantom
share of that forced CC let pocket CTs clear on merit (toward actual
4.56/5.24/3.09 TWh) without re-arming the drag?

Pre-registered directions (scored vs caiso-69 main and its ablation):
CT_PEAKER up from 0.79-0.94 TWh toward the ablation's 2.02/1.41/0.98
(bounded by it -- the ablation removes ALL forcing incl. this bridge, so
it is the ceiling of what de-crowding alone can release); CC_REGULAR down;
belly lambda moves TOWARD measured $13-33 or at worst the caiso-66
+$0.30-0.46 away (the disclosed tension -- if the belly lambda degrades
materially while CT recovers, the result adjudicates crowding-out vs
belly-posture as separable phenomena, which is the point of the probe).

Flag plumbing: ``caiso_ra_bridge_startup_aware`` is not a
``solve_and_persist`` kwarg; it rides the generic ``prb_overrides``
scenario-override channel, exactly as the registered caiso-66 run did
(its run_config.json carries it inside ``coal_prb_sigmoid_overrides``).
All other keeper-specific structural flags are passed explicitly per the
caiso-69 script's docstring (several are NOT in calibration_flags and
would silently drop from a bare replay).

Registered as a PROBE (caiso-70), never a keeper -- promotion is a
separate owner decision after LOYO scoring within 2023-2025 (rule 22).

Usage: python scripts/probes/_caiso_g61b_decrowd_ab.py {main|ablation}
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
    out = ROOT / ("caiso70_g61b_decrowd" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # THE A/B DELTA vs caiso-69: startup-aware bridge run detection, via the
    # generic scenario-override channel (caiso-66 precedent).
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True

    solve_and_persist(
        cf["years"],  # all three years in one call (rule 16) -- not [year]
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
        # from calibration_flags -- see the caiso-69 script's docstring.
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
        # Carried from caiso-69: drag off, per-run override only (the
        # backcast_config CAISO default stays ON -- scope doc Phase 2).
        ct_netload_drag=False,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "caiso70_g61b_decrowd").name if ablate else None,
        note=(
            f"G-61b de-crowding {mode} -- caiso-69 recipe (SP15-split "
            "topology, ct_netload_drag=False) + "
            "caiso_ra_bridge_startup_aware=True single delta, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
