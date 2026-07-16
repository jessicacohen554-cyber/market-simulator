"""caiso-89 probe: flat-CHP steam-host operating-level floor on the caiso-87 keeper recipe.

RECIPE-IDENTICAL to the caiso-87 keeper
(`scripts/probes/_caiso87_dsw_surplus_clean_ab.py` — the caiso-84 recipe +
``caiso_dsw_surplus_clean``). The single delta is ``chp_steam_floor_p25=
True``: the measured multi-year steam-host OPERATING level for CHP cogens
(Lane C / C4-shape, 2026-07-16 handoff). Measured CEMS: the real CAISO CC_CHP
steam fleet runs FLAT 0.65-0.76 GW net across all 24 hod (May-2023, hod
max/min 1.16 — host steam physics), while the keeper's CC_CHP ducks to
~0.06 GW midday / 0.8 GW evening because the p2 "never-below" statistic
behind ``chp_pmin_cf`` reads 0.0 for every flat host that takes a few
non-outage offline hours (MECH_CHP_STEAM forces only ~0.02 GW avg, D-2
share_of_class 2.3-3.3%).

Mechanism: the artifact's new ``p25_allhr_cf`` (all-hours p25 of CAMPD
available-CF, pooled 2023-2025 by the frozen derive_thermal_tranches
estimator — outage hours drop from the sample, economic-offline hours count
as zeros) replaces the p2 level in the SAME grid floor formula
``pmin_cf x (1 - btm_share)`` with the SAME MECH_CHP_STEAM attribution
(rule 19 level swap, no new mechanism). The statistic self-targets: only the
flat merchant hosts survive (Midway-Sunset 55217 -> 75.0%, Elk Hills 55400 ->
81.5%, THUMS 50865 CT_CHP -> 90.9%); every cycling cogen measures 0.0 and
keeps its p2/eia923_cf floor (the CT_CHP fleet's online-p25 alternative was
audited and REJECTED: it would force 1.77 vs 0.38-0.41 TWh actual — a
rule-17 off-window bug by the class's own evidence). Estimation-stage
cross-year stability: class per-year CV 0.056, LOYO worst 9.1% (inside the
CV<=0.20 / LOYO<=25% gates that closed FINDING-caiso88). Grid floor delta
~570 MW flat (272 + 278 + 19.5), availability-clipped so measured outage
windows (incl. the Oct-Dec-2025 gas outages) still relax it.

PRE-REGISTERED directions (BEFORE the solve):
1. C4 gas hourly-shape improves (the lane target): 2023 r .824 / NRMSE .330
   and 2025 r .851 / .302 move toward actual as CC_CHP stops ducking; the
   May-2023 overnight composition narrows ~0.6 GW.
2. C1 CHP rows hold (annual energy roughly pinned): floor-implied class
   energy sits UNDER actual every year (CC_CHP 6.6/5.4/5.4 floor vs
   7.5/6.0/6.1 TWh CEMS actual); 2025 CC_CHP (-1.1 TWh under in the keeper)
   narrows. C1-2024 CC_REGULAR (+6.01 TWh) likely narrows — the forced CHP
   base displaces economic CC_REGULAR trough dispatch.
3. C3a ~flat (imports are marginal in the soft-month troughs; this is a
   structural-fidelity lever, rule 1 — do NOT reject it for a flat C3a).
   C2 2025 gas (-2.3%) moves toward zero (more CHP gas burn in troughs, but
   partially offset by CC_REGULAR displacement).
4. C3b/C3c ~unchanged (the floor binds in troughs, not tight hours).
5. WATCH: Apr-2023 (-4.2) / Jan-2024 (-4.8) must not deepen materially;
   Jan/Feb-2023 winter untouched (floor is price-passive base gas).
FAIL conditions (pre-registered): a load-bearing gate flips PASS->FAIL, the
WATCH months deepen materially, or D-4 shows the floor binding against its
own driver evidence — then the construction is re-examined against its own
gates, never tuned to the residual.

LOYO note: the level is pooled 2023-2025 (multi-year conditioning is the
rule-13 requirement — never same-year pinning); the estimation-stage
CV/LOYO gates above are the cross-year transfer check (caiso-80/82/84/87
precedent).

Registered as a PROBE, all three years in one invocation (rule 16), NO
zero-forcing ablation twin (rule 21 as amended 2026-07-14).

Usage: python scripts/probes/_caiso89_chp_steam_floor_ab.py main
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
            "caiso-89 carries no ablation twin (rule 21 amended 2026-07-14); "
            "run with 'main'."
        )
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso89_chp_steam_floor"
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-87 keeper recipe, unchanged, plus the SINGLE caiso-89 delta:
    # the measured multi-year CHP steam-host operating-level floor.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True
    overrides["caiso_citygate_spot_level"] = True  # the caiso-84 keeper delta
    overrides["caiso_dsw_surplus_clean"] = True  # the caiso-87 keeper delta
    overrides["chp_steam_floor_p25"] = True  # THE caiso-89 delta

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
        note=(
            "caiso-89 chp steam-host floor main -- caiso-87 keeper recipe + "
            "chp_steam_floor_p25=True (measured multi-year all-hours-p25 "
            "steam-host operating level, MECH_CHP_STEAM level swap; Lane C "
            "2026-07-16 handoff), 2023-2025"
        ),
    )
    print(f"DONE main -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
