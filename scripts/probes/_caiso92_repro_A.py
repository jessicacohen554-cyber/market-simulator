"""caiso-92 probe: the MEASURED DAM offer surface on the caiso-90 keeper recipe.

RECIPE-IDENTICAL to the caiso-90 keeper
(`scripts/probes/_caiso90_citygate_flow_date_ab.py`). The single structural
delta GROUP is the measured CAISO DAM offer surface (C1 CC-over/CT-under
lane WP-A, 2026-07-16 handoff; the admissible route named by
FINDING-caiso91b and diagnosis §3-4), derived from CAISO's OWN published
DAM bids (OASIS Public Bid Data, 90-day-lag masked curves — the
dam-public-bids intake + scripts/derive_caiso_offer_surface.py):

* ``caiso_offer_surface_measured=True`` — the STATIC half: the fitted
  ``_CAISO_OFFER_CURVE`` econ_low / econ_high / peak multipliers for
  CC_REGULAR + CT_PEAKER are REPLACED by the measured cap-weighted medians
  of the fleet's own bid curves (carbon/VOM-netted so the tranche mc
  round-trips the measured bid; committed band deliberately unarmed — the
  Lever-A inversion lesson, rule 19). This owns the Panoche bid wedge: the
  measured CT econ rung sits $5-10 under the fitted carbon+multiplier-
  loaded rung that priced the class out of hours its fuel-only SRMC clears.
* ``caiso_offer_surface_conditional=True`` — the CONDITIONAL half: the
  PJM/NEISO condition-binned peak-rung ladder ported to CAISO (5
  equal-capacity peak rungs repriced P1-only to the measured
  per-net-load-bin top-of-curve quantiles; loose hours byte-identical,
  ratio clamped >= 1). This carries the measured DA-expectation tail the
  static bands cannot (the C3c summer singles clear $200-1175 in DA at fat
  reserves — diagnosis §1/§3).

Both flags are explicit solve_and_persist kwargs (NOT prb_overrides: the
static merge and rung split run inside backcast_config on the explicit
parameters). Zero fitted parameters: every consumed number is a measured
bid statistic normalized by the model's own fuel/carbon inputs
(rules 5/11/13); the derive carries pre-registered estimation gates
(G1-G4, incl. estimation-stage LOYO — the caiso-89 precedent) and is
frozen against residuals (rule 23). Rule-24/25 SHRINK: fitted multipliers
retire where measured rungs land; CAISO-only, no cross-ISO fallback.

MECHANISM (one measured surface, two symptom faces — rule 19): the fitted
CT econ rungs (1.10-1.50 x HR + carbon) price the CT class out of the
evening/overnight hours its measured bids clear, so the model serves the
ramp with CC (C1 volume, both sides) and never reaches the CT-marginal
evening dual (the hod ladder's evening underprice; the C3c summer
remainder on its extreme).

PRE-REGISTERED directions (BEFORE the solve; baselines = the same-machine
caiso-90 repro solved this session):
1. C1: CT_PEAKER model energy (0.84 / 0.69 / 0.32 TWh vs actual
   4.13 / 4.33 / 2.37) RISES via MERIT — no floor is added (C8 stays clean
   by construction); CC_REGULAR (+1.90 / +5.30 / +2.55 TWh) must not
   inflate. The evening hod buckets move most; the overnight CC over-run
   is candidate-3 (WP-B) territory and is NOT expected to close here.
2. The hod price ladder: the evening leg (hod 17-21 resid -3.9 / -2.9 /
   -0.8) closes toward 0; the belly leg (hod 10-14, +13.8 / +11.1 / +9.1)
   must NOT inflate (measured CC econ bands may lower it — an
   improvement, not a fail).
3. C3a 2024/2025 (+11.5 / +15.2 % baselines) must not inflate materially;
   C3b PASS and the monthly map are the guards.
4. C3c (DA basis, days before counts): 2023's 18 h on Jan-13 (the right
   day) hold; summer singles (Jul-Aug evening hod 16-19) may start
   landing via the tight-bin measured tops; 2025 stays <= 10 h. A new
   tail on days the actual tail does not contain is a FAIL signal.
5. C2-2025 gas (-1.6 % baseline): more CT at higher heat rates raises gas
   burn — watch the sign. C4-2023 gas (.828/.319 FAIL baseline) watch.
6. WATCH months (ONE construction, A-vs-B): Feb-2023 (+4.3) and Apr-2023
   (-2.8) must not deepen materially; Jan-2024 (~0) must not reopen;
   Sep-Dec-2025 (+8..+11) is the CLOSED autumn lane.
FAIL conditions (pre-registered): a load-bearing gate flips PASS->FAIL,
C3a inflates materially, a WATCH month deepens materially, the new tail
lands on wrong days, or the surface is measured inert — then the
construction is re-examined against its own evidence (classification,
normalization, coverage), never tuned to the residual.

Registered whatever the result (rule 15), all three years in one
invocation (rule 16), NO ablation twin (rule 21 as amended 2026-07-14).

Usage: python scripts/probes/_caiso92_measured_offer_surface_ab.py main
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
            "caiso-92 carries no ablation twin (rule 21 amended 2026-07-14); "
            "run with 'main'."
        )
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso92_repro_A"
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-90 keeper recipe, unchanged (same overrides stack as
    # _caiso90_citygate_flow_date_ab.py).
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
        # THE caiso-92 delta group: the measured DAM offer surface (explicit
        # kwargs — the static merge + rung split run inside backcast_config
        # on these parameters, NOT on the prb_overrides channel).
        caiso_offer_surface_measured=True,
        caiso_offer_surface_conditional=True,
        note=(
            "caiso-92 measured offer surface main -- caiso-90 keeper recipe "
            "+ caiso_offer_surface_measured + caiso_offer_surface_conditional "
            "(OASIS Public Bid Data: measured static econ/peak band mults "
            "replace the fitted _CAISO_OFFER_CURVE gas multipliers, + the "
            "condition-binned measured peak-rung ladder, P1-only; C1 lane "
            "WP-A 2026-07-16), 2023-2025"
        ),
    )
    print(f"DONE main -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
