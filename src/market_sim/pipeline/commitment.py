"""Shared P2 commitment pass — one commitment core for both orchestrators (Stage 4).

The P2 commitment screen — the optional third LP solve that re-dispatches the
fleet under a commitment mask derived from P1 clearing prices — was duplicated
near-verbatim in ``runner.py`` (forecast) and ``scripts/run_calibration.py``
(``_commitment_pass``, backcast) — orchestrator-unification plan §3.4. Stage 4
hoists the union of the two bodies here; both orchestrators now call
:func:`run_commitment_pass`.

The pass has four config-gated branches (all opt-in — P1 is THE main run per
CLAUDE.md; P2 never runs unless a gate below is set):

- **CAISO RA must-offer bridge** (``caiso_ra_mustoffer``, CAISO only) — now
  applied **P1-native**, not in P2. Since P2 was archived (CLAUDE.md: P0/P1 are
  the only production passes and every run is scored on P1), the bridge is
  injected as a ``min_gen`` floor *before* the single P1 solve, detected from the
  P0 run pattern (:func:`build_caiso_ra_p1_prep` /
  :func:`caiso_ra_p1_floor_fleet` above), so ``caiso_ra_mustoffer`` no longer
  triggers a P2 pass. The in-pass RA branch below is retained for the legacy
  ``--enable-legacy-p2`` path but is unreachable on the CAISO default path (it
  gates on ``not commitment_enabled``, and P2 on CAISO now triggers only via
  ``commitment_enabled``).
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


def caiso_ra_p1_floor_fleet(
    config,
    iso: str,
    fleet: list,
    fleet_arrays,
    p0_dispatch: np.ndarray,
    p0_prices: np.ndarray | None,
    mc_base: np.ndarray,
    release_hours: np.ndarray | None = None,
):
    """Return a floored ``FleetArrays`` for the P1 solve — the P1-native RA bridge.

    The CAISO Resource-Adequacy must-offer bridge (``caiso_ra_mustoffer``) used
    to run as a P2 re-solve on top of P1. P2 is archived (CLAUDE.md: P0/P1 are
    the only two passes, every run is scored on P1), so the bridge is now applied
    as a ``min_gen`` floor *before* the single P1 clearing solve: the same
    forward-derivable detector (:func:`model.commitment.caiso_ra_mustoffer_min_gen`)
    reads the model's own base-cost **P0** run pattern (and P0 duals / base MC for
    the startup-economics extension) instead of P1, writes the min-load floor on
    the merchant gas CC/CT fleet, and raises availability where the floor exceeds
    the economic ceiling so the LP stays feasible. The floor rides into P1, so the
    scored P1 pass carries the RA structure with no second solve.

    Detection from P0 rather than P1 keeps the input forward-derivable and
    condition-responsive (P0 and P1 are the same LP, differing only in the
    startup-markup objective — the midday run/idle pattern the bridge keys on is
    the same), and no measured generation enters (CLAUDE.md #1/#11).

    Returns ``None`` when the mechanism is off, the ISO is not CAISO, or the
    detector produces no floor (so the caller keeps the ordinary warm-started P1).
    """
    if not (getattr(config, "caiso_ra_mustoffer", False) and iso == "CAISO"):
        return None
    import dataclasses

    from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER
    from market_sim.model.commitment import caiso_ra_mustoffer_min_gen

    # Startup-cost-aware extension (caiso-44) + solar-proportional / seasonal
    # decommitment (caiso-48): identical gating to the former P2 branch, but fed
    # the P0 solution (dispatch + duals) — the LMP/MC the restart inequality
    # prices the gap at is the model's own base-cost dual, still forward-derivable.
    startup_bridge = bool(getattr(config, "caiso_ra_startup_bridge", False))
    bridge_decommit = startup_bridge and bool(
        getattr(config, "caiso_ra_bridge_decommit", False)
    )
    # Startup-aware run screen (G-61 path (b)): both it and the economic
    # bridge price start economics off the P0 duals + base MC.
    startup_aware = bool(getattr(config, "caiso_ra_bridge_startup_aware", False))
    need_econ = startup_bridge or startup_aware
    surplus_floor_value = (
        -float(config.renewable_keep_running_value)
        if getattr(config, "negative_renewable_offers", False)
        else 0.0
    )
    ra_floor = caiso_ra_mustoffer_min_gen(
        p0_dispatch,
        fleet_arrays,
        fleet,
        float(config.caiso_ra_min_load_frac),
        p1_prices=p0_prices if need_econ else None,
        base_mc=mc_base if need_econ else None,
        startup_bridge=startup_bridge,
        bridge_decommit=bridge_decommit,
        surplus_floor_value=surplus_floor_value,
        startup_aware=startup_aware,
        release_hours=release_hours,
    )
    # RA-quantity gate (gap G-61 path (a)): cap the bridged fleet at the
    # published gas-fired must-offer RA capacity for the compliance year —
    # the obligation attaches to RA-contracted capacity, not the whole
    # merchant fleet. Cheapest-startup plants drop first (RUC order).
    if getattr(config, "caiso_ra_mustoffer_quantity_gate", False):
        from market_sim.config.constants import CAISO_RA_MUSTOFFER_GAS_MW
        from market_sim.model.commitment import apply_ra_mustoffer_quantity_gate

        year = int(getattr(config, "weather_year", 0) or 0)
        cap_mw = CAISO_RA_MUSTOFFER_GAS_MW.get(year)
        if cap_mw is None and CAISO_RA_MUSTOFFER_GAS_MW:
            # Forward/uncovered year: latest published vintage (rule 23 —
            # refreshes when the next DMM annual report lands).
            cap_mw = CAISO_RA_MUSTOFFER_GAS_MW[max(CAISO_RA_MUSTOFFER_GAS_MW)]
        if cap_mw is not None:
            apply_ra_mustoffer_quantity_gate(ra_floor, fleet, fleet_arrays, cap_mw)
    if not np.any(ra_floor > 0.0):
        return None
    base_min_gen = (
        fleet_arrays.min_gen
        if fleet_arrays.min_gen is not None
        else np.broadcast_to(fleet_arrays.pmin[:, None], ra_floor.shape)
    )
    new_min_gen = np.maximum(base_min_gen, ra_floor)
    # D-2 attribution: the RA bridge owns every gen-hour where it strictly raised
    # the composed floor (maximum-composition, data.floor_mechanisms).
    base_mech = getattr(fleet_arrays, "min_gen_mechanism", None)
    new_mech = (
        base_mech.copy()
        if base_mech is not None
        else np.zeros(ra_floor.shape, dtype=np.int8)
    )
    new_mech[ra_floor > base_min_gen] = MECH_RA_MUSTOFFER
    # Feasibility: the LP binds ``min_gen <= P <= pmax * availability``. Raise
    # availability to at least ``min_gen / pmax`` on every floored gen-hour so the
    # floor never makes the P1 bound infeasible — the same guard the P2
    # preserve_min_gen path applied, minus the coal pin / commitment mask (P1
    # solves coal and every unit freely above the floor; there is no second pass
    # to lock a prior dispatch into).
    avail = fleet_arrays.availability.copy()
    pmax_safe = np.maximum(fleet_arrays.pmax, 1.0)[:, None]
    floored = new_min_gen > 0.0
    if floored.any():
        need = np.clip(new_min_gen / pmax_safe, 0.0, 1.0)
        avail = np.where(floored, np.maximum(avail, need), avail)
    return dataclasses.replace(
        fleet_arrays,
        min_gen=new_min_gen,
        min_gen_mechanism=new_mech,
        availability=avail,
        pmin=fleet_arrays.pmin.copy(),
    )


def build_caiso_ra_p1_prep(
    config,
    iso: str,
    fleet: list,
    fleet_arrays,
    mc_base,
    renewable_potential_mw: np.ndarray | None = None,
):
    """Return a ``p1_fleet_prep`` hook for :func:`pipeline.solve.run_energy_solve`.

    The hook is called with the P0 result once P0 has solved; it returns the
    RA-floored ``FleetArrays`` the P1 solve should use (or ``None`` to keep the
    ordinary warm-started P1). ``None`` when the RA must-offer mechanism is off or
    the ISO is not CAISO, so no non-CAISO / non-RA path changes.

    Args:
        renewable_potential_mw: Optional ``(T,)`` system wind+solar available
            potential (``Σ_z cf × cap``) — required only by the curtailed-VRE
            release (``caiso_ra_bridge_curtailment_release``, gap G-61 path
            (c)), which compares it against the P0 solution's dispatched
            wind+solar to find genuine-curtailment hours. ``None`` (the
            forecast orchestrator, which does not thread it yet) leaves the
            release inert by construction.
    """
    if not (getattr(config, "caiso_ra_mustoffer", False) and iso == "CAISO"):
        return None

    def _prep(r0):
        release_hours = None
        if (
            getattr(config, "caiso_ra_bridge_curtailment_release", False)
            and renewable_potential_mw is not None
        ):
            from market_sim.config.constants import CAISO_CURTAIL_RELEASE_EPS_MW

            dispatched = np.asarray(r0.wind_dispatched, dtype=float).sum(
                axis=0
            ) + np.asarray(r0.solar_dispatched, dtype=float).sum(axis=0)
            curtail = (
                np.asarray(renewable_potential_mw, dtype=float).reshape(-1) - dispatched
            )
            release_hours = curtail > CAISO_CURTAIL_RELEASE_EPS_MW
        return caiso_ra_p1_floor_fleet(
            config,
            iso,
            fleet,
            fleet_arrays,
            r0.dispatch,
            r0.prices,
            mc_base,
            release_hours=release_hours,
        )

    return _prep


def _pjm_unit_commitment_physics(fleet_arrays) -> tuple[np.ndarray, np.ndarray]:
    """Per-unit ``(min_down_hours, startup $/MW)`` from the published class tables.

    The same member derivation as ``reserve_config._posture_pool_params``
    (rule 18 — commitment eligibility gates on unit physics, never class
    names): coal from ``BIN_STARTUP_COST_PER_MW['COAL']`` +
    ``COAL_BIN_MIN_DOWN_HOURS``, gas CC/CT/ST from the NREL/SR-5500-55433
    class tables (``COMMITMENT_PARAMS_BY_FUEL``) keyed by heat rate. Fuels
    with no table (the oil quick-start IC/CT class ``_commitment_params``
    never screens) carry ``(0, 0)`` — fast-start by physics.
    """
    from market_sim.data.fleet import (
        BIN_STARTUP_COST_PER_MW,
        COAL_BIN_MIN_DOWN_HOURS,
        FUEL_TYPE_NAMES,
    )
    from market_sim.model.commitment import COMMITMENT_PARAMS_BY_FUEL

    n_gen = int(fleet_arrays.pmax.shape[0])
    hr = np.asarray(fleet_arrays.heat_rate, dtype=float)
    fuels = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    startup = np.zeros(n_gen)
    min_down = np.zeros(n_gen)
    for g in range(n_gen):
        f = fuels[g]
        if f == "coal":
            startup[g] = BIN_STARTUP_COST_PER_MW["COAL"]
            min_down[g] = float(COAL_BIN_MIN_DOWN_HOURS)
            continue
        table = COMMITMENT_PARAMS_BY_FUEL.get(f)
        if table is None:
            continue  # no commitment table -> fast-start by physics
        params = table[-1][1]
        for cutoff, p in table:
            if hr[g] < cutoff:
                params = p
                break
        startup[g] = float(params["startup_per_mw"])
        min_down[g] = float(params["min_down_hours"])
    return min_down, startup


def pjm_commitment_scoped_reserve_fleet(config, fleet_arrays, p0_dispatch):
    """Return the P1 ``FleetArrays`` with the commitment-scoped reserve mask applied.

    PJM path B (G-20b): the fa_p2-style availability screen, made P1-native.
    ERCOT's AS-aware P2 zeroes decommitted units' availability so idle
    slow-start capacity leaves the reserve-headroom RHS
    (``apply_commitment_with_coal_pin`` + ``ercot_commitment_headroom_overrides``);
    P2 is archived, so PJM applies the same commitment-state re-scope *before*
    the single scored P1 solve, with the commitment state read from the model's
    own base-cost **P0** run pattern (the CAISO RA bridge convention —
    forward-derivable, condition-responsive, no measured series; rules 11/13):

    * A PLANT is online in hour ``t`` when any of its tranches dispatches in P0
      (``pjm-reserve-ordc.md`` honesty-gate measure: "a plant is synchronized
      when any of its tranches dispatch") — tranches are the same physical iron,
      so an online plant's unused tranche headroom stays available.
    * Offline gaps shorter than the plant's capacity-weighted min-down are
      bridged online (``model.commitment._merge_runs``): a unit physically
      cannot cycle off-and-back inside its min-down window, so it stayed
      synchronized through the gap. Physics-loosening only — the bridge can
      only ADD online hours, never manufacture tightness (rule 11).
    * Non-fast-start reserve-eligible units (plant capacity-weighted min-down
      > ``POSTURE_FAST_START_MIN_DOWN_H`` or startup ≥
      ``POSTURE_FAST_START_STARTUP_PER_MW`` — the rule-18 physics thresholds
      ``_posture_pool_params`` uses) have availability zeroed in their plant's
      offline hours. Fast-start units are NEVER masked: an offline 10-min
      CT/oil peaker still provides non-synchronized Primary reserve
      (Manual 11 sec 4.2) and can start within the operating hour.

    A ``min_gen``-floored unit-hour is online by construction (P0 solves the
    same floors, so ``P0 >= min_gen > 0`` there) — no floor is ever masked.
    Returns ``None`` when the P0 pattern masks nothing (caller keeps the
    ordinary warm-started P1).
    """
    import dataclasses

    from market_sim.config.reserve_config import (
        POSTURE_FAST_START_MIN_DOWN_H,
        POSTURE_FAST_START_STARTUP_PER_MW,
        _reserve_eligible,
    )
    from market_sim.model.commitment import _merge_runs, find_runs

    # LP dispatch dust guard (simplex emits exact zeros for out-of-basis
    # columns; 1e-3 MW = 1 kW catches accumulated round-off only).
    TOL_MW = 1e-3

    p0 = np.asarray(p0_dispatch, dtype=float)
    n_gen, T = p0.shape
    eligible = _reserve_eligible(fleet_arrays)
    min_down_u, startup_u = _pjm_unit_commitment_physics(fleet_arrays)

    # Plant grouping: tranches of one plant share (plant_code, plant_group);
    # a unit without a plant code (imports, aggregates) is its own group.
    plant = np.asarray(fleet_arrays.plant_code, dtype=int)
    groups_raw = (
        np.asarray(fleet_arrays.plant_group, dtype=object)
        if getattr(fleet_arrays, "plant_group", None) is not None
        else np.array([""] * n_gen, dtype=object)
    )
    keys = np.array(
        [
            f"{plant[g]}|{groups_raw[g]}" if plant[g] > 0 else f"unit|{g}"
            for g in range(n_gen)
        ],
        dtype=object,
    )
    _, group_of = np.unique(keys, return_inverse=True)
    n_grp = int(group_of.max()) + 1 if n_gen else 0

    # Capacity-weighted plant min-down / startup over the reserve-eligible
    # members (the reserve-relevant iron); rule-18 fast-start exemption.
    cap = np.asarray(fleet_arrays.pmax, dtype=float)
    w = np.where(eligible, cap, 0.0)
    grp_cap = np.zeros(n_grp)
    grp_md = np.zeros(n_grp)
    grp_su = np.zeros(n_grp)
    np.add.at(grp_cap, group_of, w)
    np.add.at(grp_md, group_of, w * min_down_u)
    np.add.at(grp_su, group_of, w * startup_u)
    with np.errstate(invalid="ignore", divide="ignore"):
        grp_md = np.where(grp_cap > 0, grp_md / grp_cap, 0.0)
        grp_su = np.where(grp_cap > 0, grp_su / grp_cap, 0.0)
    grp_fast = (grp_md <= float(POSTURE_FAST_START_MIN_DOWN_H)) & (
        grp_su < float(POSTURE_FAST_START_STARTUP_PER_MW)
    )
    gated = eligible & ~grp_fast[group_of]
    if not gated.any():
        return None

    # Plant online pattern from P0: any tranche dispatching -> the plant is
    # synchronized that hour (all its tranches' headroom stays available).
    online = np.zeros((n_grp, T), dtype=bool)
    np.logical_or.at(online, group_of, p0 > TOL_MW)

    # Bridge offline gaps shorter than the plant's min-down (loosening only).
    for r in np.unique(group_of[gated]):
        md = float(grp_md[r])
        if md <= 1.0:
            continue
        runs = find_runs(online[r])
        if not runs:
            continue
        for start, end in _merge_runs(runs, md):
            online[r, start:end] = True

    masked = gated[:, None] & ~online[group_of]
    if not masked.any():
        return None
    avail = np.where(masked, 0.0, fleet_arrays.availability)
    return dataclasses.replace(
        fleet_arrays,
        availability=avail,
        pmin=fleet_arrays.pmin.copy(),
    )


def build_pjm_reserve_p1_prep(config, iso: str, fleet_arrays):
    """Return ``(p1_fleet_prep, p1_kwargs_prep)`` hooks for ``run_energy_solve``.

    PJM path B wiring (``pjm_reserve_commitment_scoped``, GATED default off):
    the fleet hook applies :func:`pjm_commitment_scoped_reserve_fleet` from the
    P0 run pattern; the kwargs hook recomputes the deliverable reserve-supply
    cap (``pjm_reserve_supply_cap`` → ``pjm_reserve_deliverable_supply_cap_mw``)
    on the MASKED fleet, so the P1 cap is Σ ramp10 over the ONLINE eligible
    units — the ``pjm-reserve-ordc.md`` bind-gate "online + 10-min-deliverable"
    measure — instead of the full-fleet ~39 GW. ``(None, None)`` when the
    mechanism is off, the ISO is not PJM, or the co-opt is off, so every other
    path is byte-identical.

    Raises on a stacked path-A/pergen config: the online-gate proxy and the
    per-pool layout scope the same phenomenon (one mechanism per phenomenon,
    rule 19) — path B supersedes, never composes.
    """
    if not (
        getattr(config, "pjm_reserve_commitment_scoped", False)
        and iso == "PJM"
        and getattr(config, "energy_reserve_coopt", False)
    ):
        return None, None
    if getattr(config, "pjm_reserve_online_gated", False) or getattr(
        config, "pjm_reserve_pergen", False
    ):
        raise ValueError(
            "pjm_reserve_commitment_scoped (path B) supersedes "
            "pjm_reserve_online_gated (path A) and is incompatible with "
            "pjm_reserve_pergen — enable exactly one reserve-supply scoping "
            "(CLAUDE.md rule 19: one mechanism per phenomenon)"
        )

    def _fleet_prep(r0):
        return pjm_commitment_scoped_reserve_fleet(config, fleet_arrays, r0.dispatch)

    def _kwargs_prep(r0, p1_fleet_arrays):
        # Only when the mask fired AND the deliverable cap is part of the recipe:
        # recompute the (1, T) supply cap on the masked availability.
        if p1_fleet_arrays is fleet_arrays:
            return None
        if not getattr(config, "pjm_reserve_supply_cap", False):
            return None
        from market_sim.results.scarcity import pjm_reserve_deliverable_supply_cap_mw

        cap = pjm_reserve_deliverable_supply_cap_mw(
            config, p1_fleet_arrays, int(config.hours)
        )
        if cap is None:
            return None
        return {"reserve_supply_cap": cap}

    return _fleet_prep, _kwargs_prep


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
    # LCR-aware commitment (CAISO local-capacity-revenue proxy): credit the
    # P1 LCR dual in the commitment margin so locally-committed units are not
    # decommitted on energy alone (BCR/CPM analogue, D-8 closure §6).
    lcr_value = None
    if (
        getattr(cfg, "caiso_lcr_commitment_credit", False)
        and iso == "CAISO"
        and p1.lcr_dual is not None
        and p1.lcr_gen_idx is not None
    ):
        from market_sim.model.commitment import lcr_dual_to_unit_value

        lcr_value = lcr_dual_to_unit_value(
            p1.lcr_dual, p1.lcr_gen_idx, fa.pmax.shape[0]
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
        lcr_value=lcr_value,
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
