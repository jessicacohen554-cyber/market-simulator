"""Renewable portfolio standard constraints."""

from __future__ import annotations

from market_sim.config.constants import STATE_RPS_FLOORS


def get_rps_target(iso: str, year: int) -> float | None:
    """Return the clean-energy share required of an ISO in a given year.

    The floor trajectory in :data:`STATE_RPS_FLOORS` is defined at a few
    knot years; intermediate years are linearly interpolated. Years before
    the first knot take the first value, years after the last take the
    last value.

    Args:
        iso: ISO identifier (case-insensitive), e.g. ``"CAISO"``.
        year: Simulation year.

    Returns:
        The required clean-energy fraction, or ``None`` when the ISO has no
        renewable portfolio standard defined.
    """
    floors = STATE_RPS_FLOORS.get(iso.upper())
    if floors is None:
        return None

    knots = sorted(floors)
    if year <= knots[0]:
        return floors[knots[0]]
    if year >= knots[-1]:
        return floors[knots[-1]]

    for lo, hi in zip(knots, knots[1:]):
        if lo <= year <= hi:
            span = hi - lo
            frac = (year - lo) / span
            return floors[lo] + frac * (floors[hi] - floors[lo])
    return floors[knots[-1]]
