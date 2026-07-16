"""caiso-91 probe: online-scoped reserve co-optimization on the caiso-90 keeper recipe.

RECIPE-IDENTICAL to the caiso-90 keeper
(`scripts/probes/_caiso90_citygate_flow_date_ab.py` — the caiso-89 recipe +
``caiso_citygate_flow_date``). The single structural delta is the CAISO
energy+reserve co-optimization with online-quality scoping (the issue-#1492
"correct build" — C1 CC-over/CT-under lane, owner directive 2026-07-16,
`docs/DIAGNOSIS-caiso-evening-merit-c1-c3c-2026-07.md` §5.1):

* ``energy_reserve_coopt=True`` + ``caiso_reserve_coopt=True`` — the
  per-generator spin/non-spin contingency co-opt (BAL-002-WECC-3 requirement
  = max(fleet MSSC, 6% load); tariff §27.1.2.3.5 scarcity demand curves;
  pergen (zone, fuel-class) R pools with the 10-min deliverable-ramp bound;
  storage RS at the 30-min ASSOC sustain; hydro at governor-physics ramp).
  Alone this is caiso-59's measured-INERT structure (12.9 GW deliverable
  ramp vs ~2.2 GW requirement, cleared from idle CC at zero opportunity
  cost).
* ``caiso_reserve_online_scoped=True`` — THE increment that makes it bite:
  each pool splits into a SPIN column (ONLINE 10-minute ramp only — spinning
  reserve is synchronized capacity, tariff §8.4/App. K; online pattern from
  the model's own P0 run pattern at the P0→P1 seam,
  ``pipeline.commitment.caiso_pergen_sync_reserve_caps`` — the
  ``pjm_reserve_pergen_sync`` convention, min-down gaps bridged, rule-18
  physics fast-start flags) and a NONSPIN column (OFFLINE fast-start ramp;
  offline slow iron backs nothing). Families become the nested tariff
  procurement: spin (½ requirement, spin curve, SPIN columns + storage RS)
  and contingency-total (FULL requirement, non-spin curve, all columns —
  BPM downward substitution).
* ``caiso_scarcity_pricing=False`` + ``scarcity_pricing_enabled=False`` —
  rule-19 exclusivity (enforced by the ScenarioConfig validator): the
  post-solve LOLP overlay and the in-LP co-opt both price CAISO reserve
  scarcity; the reserve duals are now the SOLE scarcity channel
  (the screen_reserve_value precedent). The keeper's overlay is
  honest-inert in the tight hours anyway (adds $0-37; diagnosis §3).

Zero fitted parameters: every requirement/curve is a NERC/tariff value, the
ramp and fast-start gates are class physics, and the online pattern is the
model's own P0 commitment state (forward-regenerating, condition-responsive
— rules 5/11/13/23). LOYO note: year-invariant code-level structure (the
caiso-78/85/90 precedent) — no per-year parameter; each year rides its own
load, fleet MSSC, and P0 pattern.

MECHANISM (one mechanism, two symptoms — rule 19): evening spin must come
from online headroom (backing off loaded CC, displacing energy to CTs on
merit), storage, or hydro — never from idle CC. This moves BOTH C1 volume
sides (CC_REGULAR over-run down, CT_PEAKER under-run up) AND the evening
duals (the C3c CT/ST-marginal rung) together.

PRE-REGISTERED directions (BEFORE the solve):
1. C1: CC_REGULAR 2024 (+5.30 TWh baseline) falls; CT_PEAKER class energy
   (0.81/0.68/0.31 TWh baselines vs 4.13/4.33/2.37 actual) rises. The
   EVENING hod buckets move most (model serves the ramp with CC where
   reality runs CTs); the overnight CC over-run is candidate-3 territory
   and is NOT expected to close here.
2. C3c: 2024 0 h → tail hours ON actual tail days (Jan-15/16 storm days,
   summer evening singles); 2023 18 h holds or rises toward the [40,160]
   band on actual tail days; 2025 stays ≤ 10 h. Dates matter more than
   counts (rule 11 — never tuned to the count).
3. C3a 2024/2025 (+11.5/+15.2% baselines) must NOT inflate materially: the
   spin dual in ordinary evenings is a $0-10 opportunity cost on a few
   hours, not a body adder. C3b PASS and the monthly map are the guards.
4. C2-2025 gas (-1.6% baseline): more CT at higher heat rates raises gas
   burn — watch the sign.
5. WATCH: Feb-2023 (+4.3) and Apr-2023 (-2.8) must not deepen materially;
   Jan-2024 (~0) must not reopen; Sep-Dec-2025 is the closed autumn lane.
FAIL conditions (pre-registered): a load-bearing gate flips PASS→FAIL, C3a
inflates materially, the WATCH months deepen materially, the new tail lands
on days the actual tail does not contain, or the mechanism is inert on C1 —
then the construction is re-examined against its own evidence (supply
scoping, storage/hydro participation), never tuned to the residual.

Registered whatever the result (rule 15), all three years in one invocation
(rule 16), NO zero-forcing ablation twin (rule 21 as amended 2026-07-14).

Usage: python scripts/probes/_caiso91_reserve_online_scoped_ab.py main
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
            "caiso-91 carries no ablation twin (rule 21 amended 2026-07-14); "
            "run with 'main'."
        )
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso91_reserve_online_scoped"
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-90 keeper recipe, unchanged, plus the SINGLE caiso-91 delta
    # group: the online-scoped reserve co-optimization (overlay swapped out
    # per rule 19).
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
    # THE caiso-91 delta group: in-LP online-scoped reserve co-opt replaces
    # the post-solve LOLP overlay (rule-19 exclusivity, validator-enforced).
    overrides["energy_reserve_coopt"] = True
    overrides["caiso_reserve_coopt"] = True
    overrides["caiso_reserve_online_scoped"] = True
    overrides["caiso_scarcity_pricing"] = False
    overrides["scarcity_pricing_enabled"] = False

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
            "caiso-91 online-scoped reserve co-opt main -- caiso-90 keeper "
            "recipe + energy_reserve_coopt + caiso_reserve_coopt + "
            "caiso_reserve_online_scoped (in-LP spin/non-spin co-opt, spin "
            "from ONLINE units only at the P0->P1 seam; LOLP overlay off per "
            "rule 19; issue #1492 correct build, C1 lane 2026-07-16), "
            "2023-2025"
        ),
    )
    print(f"DONE main -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
