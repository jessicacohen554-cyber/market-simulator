"""In-place P1-native floor re-solve for the dispatch LP.

Refactor-consolidation plan §7 H-1. The P1-native commitment-bridge hooks
(CAISO RA must-offer, ERCOT gas bridge — ``pipeline.commitment._bridge_floored_
fleet``) inject a ``min_gen`` floor for the P1 clearing solve. That floor enters
the LP only as the thermal P-block column bounds
(``bounds.build_variable_bounds``: ``min_gen`` overrides the P lower bound,
``pmax*availability`` is the P upper bound), so the P1 solve can ride the floor
in by mutating just those column bounds on the live P0 :class:`~market_sim.
model.lp.model.DispatchModel` (HiGHS ``changeColsBounds``) and warm-solving from
the retained P0 basis — the exact analogue of the shipped ``changeColsCost``
P0->P1 re-cost — instead of rebuilding the whole LP and cold-solving it.

Kept as a standalone helper (not a ``DispatchModel`` method) so this optional
solve-path optimisation is fully additive: it reads only the model's existing
public build state (``layout`` / ``fleet`` / ``T`` / ``_h`` / ``_coopt`` /
``_standalone_posture``) and never touches ``model.py``.
"""

import numpy as np


def availability_feeds_rows(model, ramp_present: bool) -> bool:
    """Whether generator availability feeds an LP *row* in ``model``.

    Availability enters the LP as the P-block column *upper* bound
    (``pmax*availability``) always, and additionally the ramp-row RHS
    (``rows._build_ramp_rows``) and the co-opt reserve-headroom / commitment-
    posture caps (``reserve_rows``, ``posture_ucap``). :func:`refloor_thermal_
    inplace` uses this to decide whether a floored fleet whose availability
    changed can be applied as a pure P-block column-bound edit (no availability-
    dependent row) or must fall back to a cold rebuild.

    Reads the model's existing co-opt / posture state; ramp presence is passed
    by the caller (the assembled dispatch kwargs) because ``ramp_gen_idx`` is
    not retained on the model.

    Args:
        model: The built :class:`~market_sim.model.lp.model.DispatchModel`.
        ramp_present: Whether the model was built with ramp constraints
            (``ramp_gen_idx`` in its dispatch kwargs).

    Returns:
        ``True`` when availability feeds a row (ramp / co-opt reserve /
        posture), ``False`` when it is only the P-block upper bound.
    """
    return bool(
        model._coopt
        or getattr(model, "_standalone_posture", False)
        or bool(model.layout.n_posture)
        or ramp_present
    )


def refloor_thermal_inplace(model, fleet, avail_in_rows: bool) -> bool:
    """Re-bound the thermal P[g,t] block of a live model in place for a floor.

    The floored fleet (from a P1-native commitment bridge) differs from the one
    ``model`` was built on only in ``min_gen`` (the injected floor) and, for
    feasibility, ``availability`` (raised where the floor would otherwise exceed
    ``pmax*availability``). Both enter the LP purely as the thermal P-block
    column bounds, so this recomputes those bounds exactly as
    ``bounds.build_variable_bounds`` does and applies them with a single
    ``changeColsBounds`` on the P columns; the caller then warm-solves the P1
    objective from the retained P0 basis.

    Valid only when the floored fleet's sole LP-relevant delta lands in the
    P-block column bounds. ``min_gen`` always qualifies (it is read nowhere but
    the P lower bound). ``availability`` also feeds the ramp-row RHS and the
    co-opt reserve/posture caps, so when it *changed* AND those rows are present
    (``avail_in_rows``) an in-place P-column edit would not reproduce a cold
    rebuild; the function then declines (returns ``False``, model untouched) so
    the caller can cold-rebuild. Must be called after the P0 solve and before
    the P1 solve.

    Args:
        model: A P0-solved :class:`~market_sim.model.lp.model.DispatchModel`
            whose optimal basis is retained for the warm P1 re-solve.
        fleet: The floored ``FleetArrays`` the P1 solve should use. It shares
            the model's generator ordering and ``pmax`` (the floor hooks only
            ``dataclasses.replace`` ``min_gen`` / ``availability`` / metadata).
        avail_in_rows: Whether availability feeds an LP row here — see
            :func:`availability_feeds_rows`.

    Returns:
        ``True`` when the P-block bounds were mutated in place (caller then
        warm-solves); ``False`` when the change is unsupported in place and the
        model was left untouched (caller cold-rebuilds).
    """
    built = model.fleet
    if fleet is built or fleet.n_gen != built.n_gen:
        return False
    avail = np.asarray(fleet.availability, dtype=float)
    if avail_in_rows and not np.array_equal(
        avail, np.asarray(built.availability, dtype=float)
    ):
        # Availability changed and it feeds an LP row here — a P-column edit
        # cannot reproduce a cold rebuild. Decline; the caller cold-solves.
        return False

    layout = model.layout
    T = model.T
    n_gen = layout.n_gen
    # Recompute the P-block bounds exactly as build_variable_bounds does: upper
    # = pmax*availability; lower = min_gen (or pmin broadcast) clipped to the
    # upper so a decommitted-hour zero upper forces P=0 rather than an
    # infeasible min_gen > upper.
    p_upper = np.asarray(fleet.pmax, dtype=float)[:, np.newaxis] * avail
    min_gen = getattr(fleet, "min_gen", None)
    if min_gen is not None:
        p_lower = np.asarray(min_gen, dtype=float)
    else:
        p_lower = np.broadcast_to(
            np.asarray(fleet.pmin, dtype=float)[:, np.newaxis], (n_gen, T)
        )
    p_lower = np.minimum(p_lower, p_upper)

    # Flat hour-major column indices of the P block (VariableLayout.p_col:
    # t*vph + _p_off + g), matching build_variable_bounds' (T, vph) ravel — so
    # the transposed (T, n_gen) bound arrays ravel into the same order.
    vph = layout.vars_per_hour
    idx = (
        np.arange(T, dtype=np.int32)[:, np.newaxis] * vph
        + layout._p_off
        + np.arange(n_gen, dtype=np.int32)[np.newaxis, :]
    ).ravel()
    lower = np.ascontiguousarray(p_lower.T, dtype=np.float64).ravel()
    upper = np.ascontiguousarray(p_upper.T, dtype=np.float64).ravel()
    model._h.changeColsBounds(idx.size, idx, lower, upper)
    # The floored fleet is what P1 solves on and what the caller persists as the
    # P1 floors (D-2 attribution) — mirror the cold path's rebuild.
    model.fleet = fleet
    return True
