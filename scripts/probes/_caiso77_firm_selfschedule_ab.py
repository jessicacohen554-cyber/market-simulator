"""caiso-77 probe: self-scheduled firm import base on the caiso-76 recipe.

Single-delta A/B against the caiso-76 keeper
(`scripts/probes/_caiso76_hydro_budget_ab.py`): the caiso-75 recipe plus the
measured hydro budget correction (``hydro_backfill_year=2024`` +
``hydro_eia930_monthly=True``), plus ONE mechanism:
``caiso_firm_import_selfschedule=True`` — the firm/contracted import blocks
become must-flow at their shaped capability
(FINDING-caiso77-c1-cluster-firm-selfschedule-2026-07-11.md).

THE TARGET is the C1 CC-over/CT-under cluster (CC_REGULAR +5.05/+7.04 TWh
over in 2023/24; same-fleet CAMPD +6.2/+11.2/+14.3 TWh across 2023-25,
concentrated overnight and the summer morning shoulder, while CT_PEAKER
under-runs the evening ramp). D-2 attribution shows the CC flatness is
ECONOMIC, and its counterpart is the price-gated contracted import base:
the firm tranches carry the measured caiso-73 shape and the published DMM
RA-import x MIC-split level but are priced at two G-26 static-fitted Tier-3
contract-cost proxies ($28/$48), so any hour the model LMP sits below the
proxy the LP leaves the contracted base untaken and runs CC flat instead —
the model under-imports the overnight/evening base 0.6-2.3 GW against the
revealed 4.3-5.9 GW self-scheduled plateau (gap register G-15(b)).

In the real market these blocks are self-scheduled or bid at/below $0/MWh
(CPUC D.20-06-028 RA import must-offer) and flow independent of the hourly
spot spread. The delta floors each firm tranche's hourly min_gen at its FULL
shaped capability (pmax x availability; MECH_FIRM_IMPORT — a contract,
ablation-kept, D-2 exempt), the exact Manitoba/HQ firm must-flow pattern.
ZERO new free parameters: level and shape are the keeper's existing measured
inputs; the two static-fitted firm prices stop influencing dispatch (at
pmin = pmax they never set the margin).

Pre-registered directions (rubric v2.4, all three train years — full list
in the FINDING S4):
  - 2023/24: overnight/evening imports rise toward the measured base;
    CC_REGULAR falls toward the C1 band; C4 gas r rises; C7/C8 hold.
  - CT_PEAKER flat-to-slightly-up (the bridge-crowding channel is untouched
    — lead (c) stays open).
  - 2025: CC_REGULAR falls toward the CEMS truth (+14.3 over same-fleet).
    DISCLOSED: the C2 family metric (-4.1% CAVEAT) may print further
    negative on the current bench basis, which is itself inconsistent with
    same-year CEMS for 2025 (FINDING S2 cross-basis note; bench rework is
    the session's Task 2/3). Rules 1/14: the measured mechanism stays in
    regardless; a C2-2025 move on a suspect basis is adjudicated against
    the CEMS same-fleet evidence.
  - Annual imports: net movement AMBIGUOUS (disclosed) — the corridor ATC
    envelopes and the MIC simultaneous-import cap still bound delivered
    flow; midday firm capability stays at the measured shape's own collapse.

Registered as PROBES (main + zero-forcing ablation twin; the firm-import
floor is a contract and survives the ablation by construction, like the
Manitoba/HQ blocks).

Usage: python scripts/probes/_caiso77_firm_selfschedule_ab.py {main|ablation}
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
    out = ROOT / ("caiso77_firm_selfschedule" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # caiso-76 recipe (caiso-75 structural flags via the generic
    # scenario-override channel + the measured hydro budget kwargs), plus THE
    # caiso-77 delta: caiso_firm_import_selfschedule=True.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True  # THE caiso-77 DELTA

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
        # Standing measured hydro budget correction (caiso-76, rules 1/14).
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
        # CAISO-specific structural flags carried by the keeper but absent
        # from calibration_flags (caiso-69/70/73/74/75/76 script docstrings).
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
        ablation_of=(out.parent / "caiso77_firm_selfschedule").name if ablate else None,
        note=(
            f"caiso-77 self-scheduled firm import base {mode} -- "
            "caiso-76 recipe + caiso_firm_import_selfschedule=True single "
            "delta, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
