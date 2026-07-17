"""caiso-94 probe: the DAYTIME trigger-OFF clean import depth on the caiso-93 keeper recipe.

RECIPE-IDENTICAL to the caiso-93 KEEPER (`_caiso93_overnight_clean_ab.py` — the
caiso-92 recipe + caiso_dsw_overnight_clean). The SINGLE delta in ``main`` is
``caiso_dsw_daytime_clean=True`` (FINDING-caiso94-daytime-wedge-2026-07-17; the
C3a-2025 daytime lane; owner-authorized diagnostic build 2026-07-17): the
measured DAYTIME trigger-OFF (hod 6-21) WEIM clean-transfer depth on the south
corridor — p95 DSW net import over the daytime trigger-OFF window,
5,441/5,762/5,998 MW (CV 0.040, LOYO ≤8.1%), net of the shaped firm block AND
the caiso-87 surplus tranche AND the caiso-93 overnight tranche, measured-hub
trigger-OFF hours only (the 2023 Jan-Feb gap never arms; caiso-87 trigger-ON
hours never arm — disjoint from caiso-87), EF 0, priced at the RAW measured
Palo Verde hub with NO wheel. Zero fitted scalars.

DIAGNOSTIC, not a keeper build (owner framing 2026-07-17): the derive-first gate
(FINDING-caiso94) proved the measured no-wedge structure that admitted caiso-93
overnight extends to the daytime — ADMISSIBILITY only. This solve settles the
two open questions the gate cannot: does the model actually over-price these
trigger-OFF daytime hours (INERTNESS risk, à la caiso-86 partial-ladder), and
does the total-flow depth OVERSHOOT (push daytime λ below actual)?

The A-leg (baseline) is the SAME-MACHINE caiso-93 keeper repro (``repro`` mode →
caiso94_repro_A), NOT the committed keeper bundle (cross-machine HiGHS spread
0.5-1.2 TWh gas/yr). Run the two legs SEQUENTIALLY (this 15 GB box OOMs on two
concurrent CAISO 3-year solves).

PRE-REGISTERED directions (BEFORE the solve; baselines = the caiso-93 keeper /
same-machine caiso94_repro_A):
1. C3a-2025 (+13.3% keeper) must fall toward the ≤10% band WITHOUT 2023
   (+5.6-class) or 2024 (+9.5, freshly passing) regressing over the line.
2. The hod λ ladder: the belly (hod 10-14, +11.6/+10.2/+8.9) and the AUTUMN
   daytime should FALL; the overnight leg (+1.9/+0.4/+1.9) must HOLD (protected
   caiso-93 result); the non-autumn EVENING (−5.8/−4.1/−1.2, model under) must
   NOT deepen materially (the overshoot watch — a clean import there could push
   λ further under; raw-hub pricing self-scopes, but WATCH).
3. C1 grid MUST stay 12/12 (protected caiso-93 result): CC_REGULAR
   −0.30/+2.30/−0.47 and CT/CHP/ST byte-class baselines must not degrade.
4. WHO SERVES THE NIGHT: the overnight shares (51/49/47%) must HOLD (the daytime
   leg is disjoint from overnight by construction).
5. C2 gas sign (2025 diagnostic −7.9%): displacing daytime CC pushes gas DOWN
   further — report, owner adjudicates (rules 1/14; a flip names the CT/CHP
   under-run half, not a reason to bury the import fix).
6. C3c (DA diagnostic + RT gate): the winter tail (Jan-13-2023 19 h) holds; no
   new tail on days the actual tail does not contain.
7. WATCH months: Feb-2023 (+5.1, hub-gap protected), Apr-2023 (−3.2, must not
   deepen), Jan-2024 (−0.5), May/Jun-2023/24, Sep-Dec-2025 (the TARGET autumn
   daytime — should improve).
FAIL/redirect conditions (pre-registered): the depth is measured INERT (model
already prices daytime-OFF near actual → the C3a-2025 residual is model-side,
not the import wedge — a legitimate finding, not tuned away); the daytime λ
OVERSHOOTS materially UNDER; C1 drops below 12/12 or the overnight λ closure
degrades (protected results) → the construction is re-examined against its own
evidence, never tuned to the residual.

Registered whatever the result (rule 15), all three years in one invocation
(rule 16), NO ablation twin (rule 21 as amended 2026-07-14).

Usage:
  python scripts/probes/_caiso94_daytime_clean_ab.py repro   # A-leg baseline (run FIRST)
  python scripts/probes/_caiso94_daytime_clean_ab.py main    # B-leg (daytime on)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
# Base calibration_flags source (coal sigmoids, offer curves, etc.) — the same
# source the caiso-93 keeper probe reads; the keeper recipe is rebuilt by the
# explicit overrides below.
BASE = ROOT / "caiso65_seam_envelope_clock"


def _keeper_overrides(cf: dict) -> dict:
    """The caiso-93 keeper prb_overrides stack (recipe-identical)."""
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
    overrides["caiso_dsw_overnight_clean"] = True  # caiso-93 (the keeper delta)
    return overrides


def main(mode: str) -> None:
    if mode not in ("main", "repro"):
        raise SystemExit("run with 'repro' (A-leg baseline) or 'main' (B-leg).")
    cf = json.loads((BASE / "run_config.json").read_text())["calibration_flags"]
    overrides = _keeper_overrides(cf)

    if mode == "main":
        # THE caiso-94 delta: the measured daytime trigger-OFF clean depth.
        overrides["caiso_dsw_daytime_clean"] = True
        out = ROOT / "caiso94_daytime_clean"
        note = (
            "caiso-94 daytime clean depth main -- caiso-93 keeper recipe + "
            "caiso_dsw_daytime_clean (measured daytime trigger-OFF WEIM "
            "clean-transfer depth, hod 6-21, raw-hub no-wheel pricing, EF 0, "
            "net of firm + caiso-87 surplus + caiso-93 overnight; "
            "FINDING-caiso94-daytime-wedge-2026-07-17, owner-authorized "
            "DIAGNOSTIC), 2023-2025"
        )
    else:  # repro — the same-machine caiso-93 keeper A-leg baseline
        out = ROOT / "caiso94_repro_A"
        note = (
            "caiso-94 A-leg baseline -- caiso-93 keeper recipe repro "
            "(same-machine baseline for the caiso-94 daytime A/B; "
            "un-registered per the FINDING-caiso92b protocol), 2023-2025"
        )
    out.mkdir(parents=True, exist_ok=True)

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
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
