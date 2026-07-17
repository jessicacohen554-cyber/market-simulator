"""caiso-93 probe: the OVERNIGHT clean import depth on the caiso-92 keeper recipe.

RECIPE-IDENTICAL to the caiso-92 keeper
(`scripts/probes/_caiso92_measured_offer_surface_ab.py` — the caiso-90 recipe
+ caiso_offer_surface_measured + caiso_offer_surface_conditional). The SINGLE
delta is ``caiso_dsw_overnight_clean=True`` (FINDING-caiso93-overnight-no-
wedge-2026-07-17; the FINDING-caiso92b §6 import-side redirect;
owner-authorized build 2026-07-17): the measured unconditional overnight
(hod 0-5) WEIM clean-transfer depth on the south corridor — p95 DSW net
import over ALL overnight hours, 5,870/6,205/6,487 MW (CV 0.041, LOYO
≤8.1%), net of the shaped firm block AND the caiso-87 surplus tranche,
measured-hub hours only (the 2023 Jan-Feb gap never arms), EF 0, priced at
the RAW measured Palo Verde hub with NO wheel (WEIM transfers pay no OATT
point-to-point charge; the measured overnight spread ≈ raw hub corroborates).
Zero fitted scalars.

MECHANISM (one import-side fix, both symptoms — rule 19): the model prices
every incremental overnight DSW MW at hub + the +$12-15 unspecified CARB
wedge — parity with domestic CC — so it serves the overnight residual with
CC where reality imports (FINDING-caiso92b: CC over-run +1.39/+2.11/+2.61
TWh ≈ import under-run −1.36/−1.70/−3.03). The measured record shows NO
wedge in 93-99% of ALL overnight hours (FINDING-caiso93 §2-3). Arming the
measured clean depth lets the LP substitute ~hub-parity imports for
wedge-parity CC ECONOMICALLY (a capability, not a floor — pmin 0, no D-2
row; fossil rungs unchanged beyond the depth; corridor ATC envelope still
caps delivered flow).

PRE-REGISTERED directions (BEFORE the solve; baselines = the caiso-92
keeper / same-machine caiso92_repro_A):
1. WHO SERVES THE NIGHT re-runs toward measured: overnight CC_REGULAR
   (model 15.16/14.76/13.78 vs CEMS 13.77/12.65/11.17 TWh) FALLS; overnight
   imports (model 10.03/9.87/10.30 vs measured 11.39/11.57/13.33) RISE.
2. The hod λ ladder: the overnight leg (+3.4/+1.8/+3.6) CLOSES toward 0 —
   the price, not just the volume. 2024 (+1.8) may slightly overshoot
   under raw-hub pricing (disclosed, FINDING-caiso93 §5); a material 2023/
   2025 overshoot (overnight λ going several $ UNDER) is a FAIL signal.
3. C3a 2024/2025 (+10.4/+14.3% baselines) must NOT inflate — expected
   direction is improvement (overnight over-price closes). The belly
   (hod 10-14) and evening legs are untouched by construction — watch.
4. C2 gas sign is the PRINCIPAL RISK GATE (2025 baseline −2.3%): displacing
   +1.4/+2.1/+2.6 TWh of overnight CC pushes total gas DOWN; a C2 flip
   names the OTHER half of the C1 cluster (CT_PEAKER/CHP under-runs), not a
   reason to bury the import fix (rules 1/14) — report, owner adjudicates.
5. C1: CC_REGULAR over-runs shrink toward the band; CT_PEAKER must not
   fall (its under-run is a different lane).
6. C3c (DA diagnostic + RT gate): the winter tail (Jan-13-2023 18 h) holds;
   no new tail on days the actual tail does not contain.
7. WATCH months (A-vs-B): Feb-2023 (hub-gap hours never arm — should be
   ~untouched), Apr-2023 (−4.2 baseline, must not deepen), Jan-2024 (~0),
   Sep-Dec-2025 (the CLOSED autumn lane: overnight hours only, the midday/
   evening autumn residual must not be touched).
FAIL conditions (pre-registered): a load-bearing gate flips PASS→FAIL
(C2 reported to the owner per #4), a WATCH month deepens materially, the
overnight λ overshoots materially UNDER in 2023/2025, or the depth is
measured inert — then the construction is re-examined against its own
evidence, never tuned to the residual.

Registered whatever the result (rule 15), all three years in one
invocation (rule 16), NO ablation twin (rule 21 as amended 2026-07-14).

Usage: python scripts/probes/_caiso93_overnight_clean_ab.py main
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "caiso65_seam_envelope_clock"


def main(mode: str) -> None:
    if mode != "main":
        raise SystemExit(
            "caiso-93 carries no ablation twin (rule 21 amended 2026-07-14); "
            "run with 'main'."
        )
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso93_overnight_clean"
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-92 keeper recipe, unchanged (same overrides stack as
    # _caiso92_measured_offer_surface_ab.py).
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True
    overrides["caiso_citygate_spot_level"] = True  # the caiso-84 keeper delta
    overrides["caiso_dsw_surplus_clean"] = True  # the caiso-87 keeper delta
    overrides["chp_steam_floor_p25"] = True  # the caiso-89 keeper delta
    overrides["caiso_citygate_flow_date"] = True  # the caiso-90 keeper delta
    # THE caiso-93 delta: the measured unconditional overnight clean depth.
    overrides["caiso_dsw_overnight_clean"] = True

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
        # from calibration_flags (caiso-69/70/73/74/75/76/77 script docstrings).
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
        # The caiso-92 keeper delta group (the measured DAM offer surface):
        # explicit kwargs, NOT prb_overrides (backcast_config runs the static
        # merge + rung split on these parameters).
        caiso_offer_surface_measured=True,
        caiso_offer_surface_conditional=True,
        note=(
            "caiso-93 overnight clean depth main -- caiso-92 keeper recipe "
            "(caiso-90 + measured DAM offer surface) + caiso_dsw_overnight_clean "
            "(measured unconditional overnight WEIM clean-transfer depth, "
            "hod 0-5, raw-hub no-wheel pricing, EF 0; "
            "FINDING-caiso93-overnight-no-wedge-2026-07-17, owner-authorized), "
            "2023-2025"
        ),
    )
    print(f"DONE main -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
