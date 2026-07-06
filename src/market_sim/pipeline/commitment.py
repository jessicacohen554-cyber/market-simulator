"""Shared P2 commitment pass — one commitment core for both orchestrators (Stage 4).

The P2 commitment screen — the optional third LP solve that re-dispatches the
fleet under a commitment mask derived from P1 clearing prices — was duplicated
near-verbatim in ``runner.py`` (forecast) and ``scripts/run_calibration.py``
(``_commitment_pass``, backcast) — orchestrator-unification plan §3.4. Stage 4
hoists the union of the two bodies here; both orchestrators now call
:func:`run_commitment_pass`.

The pass has four config-gated branches (all opt-in — P1 is THE main run per
CLAUDE.md; P2 never runs unless a gate below is set):

- **CAISO RA must-offer bridge** (``caiso_ra_mustoffer``, CAISO only, engaged
  only when the economic commitment screen is off): a pure min-load bridge
  floor on the merchant gas CC/CT fleet — NO economic decommit screen.
  Previously reachable only from the backcast orchestrator; the forecast
  orchestrator's ``caiso_ra_mustoffer`` P2 *trigger* (audit gap A10) ran the
  economic screen instead — Stage 4 closes that drift: the trigger now reaches
  the real RA branch from both entry points.
- **Economic commitment screen** (``commitment_enabled``): CC/CT run-length
  screening on P1 margins + the coal pin
  (``model.commitment.compute_commitment`` →
  ``apply_commitment_with_coal_pin``).
- **NYISO path B** (``nyiso_synchronised_reserve``, NYISO only): force-commit
  the cheapest-startup NYC quick-start units until committed capacity covers
  the measured NYC spinning requirement, so the locational spinning family
  binds endogenously (docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md).
  Previously reachable only from the forecast orchestrator.
- **ERCOT AS-aware commitment** (``ercot_as_aware_commitment`` + multi-product
  co-opt, ERCOT only): value a unit's AS revenue (its own P1 reserve dual —
  never the measured MCPC) in the screen, floor committed headroom at the
  procured AS (AS-adequacy), and re-scope the P2 headroom rows to the
  commitment state (WS1).

Neutrality note (plan §7.3, Stage-4 gate): the hoist is statement-for-statement
and byte-identical on every keeper and on both orchestrators' default paths.
The single unified-semantics choice is the all-class reserve-family exclusion
in the AS-adequacy requirement (``fam_class >= 0``): the forecast body
documented and excluded the lumped total-ORDC family (reserve_class -1, "a
demand on the aggregate, not one product's procurement"), while the backcast
body's unfiltered ``np.add.at`` silently mis-indexed a -1 family onto the last
product's requirement. The shared core carries the forecast (documented)
semantics; the two bodies differ only under ERCOT AS-aware commitment WITH the
total-ORDC family enabled — a combination no keeper and no default path uses
(the Stage-4 P2 probe gate runs AS-aware with the total family off, where the
two bodies are provably byte-identical).
"""

from __future__ import annotations

import numpy as np

from market_sim.model.commitment import (
    apply_commitment_with_coal_pin,
    as_adequacy_commit,
    compute_commitment,
    reserve_adequacy_commit,
)
from market_sim.model.dispatch import solve_dispatch


def run_commitment_pass(state: dict, config=None):
    """Run the P2 commitment pass from a P1 ``state`` dict; return the result.

    Re-uses the cached P1 marginal cost, demand and dispatch inputs, so only
    the single P2 LP solve runs — no P0/P1 re-solve. ``config`` overrides the
    state's config (to iterate commitment params); defaults to the state's.
    This is the seam the backcast P2 post-processing layer
    (``run_calibration_full.run_p2``) uses on pickled ``p2_state`` bundles.

    Args:
        state: The P1 input bundle. Required keys: ``iso``, ``fleet`` (the
            dispatch ``Generator`` list), ``fleet_arrays``, ``mc_base``,
            ``mc_bid``, ``p1_result``, ``demand``, ``dispatch_kwargs``,
            ``config``. ``zone_names`` is required only when NYISO path B
            fires (older pickled states predate the key). As a side effect the
            P2 fleet bounds are stashed under ``state["fleet_arrays_p2"]`` so
            the backcast bundle writer can persist the floors the P2 dispatch
            actually saw (D-2 forced-energy attribution).
        config: Optional ``ScenarioConfig`` override for commitment-parameter
            iteration; defaults to ``state["config"]``.

    Returns:
        The P2 ``DispatchResult``.
    """
    cfg = config if config is not None else state["config"]
    iso = state["iso"]
    fleet = state["fleet"]
    fa = state["fleet_arrays"]
    p1 = state["p1_result"]
    dk = state["dispatch_kwargs"]
    # CAISO RA must-offer commitment (Step-1 overhaul): a PURE min-load bridge
    # floor on the merchant gas CC/CT fleet — NO economic decommit screen. Each
    # unit the economic P1 dispatch runs before AND after a midday idle gap
    # shorter than its min-down time is held at min-load across the gap
    # (model.commitment.caiso_ra_mustoffer_min_gen); the P2 re-solve then sets
    # the level economically above that floor. This replaces the removed
    # measured-NG:NG slab. Distinct from the ERCOT AS-aware path below (other
    # ISO); engaged only when the economic commitment screen is off (the keeper
    # config) so the two never compose.
    if (
        getattr(cfg, "caiso_ra_mustoffer", False)
        and iso == "CAISO"
        and not cfg.commitment_enabled
    ):
        import dataclasses

        from market_sim.model.commitment import caiso_ra_mustoffer_min_gen

        # Startup-cost-aware extension (caiso-44, default off): also bridge a gap
        # LONGER than min-down when cycling off is uneconomic, using the model's
        # OWN P1 dual (LMP) and base MC in the restart inequality — no measured
        # pin. Off => the plain physical (gap < min-down) bridge, byte-identical.
        startup_bridge = bool(getattr(cfg, "caiso_ra_startup_bridge", False))
        # Solar-proportional / seasonal decommitment (caiso-48, default off):
        # bound economic bridges to the day-ahead commitment horizon and
        # decommit them RUC-order where the candidate floors exceed the P1
        # import/export absorption — the surplus hours reprice to the
        # curtailable-renewable keep-running offer, the same floor the
        # negative_renewable_offers dispatch offers use (no new constant).
        bridge_decommit = startup_bridge and bool(
            getattr(cfg, "caiso_ra_bridge_decommit", False)
        )
        surplus_floor_value = (
            -float(cfg.renewable_keep_running_value)
            if getattr(cfg, "negative_renewable_offers", False)
            else 0.0
        )
        ra_floor = caiso_ra_mustoffer_min_gen(
            p1.dispatch,
            fa,
            fleet,
            float(cfg.caiso_ra_min_load_frac),
            p1_prices=p1.prices if startup_bridge else None,
            base_mc=state["mc_base"] if startup_bridge else None,
            startup_bridge=startup_bridge,
            bridge_decommit=bridge_decommit,
            surplus_floor_value=surplus_floor_value,
        )
        base_min_gen = (
            fa.min_gen
            if fa.min_gen is not None
            else np.broadcast_to(fa.pmin[:, None], ra_floor.shape)
        )
        new_min_gen = np.maximum(base_min_gen, ra_floor)
        # D-2 attribution: the RA bridge wins wherever it strictly raised the
        # composed floor (maximum-composition, data.floor_mechanisms).
        from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER

        base_mech = getattr(fa, "min_gen_mechanism", None)
        new_mech = (
            base_mech.copy()
            if base_mech is not None
            else np.zeros(ra_floor.shape, dtype=np.int8)
        )
        new_mech[ra_floor > base_min_gen] = MECH_RA_MUSTOFFER
        fa_ra = dataclasses.replace(
            fa,
            min_gen=new_min_gen,
            min_gen_mechanism=new_mech,
            pmin=fa.pmin.copy(),
        )
        # All-committed mask: no decommit. preserve_min_gen carries the RA
        # min-load floor into P2 and raises availability to keep it feasible.
        committed = np.ones(ra_floor.shape, dtype=bool)
        fa_p2 = apply_commitment_with_coal_pin(
            fa_ra,
            committed,
            p1.dispatch,
            fleet,
            screen_coal=False,
            preserve_min_gen=True,
        )
        # Expose the P2 bounds (incl. the RA floor + mechanism ids) so the
        # bundle writer can persist the floors the P2 dispatch actually saw.
        state["fleet_arrays_p2"] = fa_p2
        return solve_dispatch(fa_p2, state["demand"], mc=state["mc_bid"], **dk)
    # AS-aware (ERCOT multi-product co-opt): value a unit's AS revenue (the P1
    # per-product reserve dual x its reserve-eligible headroom) in the screen, so
    # the units a tight month keeps online FOR AS stay committed and the P2 co-opt
    # headroom reflects realistic online capacity. The AS value comes from the
    # model's OWN P1 balance-row dual, never the measured MCPC (no fit).
    as_value = None
    if (
        getattr(cfg, "ercot_as_aware_commitment", False)
        and iso == "ERCOT"
        and getattr(cfg, "energy_reserve_coopt", False)
    ):
        from market_sim.results.scarcity import ercot_as_aware_unit_value

        as_value = ercot_as_aware_unit_value(
            fa, p1.dispatch, p1.reserve_price_by_family, cfg.hours
        )
    committed = compute_commitment(
        p1.prices,
        state["mc_base"],
        fleet,
        fa,
        cfg,
        storage_charge=p1.storage_charge,
        storage_discharge=p1.storage_discharge,
        storage_zone_idx=dk["storage_zone_idx"],
        demand=state["demand"],
        as_value=as_value,
    )
    # NYISO path B (commitment-gated synchronised reserve): the
    # energy-economic screen decommits NYC quick-start peakers that
    # aren't needed for energy, so they can no longer back the
    # locational spinning family and the >$300 tail never fires.
    # Force-commit the cheapest-startup NYC quick-start units until
    # their committed capacity covers the MEASURED NYC spinning
    # requirement (NYISO_SPIN_FRACTION x NYC 10-min total = 250 MW),
    # so the P2 class-1 NYC headroom row equals Sum_online(pmax - P)
    # and the family binds endogenously in genuinely tight hours
    # (docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md,
    # "Path B"). NYISO-only behind the default-off flag.
    if getattr(cfg, "nyiso_synchronised_reserve", False) and iso == "NYISO":
        from market_sim.results.scarcity import (
            nyiso_spin_eligible,
            nyiso_spin_requirement_mw,
        )

        spin_eligible = nyiso_spin_eligible(fa, state["zone_names"])
        committed = reserve_adequacy_commit(
            committed,
            fa,
            fleet,
            spin_eligible,
            requirement_mw=nyiso_spin_requirement_mw(cfg),
            headroom_frac=cfg.nyiso_spin_headroom_frac,
        )
    # AS-adequacy floor (ERCOT AS-aware): re-commit cheapest eligible units until
    # committed online headroom covers the MEASURED total AS requirement, so the
    # screen cannot strip the reserve pool below what ERCOT procured (which would
    # price a false VOLL-scale shortage). The broad-month elevation then forms from
    # the binding shared-headroom dual (opportunity cost), while genuinely-short
    # acute hours still price the VOLL curve. Requirement = sum of the per-product
    # ASPLANNP433 quantities already in dispatch_kwargs, aggregated from the
    # per-FAMILY rows onto per-PRODUCT (reserve-class) rows: the ECRS
    # conservative-deployment split runs one product as two disjoint-window
    # families sharing a class (reserve_balance_class maps family -> product),
    # so summing families per class recovers the product requirement exactly
    # (identity when families == products).
    if as_value is not None and "reserve_headroom_eligible" in dk:
        req_fam = np.atleast_2d(np.asarray(dk["reserve_requirement"], dtype=float))
        hp = np.atleast_2d(np.asarray(dk["reserve_headroom_products"], dtype=bool))
        fam_class = np.asarray(
            dk.get("reserve_balance_class", np.arange(req_fam.shape[0])), dtype=int
        )
        req_by_class = np.zeros((hp.shape[1], req_fam.shape[1]), dtype=float)
        # All-class families (reserve_class -1, the ERCOT lumped ORDC
        # total-reserve curve) are a demand on the aggregate, not one
        # product's procurement — exclude them from the per-product adequacy
        # requirement (a -1 would otherwise silently index the last product).
        prod_fam = fam_class >= 0
        np.add.at(req_by_class, fam_class[prod_fam], req_fam[prod_fam])
        committed = as_adequacy_commit(
            committed,
            fa,
            fleet,
            dk["reserve_headroom_eligible"],
            dk["reserve_headroom_products"],
            req_by_class,
            p1.dispatch,
            headroom_frac=float(cfg.ercot_as_adequacy_frac),
        )
    # A reserve / AS-deployment floor (ct_deployment / reliability_deployment)
    # must survive the economic commitment screen — those units ran for
    # reliability, not economics. Preserve min_gen through P2 only when such an
    # overlay is active (NEISO/other backcasts opt in); off by default so the
    # forecast runner and every non-overlay keeper stay byte-identical.
    preserve_min_gen = bool(
        getattr(cfg, "ct_deployment_overlay", False)
        or getattr(cfg, "reliability_deployment_overlay", False)
        or getattr(cfg, "caiso_gas_commitment_floor", False)
        or getattr(cfg, "nyiso_local_selfsupply", False)
        or getattr(cfg, "reliability_floor", False)
        or getattr(cfg, "nyiso_firm_imports", False)
        or getattr(cfg, "miso_firm_imports", False)
    )
    fa_p2 = apply_commitment_with_coal_pin(
        fa,
        committed,
        p1.dispatch,
        fleet,
        screen_coal=cfg.commitment_screen_coal,
        preserve_min_gen=preserve_min_gen,
        # WS1 (commitment-state-aware reserve headroom): a cold plant's peak
        # (duct-firing) tranche can neither generate nor hold reserve — couple
        # it to the committed tranche so it leaves the P2 headroom RHS too.
        couple_peak=as_value is not None,
    )
    dk_p2 = dk
    if as_value is not None and "reserve_headroom_eligible" in dk:
        # Commitment-state-aware reserve headroom (WS1): online CTs join the
        # synchronized (fast) pool via the P2 availability, offline quick-start
        # capacity backs Non-Spin only via the extra-cap RHS. Overrides only
        # the two headroom kwargs; everything else in dk is shared with P1.
        from market_sim.config.reserve_config import (
            ercot_commitment_headroom_overrides,
        )

        dk_p2 = {
            **dk,
            **ercot_commitment_headroom_overrides(
                fa, committed, dk["reserve_headroom_eligible"]
            ),
        }
    # Expose the P2 bounds so the bundle writer can persist the floors the
    # P2 dispatch actually saw (D-2 forced-energy attribution).
    state["fleet_arrays_p2"] = fa_p2
    return solve_dispatch(fa_p2, state["demand"], mc=state["mc_bid"], **dk_p2)
