"""Renewable portfolio standard constraints."""

from __future__ import annotations

from market_sim.config.constants import (
    RPS_ELIGIBLE_FUELS_BY_ISO,
    STATE_RPS_ACP,
    STATE_RPS_FLOORS,
)


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


def get_rps_acp(iso: str) -> float | None:
    """Return the RPS Alternative Compliance Payment ceiling for an ISO.

    The ACP (:data:`STATE_RPS_ACP`) is the $/MWh price at which a
    load-serving entity buys out of the renewable portfolio standard when
    physical RECs are short. It is the price ceiling of the REC market, so the
    dispatch LP enters it as the cost of an RPS ACP escape column: this keeps
    the annual RPS row feasible when in-region wind+solar cannot reach the
    target and caps the row's dual (the REC shadow price) at this ceiling.

    Args:
        iso: ISO identifier (case-insensitive), e.g. ``"NEISO"``.

    Returns:
        The ACP ceiling in $/MWh, or ``None`` when the ISO has no RPS defined
        (in which case no ACP escape column is added and the LP is unchanged).
    """
    return STATE_RPS_ACP.get(iso.upper())


def get_rps_eligible_fuels(iso: str) -> tuple[str, ...] | None:
    """Return the statute-defined RPS-row eligible fuel set for an ISO.

    The set (:data:`RPS_ELIGIBLE_FUELS_BY_ISO`, cited per statute) names the
    fuel classes the ISO's governing *renewable-tier* statute counts toward
    its target. Wind and solar are the LP's zone columns and always count;
    names beyond them add the matching thermal-block generator columns to the
    RPS row (``model.lp.rows._resolve_rps_eligible_gen_idx``). FFR-7B Arm 1
    (rule 14 [R-ACCURATE]): the previous universal wind+solar-only convention
    under-counted NYISO by 20.2 pp (CLCPA counts existing hydro) and CAISO by
    7.1 pp (geothermal, biomass), pinning those rows' duals at the ACP ceiling
    (FFR-6B §8).

    Args:
        iso: ISO identifier (case-insensitive), e.g. ``"NYISO"``.

    Returns:
        The eligible fuel-name tuple, or ``None`` when the ISO has no
        entry — the row then keeps the wind+solar-only convention
        (byte-identical LP; PJM/MISO's folded-in convention is adjudicated
        sound to within ~2 pp, FFR-6B §8.2).
    """
    return RPS_ELIGIBLE_FUELS_BY_ISO.get(iso.upper())
