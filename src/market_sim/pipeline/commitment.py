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
- **ERCOT gas commitment bridge** (``ercot_gas_commitment_bridge``, ERCOT
  only) — P1-native like the CAISO bridge, never a P2 trigger: the same
  ISO-neutral detector scoped to merchant gas-CC with the measured ERCOT
  committed-CC LSL/HSL p50 min-load and a DA-operating-day cap on the
  economic leg (:func:`ercot_gas_bridge_p1_floor_fleet` /
  :func:`build_ercot_gas_bridge_p1_prep`).
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

import logging

import numpy as np

from market_sim.model.commitment import (
    apply_commitment_with_coal_pin,
    as_adequacy_commit,
    compute_commitment,
    reserve_adequacy_commit,
)
from market_sim.model.dispatch import solve_dispatch

logger = logging.getLogger(__name__)


def load_cc_start_trajectory(iso: str):
    """Return the ISO's measured CC start-to-load duration table, or ``None``.

    Reads the committed measured artifact
    (``scripts/data/derive_campd_cc_start_trajectory.py`` →
    ``data/raw/_processed-legacy/campd_cc_start_trajectory_<ISO>.csv``): per
    CC plant the CAMPD p50 off→on-to-full-load ramp duration in hours
    (``basis == "plant"``, gate-accepted rows only), sparse-coverage rows
    (``basis == "sparse"``, informational — callers fall back to the class
    row) and the pooled class p50 under ``plant_code == 0``
    (``basis == "class"``). ``None`` when the ISO has no artifact — the
    startup-trajectory extension is then simply inert, mirroring the
    ramp-envelope convention (never a silent hand number, rule #23). Treat
    the returned frame as read-only.
    """
    import pandas as pd

    from market_sim.config.paths import PROCESSED_DIR

    path = PROCESSED_DIR / f"campd_cc_start_trajectory_{iso.upper()}.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def cc_startup_lead_hours(fleet: list, fleet_arrays, iso: str) -> np.ndarray | None:
    """Return the ``(n_gen,)`` measured start-to-load lead hours, or ``None``.

    Maps the derived CAMPD CC start-trajectory artifact
    (:func:`load_cc_start_trajectory`) onto the dispatch fleet for the RA
    bridge's startup-trajectory extension (caiso-96 WP-1): each merchant
    gas-CC row gets its plant's gate-accepted p50 start-to-load duration;
    plants without an accepted row get the artifact's pooled class p50.
    Non-CC and cogen rows stay 0: a fast-start CT reaches load sub-hourly
    (CT_COMMITMENT_PARAMS min-down 1 h — no lead exists at hourly LP
    resolution, the parameter-not-class-name gate of rule 18), and CHP
    follows its steam host's own floor (rule 19). Returns ``None`` — the
    extension inert — when the ISO has no derived artifact (a measured
    parameter or nothing, rule #23) or no row carries a positive lead.
    """
    table = load_cc_start_trajectory(iso)
    if table is None:
        logger.warning(
            "caiso_ra_startup_trajectory: no derived start-trajectory artifact "
            "for %s (scripts/data/derive_campd_cc_start_trajectory.py) — the "
            "extension is inert (a measured lead or nothing, rule 23).",
            iso,
        )
        return None
    plant_lead = {
        int(r.plant_code): float(r.lead_hours)
        for r in table[table.basis == "plant"].itertuples()
    }
    cls = table[table.basis == "class"]
    class_lead = float(cls.lead_hours.iloc[0]) if len(cls) else 0.0
    plant_code = getattr(fleet_arrays, "plant_code", None)
    lead = np.zeros(len(fleet), dtype=int)
    for g, gen in enumerate(fleet):
        if gen.fuel_type != "gas_cc" or gen.plant_group.endswith("_CHP"):
            continue
        pc = int(plant_code[g]) if plant_code is not None else 0
        lead[g] = int(round(plant_lead.get(pc, class_lead)))
    return lead if np.any(lead > 0) else None


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
    # Startup-trajectory extension (caiso-96 WP-1): measured CC start-to-load
    # leads floor the L pre-start hours of each detected run-start at the
    # ramp-in trajectory (same mechanism, wider physics — rule 19; D-2
    # attribution stays ra_mustoffer_bridge).
    startup_lead = (
        cc_startup_lead_hours(fleet, fleet_arrays, iso)
        if getattr(config, "caiso_ra_startup_trajectory", False)
        else None
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
        startup_lead_hours=startup_lead,
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
    return _bridge_floored_fleet(
        fleet_arrays,
        ra_floor,
        MECH_RA_MUSTOFFER,
        preserve_absorption=bool(getattr(config, "caiso_p1_export_sink_seam", False)),
    )


def _bridge_floored_fleet(
    fleet_arrays,
    bridge_floor: np.ndarray,
    mech_id: int,
    preserve_absorption: bool = False,
):
    """Compose a P1-native bridge floor onto a ``FleetArrays`` (shared tail).

    The floor-composition/attribution/feasibility sequence both P1-native
    commitment bridges share (CAISO RA must-offer, ERCOT gas commitment
    bridge): maximum-compose the bridge floor onto ``min_gen``, tag the D-2
    mechanism id wherever the bridge strictly raised the composed floor
    (data.floor_mechanisms maximum-composition rule), and raise availability
    to at least ``min_gen / pmax`` on every floored gen-hour so the floor
    never makes the P1 bound ``min_gen <= P <= pmax * availability``
    infeasible — the same guard the P2 preserve_min_gen path applied, minus
    the coal pin / commitment mask (P1 solves every unit freely above the
    floor; there is no second pass to lock a prior dispatch into).

    Args:
        preserve_absorption: Exempt the ``pmin < 0`` absorption rows (the
            priced export sinks) from the maximum-composition, restoring the
            invariant ``data.fleet.arrays._compose_min_gen_floors`` already
            states for its own zeros-init: *"export sinks (pmin < 0,
            absorption modeled as negative generation) must keep their range
            — a zero floor would pin them off"*. The bridge floor is a
            zeros-initialised array positive only on bridged thermal rows, so
            ``max(pmin, 0) = 0`` collapses every sink's lower bound to zero
            and the scored P1 pass solves with its export outlet DELETED
            while P0 keeps it (FINDING-caiso138 §D measured the consequence:
            zero exports in all 26,280 corridor-hours of every CAISO keeper
            since the RA bridge). Default ``False`` — the seam is
            CAISO-flag-gated (``ScenarioConfig.caiso_p1_export_sink_seam``)
            so no other ISO's keeper recipe shifts underneath it; the ERCOT
            and NYISO bridges re-gate on their own evidence (rule 25
            [R-ISO-SCOPE], caiso-138 §D cross-ISO blast radius).
    """
    import dataclasses

    base_min_gen = (
        fleet_arrays.min_gen
        if fleet_arrays.min_gen is not None
        else np.broadcast_to(fleet_arrays.pmin[:, None], bridge_floor.shape)
    )
    new_min_gen = np.maximum(base_min_gen, bridge_floor)
    if preserve_absorption:
        absorb = np.asarray(fleet_arrays.pmin, dtype=float) < 0.0
        if absorb.any():
            new_min_gen[absorb, :] = np.asarray(base_min_gen, dtype=float)[absorb, :]
    base_mech = getattr(fleet_arrays, "min_gen_mechanism", None)
    new_mech = (
        base_mech.copy()
        if base_mech is not None
        else np.zeros(bridge_floor.shape, dtype=np.int8)
    )
    # Tag where the COMPOSED floor strictly rose, not where the raw bridge
    # floor exceeds the base: identical for every gen row, and with
    # preserve_absorption on it keeps MECH_RA_MUSTOFFER off the exempt sink
    # rows (the raw floor's 0 does exceed their negative pmin).
    new_mech[new_min_gen > base_min_gen] = mech_id
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


def _ercot_gas_bridge_floor(
    config,
    fleet: list,
    fleet_arrays,
    p0_dispatch: np.ndarray,
    p0_prices: np.ndarray | None,
    mc_base: np.ndarray,
) -> np.ndarray | None:
    """Compute the raw ``(n_gen, T)`` ERCOT gas-CC bridge floor (or ``None``).

    The detector body shared by the P1 fleet hook (the floor itself) and the
    floor-scoped LSL markdown bid hook (its hour mask) — hoisted out of
    :func:`ercot_gas_bridge_p1_floor_fleet` so
    :func:`build_ercot_gas_bridge_p1_preps` computes the floor ONCE per P0
    result and shares it (the ERCOT-64 charter wiring trap #2: two hooks
    re-running the detector independently could diverge). Assumes the caller
    already checked the ``ercot_gas_commitment_bridge`` + ISO gate. Returns
    ``None`` when the detector produces no floor.
    """
    from market_sim.config.constants import DA_COMMITMENT_HORIZON_HOURS
    from market_sim.model.commitment import caiso_ra_mustoffer_min_gen, find_runs

    # Economic ≥min-down bridging (the overnight-between-run-days carrier):
    # priced off the P0 duals + base MC, exactly the CAISO startup-bridge
    # construction. The CAISO startup-AWARE run screen is deliberately not
    # exposed here (dropped with cause — see the ScenarioConfig field note).
    startup_bridge = bool(getattr(config, "ercot_gas_bridge_startup", True))
    max_gap = (
        float(DA_COMMITMENT_HORIZON_HOURS)
        if getattr(config, "ercot_gas_bridge_da_horizon", True)
        else None
    )
    # ercot141 online-hours leg: floor the committed band in every P0-ONLINE
    # hour, not only the idle gaps (ScenarioConfig.ercot_gas_bridge_online_hours
    # — the ERCOT-139 §4.1 successor; same mechanism/level/D-2 id, wider window).
    # The getattr default mirrors the registered field default, so a replayed
    # pre-ercot141 recorded config reproduces its original solve exactly.
    online_hours = bool(getattr(config, "ercot_gas_bridge_online_hours", False))
    bridge_floor = caiso_ra_mustoffer_min_gen(
        p0_dispatch,
        fleet_arrays,
        fleet,
        float(config.ercot_gas_bridge_min_load_frac),
        p1_prices=p0_prices if startup_bridge else None,
        base_mc=mc_base if startup_bridge else None,
        startup_bridge=startup_bridge,
        fuel_types=("gas_cc",),
        max_econ_gap_hours=max_gap,
        floor_online_hours=online_hours,
    )
    if not np.any(bridge_floor > 0.0):
        return None
    # Diagnostic trace for the D-4 window / probe analysis: every floored
    # segment IS a bridged gap, so its length distribution is the direct
    # evidence the declared window (idle gaps within one DA operating day)
    # is what actually binds.
    seg_lengths = [
        e - s
        for g in np.flatnonzero((bridge_floor > 0.0).any(axis=1))
        for s, e in find_runs(bridge_floor[g] > 0.0)
    ]
    if seg_lengths:
        seg = np.array(seg_lengths)
        buckets = {
            "<4h": int((seg < 4).sum()),
            "4-8h": int(((seg >= 4) & (seg < 8)).sum()),
            "8-16h": int(((seg >= 8) & (seg < 16)).sum()),
            "16-24h": int(((seg >= 16) & (seg <= 24)).sum()),
            ">24h": int((seg > 24).sum()),
        }
        # With the ercot141 online-hours leg armed a floored segment is no longer
        # a bridged GAP — runs and the gaps between them fuse into one committed
        # block — so the leg is named explicitly and the buckets relabelled, and
        # the headroom is reported: the leg's whole premise is that the floored
        # rows are PINNED (max P − floor = 0), which is what makes them unable to
        # set the margin (ERCOT-64). This is the arm's live verification.
        logger.info(
            "ERCOT gas commitment bridge%s: %d unit-hours floored "
            "(%.2f TWh floor volume), %d floored %s by length %s",
            " [+online-hours leg]" if online_hours else "",
            int((bridge_floor > 0.0).sum()),
            float(bridge_floor.sum()) / 1e6,
            len(seg_lengths),
            "committed blocks" if online_hours else "bridged gaps",
            buckets,
        )
    return bridge_floor


def ercot_gas_bridge_p1_floor_fleet(
    config,
    iso: str,
    fleet: list,
    fleet_arrays,
    p0_dispatch: np.ndarray,
    p0_prices: np.ndarray | None,
    mc_base: np.ndarray,
):
    """Return the bridge-floored ``FleetArrays`` for the ERCOT P1 solve.

    The ERCOT gas-CC commitment bridge (``ercot_gas_commitment_bridge``, the
    committed-state mechanism promoted from the ERCOT-62b probe — see the
    ScenarioConfig field docstring and
    docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md §5-6): the same
    ISO-neutral detector as the CAISO RA must-offer bridge
    (:func:`model.commitment.caiso_ra_mustoffer_min_gen`, fed the model's own
    base-cost P0 run pattern and duals), scoped to the merchant gas-CC fleet
    (``fuel_types=("gas_cc",)`` — the recorded ERCOT-63 class adjudication),
    with ``min_load_frac`` = the measured committed-CC LSL/HSL
    capacity-weighted p50 and the economic (≥ min-down) leg bounded to one DA
    operating day (``DA_COMMITMENT_HORIZON_HOURS``) when
    ``ercot_gas_bridge_da_horizon`` is on. D-2 attribution:
    ``MECH_GAS_COMMITMENT_BRIDGE``. Detector body:
    :func:`_ercot_gas_bridge_floor` (shared with the floor-scoped markdown's
    bid hook via :func:`build_ercot_gas_bridge_p1_preps`).

    Returns ``None`` when the mechanism is off, the ISO is not ERCOT, or the
    detector produces no floor (the caller keeps the ordinary warm-started P1).
    """
    if not (getattr(config, "ercot_gas_commitment_bridge", False) and iso == "ERCOT"):
        return None

    from market_sim.data.floor_mechanisms import MECH_GAS_COMMITMENT_BRIDGE

    bridge_floor = _ercot_gas_bridge_floor(
        config, fleet, fleet_arrays, p0_dispatch, p0_prices, mc_base
    )
    if bridge_floor is None:
        return None
    return _bridge_floored_fleet(fleet_arrays, bridge_floor, MECH_GAS_COMMITMENT_BRIDGE)


def build_ercot_gas_bridge_p1_prep(
    config, iso: str, fleet: list, fleet_arrays, mc_base
):
    """Return a ``p1_fleet_prep`` hook for the ERCOT gas commitment bridge.

    The fleet-hook-only convenience wrapper over
    :func:`build_ercot_gas_bridge_p1_preps` (kept for callers/tests that
    predate the floor-scoped markdown's shared-floor pairing). ``None`` when
    the mechanism is off or the ISO is not ERCOT, so every other path is
    byte-identical. ISO-exclusive with the CAISO and PJM P1-prep hooks by
    construction (each gates on its ISO).
    """
    fleet_prep, _ = build_ercot_gas_bridge_p1_preps(
        config, iso, fleet, fleet_arrays, mc_base
    )
    return fleet_prep


def build_ercot_gas_bridge_p1_preps(
    config,
    iso: str,
    fleet: list,
    fleet_arrays,
    mc_base,
    floorscoped_markdown_fn=None,
):
    """Return ``(p1_fleet_prep, p1_bid_adjust_prep)`` sharing ONE bridge floor.

    The ERCOT-64 pairing seam: the gas commitment bridge's P1 ``min_gen``
    floor (the committed STATE) and the floor-scoped committed-LSL markdown
    (``ercot_offer_surface_lowcurve_floorscoped`` — the measured LSL bid on
    exactly those floored plant-hours) both key on the SAME detector output,
    so the floor is computed once per P0 result and memoized; the two hooks
    :func:`pipeline.solve.run_energy_solve` calls (bid adjust first, fleet
    prep second) read the shared value — never two detector runs that could
    diverge (charter wiring trap #2). The markdown keys on the BRIDGE FLOOR
    MASK, never the v2 P0-online gate, which is False in bridged gap hours
    by construction (trap #1).

    Args:
        floorscoped_markdown_fn: Optional callable ``(floor_mask) ->
            Optional[np.ndarray]`` building the ``(n_gen, T)`` P1-only
            additive markdown from the bridge's boolean floor mask (the
            orchestrator closes over its fuel prices / net load —
            ``data.fleet.build_ercot_offer_surface_lowcurve_floorscoped_markdown``).
            Only consulted when ``ercot_offer_surface_lowcurve_floorscoped``
            is on.

    Returns:
        ``(p1_fleet_prep, p1_bid_adjust_prep)`` — either may be ``None``
        (flag off / not ERCOT / nothing to do), keeping every other path
        byte-identical.

    Raises:
        ValueError: If ``ercot_offer_surface_lowcurve_floorscoped`` is on
            without ``ercot_gas_commitment_bridge`` (the scope IS the
            bridge's floor mask — there is no window without it), or together
            with the refuted tranche-wide ``ercot_offer_surface_lowcurve``
            (same rows, same phenomenon — rule 19: one mechanism per
            phenomenon), or if ``ercot_gas_bridge_online_hours`` is on without
            ``ercot_gas_commitment_bridge`` (it widens that bridge's window —
            there is no floor to widen without it).
    """
    floorscoped = bool(
        getattr(config, "ercot_offer_surface_lowcurve_floorscoped", False)
    )
    bridge_on = bool(
        getattr(config, "ercot_gas_commitment_bridge", False) and iso == "ERCOT"
    )
    if floorscoped and iso == "ERCOT":
        if not getattr(config, "ercot_gas_commitment_bridge", False):
            raise ValueError(
                "ercot_offer_surface_lowcurve_floorscoped requires "
                "ercot_gas_commitment_bridge: the markdown's window IS the "
                "bridge's floored plant-hours (no floor, no LSL role)."
            )
        if getattr(config, "ercot_offer_surface_lowcurve", False):
            raise ValueError(
                "ercot_offer_surface_lowcurve_floorscoped is mutually "
                "exclusive with the tranche-wide ercot_offer_surface_lowcurve "
                "(same committed rows, same phenomenon — CLAUDE.md rule 19; "
                "the tranche-wide form is probe-refuted, diagnosis §7)."
            )
    # ercot141: the online-hours leg is a WIDER WINDOW on the bridge's own floor,
    # so it is meaningless (and silently inert) without the bridge — fail loud
    # rather than let an arm record the flag and solve the keeper unchanged.
    if (
        getattr(config, "ercot_gas_bridge_online_hours", False)
        and iso == "ERCOT"
        and not getattr(config, "ercot_gas_commitment_bridge", False)
    ):
        raise ValueError(
            "ercot_gas_bridge_online_hours requires ercot_gas_commitment_bridge: "
            "it widens that bridge's min-load floor from the idle gaps to every "
            "P0-online hour (no bridge, no floor to widen)."
        )
    if not bridge_on:
        return None, None

    # Per-P0-result memo: run_energy_solve calls the bid hook, then the fleet
    # hook, with the same r0 — the detector must run once for both.
    _memo: dict = {"key": None, "floor": None}

    def _floor_for(r0):
        key = id(r0)
        if _memo["key"] != key:
            _memo["key"] = key
            _memo["floor"] = _ercot_gas_bridge_floor(
                config, fleet, fleet_arrays, r0.dispatch, r0.prices, mc_base
            )
        return _memo["floor"]

    def _fleet_prep(r0):
        from market_sim.data.floor_mechanisms import MECH_GAS_COMMITMENT_BRIDGE

        bridge_floor = _floor_for(r0)
        if bridge_floor is None:
            return None
        return _bridge_floored_fleet(
            fleet_arrays, bridge_floor, MECH_GAS_COMMITMENT_BRIDGE
        )

    bid_prep = None
    if floorscoped and floorscoped_markdown_fn is not None:

        def bid_prep(r0):
            bridge_floor = _floor_for(r0)
            if bridge_floor is None:
                return None
            return floorscoped_markdown_fn(bridge_floor > 0.0)

    return _fleet_prep, bid_prep


#: ercot-227 F3: measured-class token → plant_group members (direct — the
#: derive already writes plant-group vocabulary; CHP variants excluded, the
#: RUC record's resource types are the merchant classes).
_ERCOT_RUC_CLASS_GROUPS: dict[str, tuple[str, ...]] = {
    "CC_REGULAR": ("CC_REGULAR",),
    "ST_GAS": ("ST_GAS",),
    "CT_PEAKER": ("CT_PEAKER",),
    "COAL": ("COAL",),
}


def _ercot_ruc_floor(config, fleet_arrays) -> "np.ndarray | None":
    """Build the ``(n_gen, T)`` measured RUC-instruction commitment floor.

    ercot-227 F3 (``ercot_ruc_commitment_floor``, PRECOMMIT-ercot226 §5.11
    Amendment 3, owner waiver W-3): per class-hour, the measured ONRUC LSL
    sum (:func:`results.scarcity.ercot_ruc_committed_mw`) distributed
    pro-rata over the class members' available capacity (clipped at the
    class's own capability — data-vs-data, no free parameter). The floor is
    zero wherever the measured series is zero, so its window IS the
    instruction set (off-window binding impossible by construction) and an
    uncovered year is byte-identical to flag-off. Returns ``None`` when
    nothing floors.
    """
    from market_sim.results.scarcity import ercot_ruc_committed_mw

    pg = getattr(fleet_arrays, "plant_group", None)
    if pg is None:
        return None
    pg = np.asarray(pg)
    T = int(fleet_arrays.availability.shape[1])
    year = int(getattr(config, "weather_year"))
    cap = fleet_arrays.pmax[:, None] * np.asarray(
        fleet_arrays.availability, dtype=float
    )
    floor = None
    armed: list[str] = []
    skipped: list[str] = []
    for token, groups in _ERCOT_RUC_CLASS_GROUPS.items():
        series = np.asarray(ercot_ruc_committed_mw(year, T, token), float)
        if series.max() <= 0.0:
            skipped.append(f"{token}(no measured ONRUC)")
            continue
        mask = np.isin(pg, list(groups))
        if not mask.any():
            skipped.append(f"{token}(no fleet units)")
            continue
        armed.append(f"{token}: {int((series > 0).sum())} h, max {series.max():.0f} MW")
        cls_cap = cap[mask].sum(axis=0)  # (T,)
        with np.errstate(invalid="ignore", divide="ignore"):
            level = np.where(cls_cap > 0.0, np.minimum(series, cls_cap), 0.0)
            share = np.where(cls_cap > 0.0, level / cls_cap, 0.0)  # (T,)
        contrib = cap[mask] * share[None, :]  # pro-rata, each ≤ own cap
        if floor is None:
            floor = np.zeros_like(cap)
        floor[mask] = np.maximum(floor[mask], contrib)
    print(
        f"INFO: ERCOT RUC instruction-state commitment floor ({year}): "
        f"ARMED [{'; '.join(armed) or 'none'}]"
        + (f", SKIPPED [{'; '.join(skipped)}]" if skipped else "")
    )
    if floor is None or float(floor.max()) <= 0.0:
        return None
    return floor


def wrap_ercot_ruc_floor_prep(config, iso: str, fleet_arrays, base_prep):
    """Chain the measured RUC-instruction floor after ``base_prep``.

    Wraps the (possibly ``None``) ERCOT ``p1_fleet_prep`` so the F3 floor
    composes AFTER the gas commitment bridge's floor on the same fleet —
    maximum-composition with per-mechanism attribution via
    :func:`_bridge_floored_fleet` (ties keep the incumbent id: the bridge on
    CC and the ST_GAS drag remain the rule-19 owners wherever they already
    floor at least as high). Returns ``base_prep`` unchanged when the flag
    is off or the ISO is not ERCOT (byte-identical).
    """
    if not (getattr(config, "ercot_ruc_commitment_floor", False) and iso == "ERCOT"):
        return base_prep

    from market_sim.data.floor_mechanisms import MECH_ERCOT_RUC_COMMITMENT

    def _ruc_prep(r0, _base=base_prep):
        floored = _base(r0) if _base is not None else None
        base_fa = floored if floored is not None else fleet_arrays
        ruc_floor = _ercot_ruc_floor(config, base_fa)
        if ruc_floor is None:
            return floored
        return _bridge_floored_fleet(base_fa, ruc_floor, MECH_ERCOT_RUC_COMMITMENT)

    return _ruc_prep


# NYISO gas commitment bridge: the merchant slow-start gas fuels it floors by
# default. ``gas_cc`` is the CC_REGULAR class, ``gas_st`` the ST_GAS class; the
# detector excludes every ``*_CHP`` group on top (cogens follow their steam
# host). The fast-start CT class is NOT in this default set: it is added by
# ``ScenarioConfig.nyiso_gas_bridge_ct`` (nyiso-90) and, when added, can only
# ever reach the ``min_run_hours`` extension leg — its 1 h min-down makes the
# physical bridge unreachable and fails ``RA_BRIDGE_ECON_MIN_DOWN_HOURS`` (4 h)
# for the economic one, so it is still never HELD ACROSS an idle gap
# (rule 18 [R-PHYSICS], nyiso-87 preserved). Scoping is still by unit physics
# inside the detector; this tuple only says which fuels the caller offers it.
_NYISO_BRIDGE_FUELS: tuple[str, ...] = ("gas_cc", "gas_st")

# The CT leg's fuel type, added to the per-class loop when armed.
_NYISO_CT_FUEL: str = "gas_ct"


def _nyiso_bridge_min_load_fracs(config) -> dict[str, float]:
    """Return ``{fuel_type: min_load_frac}`` for the bridge legs that are armed.

    The two slow-start legs are always offered (their fracs are measured class
    constants); the fast-start CT leg is added only when
    ``nyiso_gas_bridge_ct`` AND ``nyiso_gas_bridge_min_run`` are both on —
    without the min-run extension the CT leg has no reachable leg at all and
    would be silently inert (nyiso-89 §4a: an inert arm reads as "the mechanism
    does nothing", the most dangerous failure mode).

    Args:
        config: The run's ``ScenarioConfig``.

    Returns:
        Mapping of LP fuel type to that class's minimum-stable-load fraction.
    """
    out = {
        "gas_cc": float(config.nyiso_gas_bridge_cc_min_load_frac),
        "gas_st": float(config.nyiso_gas_bridge_st_min_load_frac),
    }
    if getattr(config, "nyiso_gas_bridge_ct", False):
        if not getattr(config, "nyiso_gas_bridge_min_run", False):
            logger.warning(
                "nyiso_gas_bridge_ct is ON but nyiso_gas_bridge_min_run is OFF "
                "— the CT leg has no reachable leg (a 1 h min-down unit can "
                "neither physically nor economically bridge) and is INERT. "
                "Not arming it."
            )
        else:
            out[_NYISO_CT_FUEL] = float(config.nyiso_gas_bridge_ct_min_load_frac)
    return out


def _nyiso_bridge_min_run_hours(config, fleet: list, fleet_arrays) -> np.ndarray:
    """Return the ``(n_gen,)`` minimum run duration for the NYISO bridge.

    Per-unit minimum-run physics for the ``min_run_hours`` extension. The
    default source is the published class table
    (``COMMITMENT_PARAMS_BY_FUEL``, NREL/SR-5500-55433) keyed by the unit's own
    heat rate — the same table the bridge already reads min-down and startup
    cost from, so the extension adds no new parameter at its default. The two
    per-class config overrides (``nyiso_gas_bridge_cc_min_run_hours`` /
    ``..._st_min_run_hours``) exist for the identification sweep and MUST be
    set from the measured CAMPD run-length artifact when a keeper adopts one
    (rule 23 [R-FROZEN-DERIVE]), never from a residual.

    Units the bridge cannot floor anyway (wrong fuel, a cogen, an incremental
    tranche with no startup cost) carry 0 — the detector skips them before it
    reads this array, so their value is inert either way.

    PER-PLANT identification (``nyiso_gas_bridge_plant_min_run``, nyiso-146):
    the class is not one run-length population (measured per-plant p25 spans
    7-646 h against a 21 h class scalar), so when the gate is on, a slow-start
    row whose plant appears in the measured artifact
    (``data/raw/_processed-legacy/campd_perplant_min_run_{ISO}.csv``) takes
    ITS OWN plant's measured value — REPLACING the class scalar for covered
    plants, never stacking on it (rule 19 [R-ONE-MECH]). Uncovered plants
    (no CAMPD series, the mixed-class drops, the misaligned Astoria campus
    pair) keep the class fallback below, and the armed CT leg keeps its own
    REQUIRED measured horizon (the artifact never covers gas_ct rows). The
    same miso-113 per-gen-vector convention as
    ``min_load_frac_by_gen``; gated default off so a control run is
    byte-identical.

    Args:
        config: The run's ``ScenarioConfig``.
        fleet: The dispatch fleet, aligned with ``fleet_arrays`` rows.
        fleet_arrays: The vectorized fleet, for ``heat_rate``.

    Returns:
        A ``(n_gen,)`` float array of minimum run hours.
    """
    from market_sim.data.perplant_min_run import load_perplant_min_run
    from market_sim.model.commitment import COMMITMENT_PARAMS_BY_FUEL

    hr = np.asarray(fleet_arrays.heat_rate, dtype=float)
    override = {
        "gas_cc": getattr(config, "nyiso_gas_bridge_cc_min_run_hours", None),
        "gas_st": getattr(config, "nyiso_gas_bridge_st_min_run_hours", None),
    }
    fuels = set(_NYISO_BRIDGE_FUELS)
    if getattr(config, "nyiso_gas_bridge_ct", False):
        # CT block commitment (nyiso-90): the measured horizon is REQUIRED, not
        # a class-table fallback — the NREL CT rows carry min_run_hours = 1,
        # which extends nothing, so falling back would make the leg inert.
        fuels.add(_NYISO_CT_FUEL)
        override[_NYISO_CT_FUEL] = float(config.nyiso_gas_bridge_ct_min_run_hours)
    per_plant: dict[int, float] = (
        load_perplant_min_run(str(getattr(config, "iso", "")))
        if getattr(config, "nyiso_gas_bridge_plant_min_run", False)
        else {}
    )
    covered = 0
    out = np.zeros(len(fleet), dtype=float)
    for g, gen in enumerate(fleet):
        fuel = gen.fuel_type
        if fuel not in fuels or gen.plant_group.endswith("_CHP"):
            continue
        # Per-plant replacement fires only on the slow-start classes the
        # artifact measures — never the CT leg, whose measured horizon is its
        # own required field above.
        if fuel in _NYISO_BRIDGE_FUELS:
            pp = per_plant.get(int(getattr(gen, "plant_code", 0) or 0))
            if pp is not None:
                out[g] = float(pp)
                covered += 1
                continue
        ov = override.get(fuel)
        if ov is not None:
            out[g] = float(ov)
            continue
        table = COMMITMENT_PARAMS_BY_FUEL.get(fuel)
        if table is None:
            continue
        params = table[-1][1]
        for cutoff, p in table:
            if hr[g] < cutoff:
                params = p
                break
        out[g] = float(params["min_run_hours"])
    if per_plant:
        logger.info(
            "NYISO gas bridge per-plant min-run identification: %d measured "
            "plant(s) in the artifact, matching %d fleet row(s); uncovered "
            "rows keep the class fallback",
            len(per_plant),
            covered,
        )
    return out


def _nyiso_gas_bridge_floor(
    config,
    fleet: list,
    fleet_arrays,
    p0_dispatch: np.ndarray,
    p0_prices: np.ndarray | None,
    mc_base: np.ndarray,
) -> np.ndarray | None:
    """Compute the raw ``(n_gen, T)`` NYISO gas commitment-bridge floor.

    Runs the ISO-neutral detector ONCE PER CLASS, because the measured minimum
    stable load differs by an order of scale between the two eligible classes
    (CC 0.523 vs ST_GAS 0.239 — CAMPD 2023-2025,
    ``scripts/data/derive_campd_gas_commitment_params.py``) and the detector
    takes a single scalar ``min_load_frac``. The per-class floors are composed
    by maximum, which is exact here: the two calls floor disjoint rows (a unit
    has one fuel type), so the maximum is a concatenation, not a stack.

    Returns ``None`` when neither class produces a floor.
    """
    from market_sim.config.constants import DA_COMMITMENT_HORIZON_HOURS
    from market_sim.data.bridge_layup_exclusions import load_layup_exclusions
    from market_sim.model.commitment import caiso_ra_mustoffer_min_gen, find_runs

    startup_bridge = bool(getattr(config, "nyiso_gas_bridge_startup", True))
    # COMMITMENT-REAL RUN SCREEN (nyiso-200, ``nyiso_gas_bridge_startup_aware``):
    # the detector's G-61 path (b) leg — a detected P0 run anchors ANY leg
    # (min-run extension, online-hours state floor, gap bridges) only when its
    # P0 energy margin per MW repays the unit's own published startup cost
    # (_ra_bridge_unit_params, the same constant the economic bridge prices).
    # Removes the P0-pattern dependence nyiso-199 §8.3 measured: a phantom
    # fragment a merit change manufactures can no longer be extended into a
    # min-load hold. Needs the P0 duals + base MC whether or not the economic
    # leg is armed. Zero new parameters; default off is byte-identical.
    startup_aware = bool(getattr(config, "nyiso_gas_bridge_startup_aware", False))
    need_econ = startup_bridge or startup_aware
    # ONLINE-HOURS LSL leg (nyiso-146 successor; the ercot141 detector leg on
    # NYISO's own evidence): floor the base tranche at min-load in EVERY hour
    # the P0 pattern has the plant online, not only across idle gaps — the
    # committed STATE the gap legs interpolate between. Same detector, same
    # measured fractions, same D-2 id; a wider window on one mechanism
    # (rule 19 [R-ONE-MECH]). CC-SCOPED: the nyiso-146 evidence (Bethlehem's
    # P1 fragmentation inside P0-committed hours) is combined-cycle conduct;
    # NYISO's gas-steam fleet cycles diurnally by its own meter and carries no
    # such evidence, so the leg arms only the gas_cc detector call (the same
    # evidence-scoping as the ERCOT leg, whose bridge is gas_cc-only).
    online_hours = bool(getattr(config, "nyiso_gas_bridge_online_hours", False))
    max_gap = (
        float(DA_COMMITMENT_HORIZON_HOURS)
        if getattr(config, "nyiso_gas_bridge_da_horizon", True)
        else None
    )
    min_run = (
        _nyiso_bridge_min_run_hours(config, fleet, fleet_arrays)
        if getattr(config, "nyiso_gas_bridge_min_run", False)
        else None
    )
    # MEMBERSHIP correction (nyiso_gas_bridge_plant_exclusions): a plant in
    # economic lay-up is not in the day-ahead commitment population at all, so
    # bridging it holds a mothballed boiler at min load across gaps it never
    # operated in (rule 17 [R-FLOOR-WINDOW]). Expressed through the detector's
    # own population gate — a non-positive min_load_frac_by_gen entry scopes the
    # row out — so no new detector parameter and no class-name tuple is needed
    # (the miso-113 convention; rule 18 [R-PHYSICS] keeps ELIGIBILITY on
    # _ra_bridge_unit_params' min-down/startup physics). Gated: with the flag
    # off the vector is None and every leg is byte-identical.
    excluded = (
        load_layup_exclusions("NYISO")
        if getattr(config, "nyiso_gas_bridge_plant_exclusions", False)
        else frozenset()
    )
    if excluded:
        in_pop = sum(
            1 for gen in fleet if int(getattr(gen, "plant_code", 0) or 0) in excluded
        )
        logger.info(
            "NYISO gas bridge membership correction: %d laid-up plant code(s) "
            "excluded, matching %d fleet row(s) — %s",
            len(excluded),
            in_pop,
            sorted(excluded),
        )
    # RESERVE-DUTY membership channel (nyiso_gas_bridge_reserve_duty_exclusions,
    # nyiso-152): the measured capacity-only CC cohort is not in the day-ahead
    # energy-commitment population either, and the lay-up channel above cannot
    # reach a plant with no CAMPD series (its criterion is CAMPD-defined).
    # Same population-gate expression, second measured membership signal —
    # rule 17 [R-FLOOR-WINDOW] / rule 19 [R-ONE-MECH]; see the field's
    # ScenarioConfig citation block.
    if getattr(config, "nyiso_gas_bridge_reserve_duty_exclusions", False):
        from market_sim.data.reserve_duty import load_reserve_duty_cc

        duty = load_reserve_duty_cc("NYISO")
        if duty:
            in_pop = sum(
                1 for gen in fleet if int(getattr(gen, "plant_code", 0) or 0) in duty
            )
            logger.info(
                "NYISO gas bridge reserve-duty membership correction: %d "
                "capacity-only plant code(s) excluded, matching %d fleet "
                "row(s) — %s",
                len(duty),
                in_pop,
                sorted(duty),
            )
            excluded = frozenset(excluded | duty)
    # STATE-FLOOR DUTY SCOPING (nyiso_gas_bridge_state_floor_min_run, the
    # nyiso-146b sharpening): the online-hours leg holds only plants whose
    # OWN measured run-length p25 clears the population gap
    # (constants.NYISO_STATE_FLOOR_MIN_RUN_HOURS — near-baseload conduct:
    # Bethlehem/Caithness/Poletti at 130-646 h, against the cyclers at
    # 7-20 h that the unscoped arm over-glued). Expressed by SPLITTING the
    # gas_cc detector call into a state cohort (floor_online_hours=True) and
    # the rest (False), partitioned through the detector's own population
    # gate (min_load_frac_by_gen zeroing) — the floors compose by maximum
    # over disjoint rows, so the split is exact and no detector parameter is
    # added.
    state_scoped = online_hours and bool(
        getattr(config, "nyiso_gas_bridge_state_floor_min_run", False)
    )
    state_cohort: frozenset[int] = frozenset()
    if state_scoped:
        from market_sim.config.constants import NYISO_STATE_FLOOR_MIN_RUN_HOURS
        from market_sim.data.perplant_min_run import load_perplant_min_run

        state_cohort = frozenset(
            code
            for code, hours in load_perplant_min_run(
                str(getattr(config, "iso", ""))
            ).items()
            if hours >= NYISO_STATE_FLOOR_MIN_RUN_HOURS
        )
        logger.info(
            "NYISO state-floor duty scoping: %d plant(s) clear the measured "
            "run-length gap and carry the online-hours floor — %s",
            len(state_cohort),
            sorted(state_cohort),
        )
    per_class = _nyiso_bridge_min_load_fracs(config)
    total = None
    legs: list[tuple[str, float, np.ndarray | None, bool]] = []
    for fuel, frac in per_class.items():
        if frac <= 0.0:
            continue
        frac_by_gen = None
        if excluded:
            frac_by_gen = np.array(
                [
                    0.0 if int(getattr(gen, "plant_code", 0) or 0) in excluded else frac
                    for gen in fleet
                ],
                dtype=float,
            )
        if state_scoped and fuel == "gas_cc":
            base = (
                frac_by_gen
                if frac_by_gen is not None
                else np.full(len(fleet), frac, dtype=float)
            )
            in_cohort = np.array(
                [
                    int(getattr(gen, "plant_code", 0) or 0) in state_cohort
                    for gen in fleet
                ]
            )
            legs.append((fuel, frac, np.where(in_cohort, base, 0.0), True))
            legs.append((fuel, frac, np.where(in_cohort, 0.0, base), False))
        else:
            legs.append((fuel, frac, frac_by_gen, online_hours and fuel == "gas_cc"))
    screen_census: dict = {}
    plant_census: dict = {}
    for fuel, frac, frac_by_gen, leg_online in legs:
        leg_stats: dict = {}
        part = caiso_ra_mustoffer_min_gen(
            p0_dispatch,
            fleet_arrays,
            fleet,
            frac,
            p1_prices=p0_prices if need_econ else None,
            base_mc=mc_base if need_econ else None,
            startup_bridge=startup_bridge,
            fuel_types=(fuel,),
            max_econ_gap_hours=max_gap,
            min_run_hours=min_run,
            floor_online_hours=leg_online,
            min_load_frac_by_gen=frac_by_gen,
            startup_aware=startup_aware,
            screen_stats=leg_stats if startup_aware else None,
        )
        if startup_aware:
            # The screen's own census, per leg — the mechanism's arithmetic
            # stated in the log so a rule-29 screen reads what it DID (runs
            # dropped, P0 hours de-anchored) and not only what the residual
            # did. Logged even when zero (nyiso-89 §4a: an inert arm must
            # read as inert, never as "the mechanism does nothing").
            k = f"{fuel}{'_state' if leg_online else ''}"
            screen_census[k] = {
                "runs_detected": int(leg_stats.get("runs_detected", 0)),
                "runs_dropped": int(leg_stats.get("runs_dropped", 0)),
                "dropped_hours": int(leg_stats.get("dropped_hours", 0)),
                "units_with_drops": len(leg_stats.get("units_with_drops", [])),
            }
            # PER-PLANT roll-up of the per-unit census (nyiso-201). The screen
            # claims by construction that no floor leg anchors on a dropped
            # run; a plant carrying bridge floor with ZERO kept runs would
            # falsify it. Logged so a rule-29 screen can check the identity at
            # the grain its named-plant gate is written in, rather than assert
            # it from the code path. Diagnostics only.
            for g_idx, cen in (leg_stats.get("per_unit") or {}).items():
                code = int(getattr(fleet[int(g_idx)], "plant_code", 0) or 0)
                acc = plant_census.setdefault(
                    code, {"detected": 0, "kept": 0, "dropped": 0, "dropped_hours": 0}
                )
                for f in acc:
                    acc[f] += int(cen.get(f, 0))
            logger.info(
                "NYISO gas bridge commitment-real run screen, leg %s: %d P0 "
                "runs detected, %d dropped as phantom (margin < startup) "
                "covering %d P0 online hours at %d unit(s)",
                k,
                screen_census[k]["runs_detected"],
                screen_census[k]["runs_dropped"],
                screen_census[k]["dropped_hours"],
                screen_census[k]["units_with_drops"],
            )
        # PER-CLASS trace. The composed total cannot show that one leg
        # contributed nothing, and a leg that floors zero unit-hours is exactly
        # the "mechanism is inert" failure nyiso-89 §4a warns reads as a
        # structural finding. Logged for every armed leg, including zero.
        logger.info(
            "NYISO gas bridge leg %s (min_load_frac %.3f, min_run %s): "
            "%d unit-hours floored, %.4f TWh floor volume",
            fuel,
            frac,
            (
                "off"
                if min_run is None
                else "{:.0f}h".format(
                    max(
                        (
                            min_run[g]
                            for g, gen in enumerate(fleet)
                            if gen.fuel_type == fuel
                        ),
                        default=0.0,
                    )
                )
            ),
            int((part > 0.0).sum()),
            float(part.sum()) / 1e6,
        )
        total = part if total is None else np.maximum(total, part)
    if startup_aware and plant_census:
        # One line per plant with detected P0 runs, sorted by plant code, so a
        # rule-29 screen can read the run screen's action at the grain its
        # named-plant gate is written in (nyiso-201 gate (b) identity leg).
        logger.info(
            "NYISO gas bridge run screen per-plant census: %s",
            ";".join(
                "{}:{}/{}/{}/{}".format(
                    c,
                    plant_census[c]["detected"],
                    plant_census[c]["kept"],
                    plant_census[c]["dropped"],
                    plant_census[c]["dropped_hours"],
                )
                for c in sorted(plant_census)
            ),
        )
    if total is None or not np.any(total > 0.0):
        return None
    # Diagnostic trace for the D-4 window analysis: every floored segment is
    # either a bridged idle gap or a min-run extension, so its length
    # distribution is the direct evidence the declared window is what binds.
    seg_lengths = [
        e - s
        for g in np.flatnonzero((total > 0.0).any(axis=1))
        for s, e in find_runs(total[g] > 0.0)
    ]
    if seg_lengths:
        seg = np.array(seg_lengths)
        buckets = {
            "<4h": int((seg < 4).sum()),
            "4-8h": int(((seg >= 4) & (seg < 8)).sum()),
            "8-16h": int(((seg >= 8) & (seg < 16)).sum()),
            "16-24h": int(((seg >= 16) & (seg <= 24)).sum()),
            ">24h": int((seg > 24).sum()),
        }
        logger.info(
            "NYISO gas commitment bridge: %d unit-hours floored "
            "(%.2f TWh floor volume), %d floored segments by length %s "
            "(min_run extension %s)",
            int((total > 0.0).sum()),
            float(total.sum()) / 1e6,
            len(seg_lengths),
            buckets,
            "ON" if min_run is not None else "off",
        )
    return total


def build_nyiso_gas_bridge_p1_prep(
    config, iso: str, fleet: list, fleet_arrays, mc_base
):
    """Return a ``p1_fleet_prep`` hook for the NYISO gas commitment bridge.

    The P1-native replacement for the h14-21 peak-window reliability-floor
    limbs (owner directive 2026-07-27, nyiso-87): instead of a temperature
    boxcar asserting that downstate steam and peakers run in fixed afternoon
    hours, the merchant slow-start gas fleet is held at minimum stable load by
    its OWN commitment physics — minimum run duration, minimum down time, and
    the startup-restart inequality priced at the model's own P0 duals. Detector:
    :func:`_nyiso_gas_bridge_floor`; D-2 attribution:
    ``MECH_NYISO_GAS_COMMITMENT_BRIDGE``.

    Returns ``None`` when the mechanism is off or the ISO is not NYISO, so
    every other path is byte-identical. ISO-exclusive with the CAISO, ERCOT and
    PJM P1-prep hooks by construction (each gates on its own ISO).
    """
    if not (getattr(config, "nyiso_gas_commitment_bridge", False) and iso == "NYISO"):
        return None

    from market_sim.data.floor_mechanisms import MECH_NYISO_GAS_COMMITMENT_BRIDGE

    def _fleet_prep(r0):
        bridge_floor = _nyiso_gas_bridge_floor(
            config, fleet, fleet_arrays, r0.dispatch, r0.prices, mc_base
        )
        if bridge_floor is None:
            return None
        return _bridge_floored_fleet(
            fleet_arrays, bridge_floor, MECH_NYISO_GAS_COMMITMENT_BRIDGE
        )

    return _fleet_prep


# SPP gas commitment bridge (SPP-44): the merchant slow-start gas fuels the
# SPP leg offers the shared detector. ``gas_cc`` is the CC_REGULAR class,
# ``gas_st`` the ST_GAS class; the detector excludes every ``*_CHP`` group on
# top (cogens follow their steam host). The fast-start CT class is NOT offered:
# on keeper-2's fleet every gas_ct committed tranche resolves a 1 h min-down /
# $20 per MW start, so the physical bridge is unreachable and
# RA_BRIDGE_ECON_MIN_DOWN_HOURS refuses the economic leg — it would be inert by
# physics even if offered (rule 18 [R-PHYSICS]; spp44/census_eligibility.py).
# Scoping is still by unit physics inside the detector; this tuple only names
# the populations the two measured constants describe.
_SPP_BRIDGE_FUELS: tuple[str, ...] = ("gas_cc", "gas_st")


def _spp_bridge_min_run_hours(fleet: list, fleet_arrays) -> np.ndarray:
    """Return the ``(n_gen,)`` minimum run duration for the SPP bridge.

    The MEASURED plant-basis class values
    (``constants.SPP_GAS_BRIDGE_MIN_RUN_HOURS``, the cap-weighted p25 of the
    CAMPD 2023-2025 plant run-length distribution: CC 15 h, ST_GAS 5 h), one
    per eligible fuel; every other row — the wrong fuel, a cogen — carries 0,
    which the detector reads as "no extension". No class table fallback and no
    per-plant channel: the SPP leg has exactly the two constants
    (PRECOMMIT-spp-44 §2.2 / §2.6).

    Args:
        fleet: The dispatch fleet, aligned with ``fleet_arrays`` rows.
        fleet_arrays: The vectorized fleet (row count only).

    Returns:
        A ``(n_gen,)`` float array of minimum run hours.
    """
    from market_sim.config.constants import SPP_GAS_BRIDGE_MIN_RUN_HOURS

    out = np.zeros(len(fleet), dtype=float)
    for g, gen in enumerate(fleet):
        if gen.fuel_type in _SPP_BRIDGE_FUELS and not gen.plant_group.endswith("_CHP"):
            out[g] = float(SPP_GAS_BRIDGE_MIN_RUN_HOURS[gen.fuel_type])
    return out


def _spp_gas_bridge_floor(
    fleet: list,
    fleet_arrays,
    p0_dispatch: np.ndarray,
    p0_prices: np.ndarray,
    mc_base: np.ndarray,
) -> np.ndarray | None:
    """Compute the raw ``(n_gen, T)`` SPP gas commitment-bridge floor.

    Runs the ISO-neutral detector ONCE PER CLASS (the NYISO precedent) because
    the measured plant-basis minimum stable load differs by more than 2x
    between the two eligible classes (CC 0.209 vs ST_GAS 0.090 —
    ``constants.SPP_GAS_BRIDGE_MIN_LOAD_FRAC``) and the detector takes one
    scalar. The per-class floors compose by maximum, which is exact: a unit
    has one fuel type, so the two calls floor disjoint rows.

    Legs, all fixed (PRECOMMIT-spp-44 §3): the physical restart bar, the
    economic restart inequality capped at one DA operating day, the measured
    minimum-run extension, and the commitment-real run screen
    (``startup_aware``). Every input is the model's own P0 solution plus
    registered physics and the four measured constants.

    Returns ``None`` when neither class produces a floor.
    """
    from market_sim.config.constants import (
        DA_COMMITMENT_HORIZON_HOURS,
        SPP_GAS_BRIDGE_MIN_LOAD_FRAC,
    )
    from market_sim.model.commitment import caiso_ra_mustoffer_min_gen, find_runs

    min_run = _spp_bridge_min_run_hours(fleet, fleet_arrays)
    total = None
    for fuel in _SPP_BRIDGE_FUELS:
        frac = float(SPP_GAS_BRIDGE_MIN_LOAD_FRAC[fuel])
        stats: dict = {}
        part = caiso_ra_mustoffer_min_gen(
            p0_dispatch,
            fleet_arrays,
            fleet,
            frac,
            p1_prices=p0_prices,
            base_mc=mc_base,
            startup_bridge=True,
            fuel_types=(fuel,),
            max_econ_gap_hours=float(DA_COMMITMENT_HORIZON_HOURS),
            min_run_hours=min_run,
            startup_aware=True,
            screen_stats=stats,
        )
        # PER-CLASS trace, logged even when zero: a leg that floors nothing is
        # exactly the "mechanism is inert" reading a rule-29 screen must be
        # able to see (nyiso-89 §4a), and the run-screen census is the
        # mechanism's own arithmetic stated in the log.
        logger.info(
            "SPP gas bridge leg %s (min_load_frac %.3f, min_run %.0fh): %d P0 runs "
            "detected, %d dropped as phantom (margin < startup) covering %d P0 "
            "online hours at %d unit(s); %d unit-hours floored, %.4f TWh floor volume",
            fuel,
            frac,
            max(
                (min_run[g] for g, gen in enumerate(fleet) if gen.fuel_type == fuel),
                default=0.0,
            ),
            int(stats.get("runs_detected", 0)),
            int(stats.get("runs_dropped", 0)),
            int(stats.get("dropped_hours", 0)),
            len(stats.get("units_with_drops", [])),
            int((part > 0.0).sum()),
            float(part.sum()) / 1e6,
        )
        total = part if total is None else np.maximum(total, part)
    if total is None or not np.any(total > 0.0):
        return None
    # D-4 trace: every floored segment is a bridged idle gap or a min-run
    # extension, so its length distribution is the direct evidence of the
    # declared self-windowing.
    seg = np.array(
        [
            e - s
            for g in np.flatnonzero((total > 0.0).any(axis=1))
            for s, e in find_runs(total[g] > 0.0)
        ]
    )
    if seg.size:
        logger.info(
            "SPP gas commitment bridge: %d unit-hours floored (%.2f TWh floor "
            "volume), %d floored segments by length %s",
            int((total > 0.0).sum()),
            float(total.sum()) / 1e6,
            int(seg.size),
            {
                "<4h": int((seg < 4).sum()),
                "4-8h": int(((seg >= 4) & (seg < 8)).sum()),
                "8-16h": int(((seg >= 8) & (seg < 16)).sum()),
                "16-24h": int(((seg >= 16) & (seg <= 24)).sum()),
                ">24h": int((seg > 24).sum()),
            },
        )
    return total


def build_spp_gas_bridge_p1_prep(config, iso: str, fleet: list, fleet_arrays, mc_base):
    """Return a ``p1_fleet_prep`` hook for the SPP gas commitment bridge.

    The SPP leg of the P1-native committed-state bridge family (lane SPP-44):
    SPP's merchant slow-start gas fleet — CC_REGULAR + ST_GAS by the rule-18
    physics gate — is held at its measured plant-basis minimum stable load by
    its own commitment physics (minimum run, minimum down, the restart
    inequality at the model's own P0 duals). Detector:
    :func:`_spp_gas_bridge_floor`; D-2 attribution:
    ``MECH_SPP_GAS_COMMITMENT_BRIDGE``.

    Returns ``None`` when the mechanism is off or the ISO is not SPP, so every
    other path is byte-identical. ISO-exclusive with the CAISO, ERCOT, NYISO,
    MISO and PJM P1-prep hooks by construction (each gates on its own ISO).
    """
    if not (getattr(config, "spp_gas_commitment_bridge", False) and iso == "SPP"):
        return None

    from market_sim.data.floor_mechanisms import MECH_SPP_GAS_COMMITMENT_BRIDGE

    def _fleet_prep(r0):
        bridge_floor = _spp_gas_bridge_floor(
            fleet, fleet_arrays, r0.dispatch, r0.prices, mc_base
        )
        if bridge_floor is None:
            return None
        return _bridge_floored_fleet(
            fleet_arrays, bridge_floor, MECH_SPP_GAS_COMMITMENT_BRIDGE
        )

    return _fleet_prep


_MISO_NIGHT_FLOOR_SUPPLIES = ("prb", "subbituminous")


def miso_coal_night_min_load_fracs(fleet: list) -> np.ndarray:
    """Return the ``(n_gen,)`` per-unit night-floor min-load fractions for MISO.

    The level leg of ``ScenarioConfig.miso_coal_night_floor`` (miso-113). For
    each regulated PRB/subbituminous CAMPD tranche the entry is that PLANT's
    own measured within-run night level NET of its own ``_mustrun`` band::

        frac_p = max(0, night_p50_p - must_run_pct_p / 100)

    ``night_p50`` is the frozen measured conduct input (p50 of plant load /
    HSL over ONLINE hours h0-5, pooled 2023-2025, WP-3 loading-when-on) read
    by :func:`data.fleet.campd_bins.coal_prb_committed_split_night` from
    ``coal_prb_committed_split_MISO.csv``; ``must_run_pct`` is the plant's own
    band, carried on the ``_committed`` tranche by ``bins_to_fleet``.

    **Subtracting the band is the rule 19 [R-ONE-MECH] reconciliation, not an
    adjustment.** The ``_mustrun`` tranche already occupies the bottom of the
    plant's stack at a fuel-free bid, so a floor written at the raw
    ``night_p50`` would deliver ``mustrun + night`` of forced output. Netting
    it makes the plant's TOTAL floor exactly ``night_p50 x plant capacity``,
    which is what the meter says. Merit order inside a plant (mustrun
    fuel-free < committed discounted < econ < peak) makes the identity exact.

    Every OTHER row is left at ``0.0``, which the detector reads as "not in
    this mechanism" and skips — the population gate is expressed as a level,
    so no class-name tuple is needed anywhere (rule 18 [R-PHYSICS] keeps the
    eligibility gate on ``_ra_bridge_unit_params``' min-down/startup physics,
    which admits only the ``_committed`` band).
    """
    from market_sim.data.fleet.campd_bins import coal_prb_committed_split_night
    from market_sim.data.fleet.eia860 import eia860_selfcommit_scope_plants

    night = coal_prb_committed_split_night("MISO")
    out = np.zeros(len(fleet), dtype=float)
    if not night:
        return out
    regulated = eia860_selfcommit_scope_plants()
    for g, gen in enumerate(fleet):
        if not getattr(gen, "is_campd_bin", False) or gen.fuel_type != "coal":
            continue
        if getattr(gen, "coal_supply", "") not in _MISO_NIGHT_FLOOR_SUPPLIES:
            continue
        code = int(getattr(gen, "plant_code", 0) or 0)
        # Population = the regulated SELF-COMMITMENT set (who self-commits is
        # a market-design fact, EIA-860 Regulatory Status / cost-of-service
        # majority ownership), the same scope the take-or-pay discount uses.
        if code not in regulated or code not in night:
            continue
        frac = float(night[code]) - float(getattr(gen, "must_run_pct", 0.0)) / 100.0
        if frac > 0.0:
            out[g] = frac
    return out


def _miso_coal_night_floor(
    config,
    fleet: list,
    fleet_arrays,
    p0_dispatch: np.ndarray,
) -> np.ndarray | None:
    """Compute the raw ``(n_gen, T)`` MISO regulated-coal night floor.

    Runs the ISO-neutral detector (:func:`model.commitment.
    caiso_ra_mustoffer_min_gen`) ONCE over the coal fleet with a PER-UNIT
    min-load vector (:func:`miso_coal_night_min_load_fracs`), because MISO's
    level is identified per plant rather than per class — the NYISO bridge's
    per-class loop generalized to per-plant without allocating one full floor
    array per plant.

    Legs armed: the ercot141 ONLINE-HOURS leg (``floor_online_hours``) plus
    the detector's unconditional physical restart bar (an idle gap shorter
    than the unit's own min-down cannot be a real cycle). The economic
    ``>=min-down`` startup leg is NOT armed: a gap at or beyond min-down is a
    next-day decommit/re-offer decision, outside this mechanism's declared
    rule-17 window (the detected committed run).

    Returns ``None`` when no plant is in scope or the detector floors nothing.
    """
    from market_sim.model.commitment import caiso_ra_mustoffer_min_gen, find_runs

    fracs = miso_coal_night_min_load_fracs(fleet)
    n_scoped = int((fracs > 0.0).sum())
    if n_scoped == 0:
        logger.info("MISO coal night floor: no plant in scope — inert")
        return None
    floor = caiso_ra_mustoffer_min_gen(
        p0_dispatch,
        fleet_arrays,
        fleet,
        0.0,  # unused: the per-unit vector supplies every level
        fuel_types=("coal",),
        floor_online_hours=True,
        min_load_frac_by_gen=fracs,
    )
    if not np.any(floor > 0.0):
        logger.info(
            "MISO coal night floor: %d scoped tranches, detector floored "
            "nothing (no P0 run) — inert",
            n_scoped,
        )
        return None
    # D-4 window evidence: with the online-hours leg armed a floored segment
    # IS a committed block (runs and any sub-min-down gap between them fuse),
    # so the segment-length distribution is the direct evidence that the
    # declared window — the detected committed run — is what binds.
    seg_lengths = [
        e - s
        for g in np.flatnonzero((floor > 0.0).any(axis=1))
        for s, e in find_runs(floor[g] > 0.0)
    ]
    seg = np.array(seg_lengths) if seg_lengths else np.zeros(0)
    logger.info(
        "MISO coal night floor: %d scoped tranches, %d unit-hours floored "
        "(%.3f TWh floor volume), %d committed blocks by length %s",
        n_scoped,
        int((floor > 0.0).sum()),
        float(floor.sum()) / 1e6,
        len(seg_lengths),
        {
            "<24h": int((seg < 24).sum()),
            "24-168h": int(((seg >= 24) & (seg < 168)).sum()),
            "168-720h": int(((seg >= 168) & (seg < 720)).sum()),
            ">720h": int((seg >= 720).sum()),
        },
    )
    return floor


def build_miso_coal_night_floor_p1_prep(config, iso: str, fleet: list, fleet_arrays):
    """Return a ``p1_fleet_prep`` hook for the MISO regulated-coal night floor.

    The P1-native committed-state floor on MISO's regulated PRB/subbituminous
    fleet (``ScenarioConfig.miso_coal_night_floor``, miso-113 — the successor
    to the two REJECTED offer-side arms, ``coal_prb_committed_dispatchable``
    (miso-111) and ``coal_prb_committed_split`` (miso-112)). Detector:
    :func:`_miso_coal_night_floor`; D-2 attribution:
    ``MECH_MISO_COAL_NIGHT_FLOOR``.

    ``preserve_absorption=True``: MISO runs priced export sinks
    (``miso_seam_export_limit`` / ``miso_seam_envelope_merit_cap``), and a
    zeros-initialised floor otherwise collapses every ``pmin < 0`` sink's
    lower bound to ``max(pmin, 0) = 0``, deleting the seam export outlet from
    the scored P1 while P0 keeps it — the defect FINDING-caiso138 §D measured
    on the CAISO corridor. Set from the start here rather than left to a
    later re-gate: this mechanism has no keeper to shift underneath.

    Returns ``None`` when the mechanism is off or the ISO is not MISO, so
    every other path is byte-identical. ISO-exclusive with the CAISO, ERCOT,
    NYISO and PJM P1-prep hooks by construction (each gates on its own ISO).
    """
    if not (getattr(config, "miso_coal_night_floor", False) and iso == "MISO"):
        return None

    from market_sim.data.floor_mechanisms import MECH_MISO_COAL_NIGHT_FLOOR

    def _fleet_prep(r0):
        floor = _miso_coal_night_floor(config, fleet, fleet_arrays, r0.dispatch)
        if floor is None:
            return None
        return _bridge_floored_fleet(
            fleet_arrays,
            floor,
            MECH_MISO_COAL_NIGHT_FLOOR,
            preserve_absorption=True,
        )

    return _fleet_prep


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


def _pjm_plant_online_pattern(fleet_arrays, p0_dispatch, eligible=None):
    """Derive the plant-online commitment pattern from the P0 run pattern.

    The shared P0 commitment-state derivation of the PJM path-B mask
    (:func:`pjm_commitment_scoped_reserve_fleet`), the pergen-sync product
    split (:func:`pjm_pergen_sync_reserve_caps`), and the CAISO online-scoped
    spin split (:func:`caiso_pergen_sync_reserve_caps`, which passes its
    ISO-local ``eligible`` mask — thermal + hydro; hydro has no commitment
    table so it counts fast-start by physics and is never min-down-bridged) —
    commitment state read from the model's own base-cost **P0** solve (the
    CAISO RA bridge convention: forward-derivable, condition-responsive, no
    measured series; rules 11/13):

    * A PLANT is online in hour ``t`` when any of its tranches dispatches in P0
      (``pjm-reserve-ordc.md`` honesty-gate measure: "a plant is synchronized
      when any of its tranches dispatch") — tranches are the same physical iron,
      so an online plant's unused tranche headroom stays available.
    * Offline gaps shorter than a non-fast-start plant's capacity-weighted
      min-down are bridged online (``model.commitment._merge_runs``): a unit
      physically cannot cycle off-and-back inside its min-down window, so it
      stayed synchronized through the gap. Physics-loosening only — the bridge
      can only ADD online hours, never manufacture tightness (rule 11).
    * Fast-start plants (capacity-weighted min-down ≤
      ``POSTURE_FAST_START_MIN_DOWN_H`` and startup <
      ``POSTURE_FAST_START_STARTUP_PER_MW`` — the rule-18 physics thresholds
      ``_posture_pool_params`` uses) are flagged in ``grp_fast``; they cycle
      freely, so their pattern is never min-down-bridged.

    Returns ``(online, group_of, grp_fast, eligible)``: the ``(n_grp, T)``
    plant-online pattern, each unit's plant-group index, the per-group
    fast-start flags, and the reserve-eligibility mask.
    """
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
    eligible = (
        _reserve_eligible(fleet_arrays)
        if eligible is None
        else np.asarray(eligible, dtype=bool)
    )
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

    # Plant online pattern from P0: any tranche dispatching -> the plant is
    # synchronized that hour (all its tranches' headroom stays available).
    online = np.zeros((n_grp, T), dtype=bool)
    np.logical_or.at(online, group_of, p0 > TOL_MW)

    # Bridge offline gaps shorter than the plant's min-down (loosening only;
    # non-fast-start plants only — fast-start iron cycles freely).
    for r in np.unique(group_of[gated]):
        md = float(grp_md[r])
        if md <= 1.0:
            continue
        runs = find_runs(online[r])
        if not runs:
            continue
        for start, end in _merge_runs(runs, md):
            online[r, start:end] = True

    return online, group_of, grp_fast, eligible


def pjm_commitment_scoped_reserve_fleet(config, fleet_arrays, p0_dispatch):
    """Return the P1 ``FleetArrays`` with the commitment-scoped reserve mask applied.

    PJM path B (G-20b): the fa_p2-style availability screen, made P1-native.
    ERCOT's AS-aware P2 zeroes decommitted units' availability so idle
    slow-start capacity leaves the reserve-headroom RHS
    (``apply_commitment_with_coal_pin`` + ``ercot_commitment_headroom_overrides``);
    P2 is archived, so PJM applies the same commitment-state re-scope *before*
    the single scored P1 solve, with the commitment state read from the model's
    own base-cost **P0** run pattern (:func:`_pjm_plant_online_pattern` — the
    plant-online derivation, min-down gap bridging, and rule-18 fast-start
    exemption all live there). Non-fast-start reserve-eligible units have
    availability zeroed in their plant's offline hours; fast-start units are
    NEVER masked (an offline 10-min CT/oil peaker still provides
    non-synchronized Primary reserve, Manual 11 sec 4.2, and can start within
    the operating hour).

    A ``min_gen``-floored unit-hour is online by construction (P0 solves the
    same floors, so ``P0 >= min_gen > 0`` there) — no floor is ever masked.
    Returns ``None`` when the P0 pattern masks nothing (caller keeps the
    ordinary warm-started P1).
    """
    import dataclasses

    online, group_of, grp_fast, eligible = _pjm_plant_online_pattern(
        fleet_arrays, p0_dispatch
    )
    gated = eligible & ~grp_fast[group_of]
    if not gated.any():
        return None

    masked = gated[:, None] & ~online[group_of]
    if not masked.any():
        return None
    avail = np.where(masked, 0.0, fleet_arrays.availability)
    return dataclasses.replace(
        fleet_arrays,
        availability=avail,
        pmin=fleet_arrays.pmin.copy(),
    )


def pjm_pergen_sync_reserve_caps(config, fleet_arrays, p0_dispatch):
    """P1 ramp caps ``(2*n_r, T)`` for the ``pjm_reserve_pergen_sync`` product split.

    The per-gen opportunity-cost co-opt's online scoping, applied to the
    RESERVE bounds only (energy availability is NOT masked — P1's free energy
    redispatch around the held reserve is what prices the sub-shortage
    opportunity cost). Column products, per Manual 11 sec 4.2:

    * **SYNC columns** ``[0, n_r)``: Σ ONLINE members' availability-scaled
      ``ramp10`` per (zone, fuel-class) pool — synchronized reserve can come
      only from synchronized (online) iron, fast-start included: an offline
      10-min CT is not synchronized, so its ramp moves to the non-sync column.
    * **NON-SYNC columns** ``[n_r, 2*n_r)``: Σ OFFLINE FAST-START members'
      ``ramp10`` — offline 10-min-startable capacity provides non-synchronized
      Primary reserve; its award still consumes the pool's ramp (this bound)
      and capacity headroom (the shared joint P+R row). Offline non-fast-start
      capacity backs nothing.

    The online pattern is the pjm-85 P0 plant-online derivation
    (:func:`_pjm_plant_online_pattern`: any-tranche-dispatching, min-down gaps
    bridged, rule-18 physics fast-start flags) — commitment state from the
    model's own P0 solve, forward-regenerating and condition-responsive
    (rules 11/13). Pooling comes from ``reserve_config.pjm_pergen_structure``,
    the same helper ``_pjm_design`` builds the layout from, so the column
    order is identical by construction.
    """
    from market_sim.config.reserve_config import (
        PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE,
        pjm_pergen_pool_ramp10,
        pjm_pergen_structure,
    )

    size_split = (
        PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE
        if getattr(config, "pjm_reserve_pergen_size_split", False)
        else None
    )
    gen_idx, col, n_r = pjm_pergen_structure(
        fleet_arrays, size_split_mean_multiple=size_split
    )
    online, group_of, grp_fast, _eligible = _pjm_plant_online_pattern(
        fleet_arrays, p0_dispatch
    )
    online_member = online[group_of[gen_idx]]  # (n_members, T) bool
    fast_member = grp_fast[group_of[gen_idx]]  # (n_members,) bool
    sync = pjm_pergen_pool_ramp10(
        fleet_arrays, gen_idx, col, n_r, member_mask=online_member
    )
    nonsync = pjm_pergen_pool_ramp10(
        fleet_arrays,
        gen_idx,
        col,
        n_r,
        member_mask=(~online_member) & fast_member[:, np.newaxis],
    )
    del online_member
    caps = np.vstack([sync, nonsync])
    del sync, nonsync
    return caps


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

    Per-gen sync split (``pjm_reserve_pergen_sync``, the G-20b successor):
    the kwargs hook recomputes the ``(2*n_r, T)`` product-split ramp caps
    (:func:`pjm_pergen_sync_reserve_caps`) from the P0 run pattern — SYNC
    columns scoped to online iron, NON-SYNC to offline fast-start — with NO
    fleet hook (energy availability is never masked; the free P1 energy
    redispatch is what prices the opportunity cost).

    Raises on a stacked path-A/path-B/pergen config: the online-gate proxy,
    the availability mask, and the per-pool product split scope the same
    phenomenon (one mechanism per phenomenon, rule 19) — enable exactly one.
    """
    if not (iso == "PJM" and getattr(config, "energy_reserve_coopt", False)):
        return None, None
    if getattr(config, "pjm_reserve_pergen_sync", False):
        if not getattr(config, "pjm_reserve_pergen", False):
            raise ValueError(
                "pjm_reserve_pergen_sync requires pjm_reserve_pergen (the "
                "product split rides the per-gen (zone, fuel-class) layout)"
            )
        if getattr(config, "pjm_reserve_commitment_scoped", False) or getattr(
            config, "pjm_reserve_online_gated", False
        ):
            raise ValueError(
                "pjm_reserve_pergen_sync is mutually exclusive with "
                "pjm_reserve_commitment_scoped (path B) and "
                "pjm_reserve_online_gated (path A) — enable exactly one "
                "reserve-supply scoping (CLAUDE.md rule 19: one mechanism "
                "per phenomenon)"
            )

        def _sync_kwargs_prep(r0, p1_fleet_arrays):
            # Recompute the product-split ramp caps on the P0 run pattern.
            # Bounds-only override: same LP dimensions, cold P1 (the seam
            # releases the P0 model first — the memory-friendly path).
            return {
                "reserve_pergen_ramp10": pjm_pergen_sync_reserve_caps(
                    config, fleet_arrays, r0.dispatch
                )
            }

        return None, _sync_kwargs_prep
    if not getattr(config, "pjm_reserve_commitment_scoped", False):
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


def caiso_pergen_sync_reserve_caps(config, fleet_arrays, p0_dispatch):
    """P1 ramp caps ``(2*n_r, T)`` for the ``caiso_reserve_online_scoped`` split.

    The CAISO port of :func:`pjm_pergen_sync_reserve_caps` — tariff products
    Spinning / Non-Spinning instead of Synchronized / Non-Synchronized:

    * **SPIN columns** ``[0, n_r)``: Σ ONLINE members' availability-scaled
      10-minute deliverable ramp per (zone, fuel-class) pool — spinning
      reserve is *synchronized* capacity (CAISO tariff §8.4 / Appendix K AS
      certification: 10-minute full conversion FROM a synchronized state), so
      only online iron backs it, fast-start and hydro included; an offline
      10-minute CT is not synchronized, so its ramp moves to the non-spin
      column.
    * **NONSPIN columns** ``[n_r, 2*n_r)``: Σ OFFLINE FAST-START members'
      ramp — non-spinning reserve is 10-minute-startable offline capacity;
      its award still consumes the pool's ramp (this bound) and capacity
      headroom (the shared joint P+R row). Offline non-fast-start capacity
      (a cold CC/ST) backs nothing.

    The online pattern is the shared P0 plant-online derivation
    (:func:`_pjm_plant_online_pattern`: any-tranche-dispatching, min-down
    gaps bridged, rule-18 physics fast-start flags), evaluated over the
    CAISO-local eligibility (thermal + hydro — hydro has no commitment table,
    so it counts fast-start by physics and cycles freely). Commitment state
    comes from the model's own base-cost **P0** solve — forward-regenerating
    and condition-responsive (rules 11/13); zero fitted parameters. Pooling
    comes from ``reserve_config.caiso_pergen_structure``, the same helper
    ``_caiso_design`` builds the layout from, so the column order is
    identical by construction.
    """
    from market_sim.config.reserve_config import (
        _caiso_reserve_eligible,
        caiso_pergen_pool_ramp10,
        caiso_pergen_structure,
    )

    gen_idx, col, n_r, ramp10 = caiso_pergen_structure(fleet_arrays)
    online, group_of, grp_fast, _eligible = _pjm_plant_online_pattern(
        fleet_arrays,
        p0_dispatch,
        eligible=_caiso_reserve_eligible(fleet_arrays),
    )
    online_member = online[group_of[gen_idx]]  # (n_members, T) bool
    fast_member = grp_fast[group_of[gen_idx]]  # (n_members,) bool
    spin = caiso_pergen_pool_ramp10(
        fleet_arrays, gen_idx, col, n_r, ramp10, member_mask=online_member
    )
    nonspin = caiso_pergen_pool_ramp10(
        fleet_arrays,
        gen_idx,
        col,
        n_r,
        ramp10,
        member_mask=(~online_member) & fast_member[:, np.newaxis],
    )
    del online_member
    caps = np.vstack([spin, nonspin])
    del spin, nonspin
    return caps


def build_caiso_reserve_p1_prep(config, iso: str, fleet_arrays):
    """Return a ``p1_kwargs_prep`` hook for the CAISO online-scoped reserve split.

    ``caiso_reserve_online_scoped`` (GATED default off, the issue-#1492
    "correct build" increment): recomputes the ``(2*n_r, T)`` spin/non-spin
    product-split ramp caps from the P0 run pattern at the P0→P1 seam
    (:func:`caiso_pergen_sync_reserve_caps`) — the PJM
    ``pjm_reserve_pergen_sync`` seam convention, sharing the CAISO RA
    bridge's P0-commitment-state basis. Bounds-only kwargs override: energy
    availability is never masked (P1's free redispatch around the held
    reserve is what prices the opportunity cost), and the caps are computed
    on the fleet P1 actually solves (``p1_fleet_arrays`` — the RA-bridge
    fleet hook may floor or decommit availability first; the pool structure
    itself depends only on static fields, so it matches the design layout
    either way). ``None`` when the mechanism is off / the ISO is not CAISO,
    so every other path is byte-identical. Composes with the CAISO RA-bridge
    ``p1_fleet_prep`` (both fire on CAISO; P1 is a cold solve under either).
    The flag-composition errors (requires ``caiso_reserve_coopt``; exclusive
    with ``caiso_commitment_posture`` / ``caiso_locational_as_families``)
    are raised by ``ScenarioConfig`` and ``reserve_config._caiso_design``.
    """
    if not (
        iso == "CAISO"
        and getattr(config, "energy_reserve_coopt", False)
        and getattr(config, "caiso_reserve_coopt", False)
        and getattr(config, "caiso_reserve_online_scoped", False)
    ):
        return None

    def _kwargs_prep(r0, p1_fleet_arrays):
        # Recompute the product-split ramp caps on the P0 run pattern.
        # Bounds-only override: same LP dimensions, cold P1 (the seam
        # releases the P0 model first — the memory-friendly path).
        return {
            "reserve_pergen_ramp10": caiso_pergen_sync_reserve_caps(
                config, p1_fleet_arrays, r0.dispatch
            )
        }

    return _kwargs_prep


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


# ---------------------------------------------------------------------------
# SOCO gas-steam CAMPAIGN commitment floor (SOCO-53d)
# ---------------------------------------------------------------------------
def _soco_gas_st_campaign_floor(
    iso: str,
    fleet: list,
    fleet_arrays,
    p0_dispatch: np.ndarray,
) -> np.ndarray | None:
    """Compute the raw ``(n_gen, T)`` SOCO gas-steam campaign commitment floor.

    Runs the ISO-neutral detector ONCE, on ``gas_st`` alone, with **only two of
    its legs armed**: the measured minimum-RUN extension and the online-hours
    LSL state floor. The restart legs are deliberately left off
    (``startup_bridge=False``) because SOCO's boilers do not two-shift — 98.6 %
    of their measured downtime-hours sit in gaps longer than 72 h and only 150
    unit-hours across three years fall inside the 8 h min-down, which is why
    ``gas_commitment_bridge`` is recorded ``R`` for this ISO (SOCO-53). The
    commitment-real run screen (``startup_aware``) is also off, and for a
    stated reason rather than by omission: it asks whether an individual
    unit's margin against an LMP repays its startup, which is a MERCHANT test,
    and SOCO has no LMP, no offers and no market at all (the same ground on
    which ``tranche_startup_amortization`` is refused for this ISO).

    Level, horizon and membership are per-plant MEASURED statistics read from
    ``data.gas_st_campaign`` — nothing here is a scalar and nothing crosses an
    ISO boundary (rules 21 / 23 / 25). A plant absent from the artifact, or
    below its campaign-duty gate, carries ``min_load_frac_by_gen = 0`` and is
    scoped out of the mechanism entirely through the detector's own population
    gate (the miso-113 convention), so no class-name tuple is needed.

    Args:
        iso: The ISO name (selects the artifact).
        fleet: The dispatch fleet, aligned with ``fleet_arrays`` rows.
        fleet_arrays: The vectorized fleet.
        p0_dispatch: The base-cost P0 dispatch, ``(n_gen, T)``.

    Returns:
        The ``(n_gen, T)`` floor, or ``None`` when it floors nothing.
    """
    from market_sim.data.gas_st_campaign import load_gas_st_campaign_params
    from market_sim.model.commitment import caiso_ra_mustoffer_min_gen, find_runs

    params = load_gas_st_campaign_params(iso)
    if not params:
        return None
    n_gen = len(fleet)
    frac_by_gen = np.zeros(n_gen, dtype=float)
    min_run = np.zeros(n_gen, dtype=float)
    covered_mw = 0.0
    for g, gen in enumerate(fleet):
        if gen.fuel_type != "gas_st" or gen.plant_group.endswith("_CHP"):
            continue
        entry = params.get(int(getattr(gen, "plant_code", 0) or 0))
        if entry is None:
            continue
        frac_by_gen[g] = entry.min_load_frac
        min_run[g] = float(entry.min_run_hours)
        covered_mw += float(fleet_arrays.pmax[g])
    if not np.any(frac_by_gen > 0.0):
        logger.info(
            "SOCO gas-steam campaign commitment floor: artifact covers %d "
            "plant(s) but no fleet row matched — inert",
            len(params),
        )
        return None
    logger.info(
        "SOCO gas-steam campaign commitment floor: %d campaign-duty plant(s) "
        "(%s), %.1f MW of gas_st rows in population; per-plant min_load_frac "
        "%s, min_run %s h",
        len(params),
        sorted(params),
        covered_mw,
        {p: round(v.min_load_frac, 4) for p, v in sorted(params.items())},
        {p: v.min_run_hours for p, v in sorted(params.items())},
    )
    floor = caiso_ra_mustoffer_min_gen(
        p0_dispatch,
        fleet_arrays,
        fleet,
        0.0,
        startup_bridge=False,
        fuel_types=("gas_st",),
        min_run_hours=min_run,
        floor_online_hours=True,
        min_load_frac_by_gen=frac_by_gen,
        startup_aware=False,
    )
    if not np.any(floor > 0.0):
        logger.info(
            "SOCO gas-steam campaign commitment floor: detector produced no "
            "floor — inert (the P0 pattern has no run on any covered plant)"
        )
        return None
    # D-4 trace: with the online-hours leg armed a floored segment IS a
    # committed CAMPAIGN (runs and their min-run extensions fuse into one
    # block), so its length distribution is the direct evidence that what the
    # mechanism places are campaigns rather than gap fills. Reported against
    # each plant's own measured synchronized share, which is the window
    # declaration's evidence (rule 17 [R-FLOOR-WINDOW]).
    T = floor.shape[1]
    for code, entry in sorted(params.items()):
        rows = [
            g
            for g, gen in enumerate(fleet)
            if int(getattr(gen, "plant_code", 0) or 0) == code
            and gen.fuel_type == "gas_st"
        ]
        if not rows:
            continue
        plant_floor = floor[rows, :].sum(axis=0)
        binding = plant_floor > 0.0
        seg = np.array([e - s for s, e in find_runs(binding)])
        logger.info(
            "SOCO campaign floor, plant %d: %.4f TWh floored over %d h "
            "(%.3f of the year) in %d campaign block(s), median %.0f h; the "
            "plant's OWN measured synchronized share is %.3f",
            code,
            float(plant_floor.sum()) / 1e6,
            int(binding.sum()),
            float(binding.sum()) / max(T, 1),
            int(seg.size),
            float(np.median(seg)) if seg.size else 0.0,
            entry.sync_share,
        )
    logger.info(
        "SOCO gas-steam campaign commitment floor: %d unit-hours floored, "
        "%.4f TWh floor volume",
        int((floor > 0.0).sum()),
        float(floor.sum()) / 1e6,
    )
    return floor


def build_soco_gas_st_campaign_p1_prep(config, iso: str, fleet: list, fleet_arrays):
    """Return a ``p1_fleet_prep`` hook for the SOCO gas-steam campaign floor.

    The SOCO leg of the P1-native committed-state family (lane SOCO-53d), and
    the only one whose object is a multi-WEEK campaign rather than an overnight
    or midday gap: SOCO's gas boilers synchronize 5.0-9.7 times a year and stay
    on 64-92 % of all hours, while the model cycles the same plants 10-349
    times a year. Detector: :func:`_soco_gas_st_campaign_floor`; D-2
    attribution: ``MECH_SOCO_GAS_ST_CAMPAIGN``.

    Returns ``None`` when the mechanism is off or the ISO is not SOCO, so every
    other path is byte-identical. ISO-exclusive with the CAISO, ERCOT, NYISO,
    SPP, MISO and PJM P1-prep hooks by construction (each gates on its own
    ISO).
    """
    if not (
        getattr(config, "soco_gas_st_campaign_commitment", False) and iso == "SOCO"
    ):
        return None

    from market_sim.data.floor_mechanisms import MECH_SOCO_GAS_ST_CAMPAIGN

    def _fleet_prep(r0):
        campaign_floor = _soco_gas_st_campaign_floor(
            iso, fleet, fleet_arrays, r0.dispatch
        )
        if campaign_floor is None:
            return None
        return _bridge_floored_fleet(
            fleet_arrays, campaign_floor, MECH_SOCO_GAS_ST_CAMPAIGN
        )

    return _fleet_prep
