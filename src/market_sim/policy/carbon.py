"""Carbon pricing and emissions policy."""

from __future__ import annotations

from market_sim.config.constants import (
    CARBON_PRICE_PATHS,
    STATE_CARBON_PRICE_BY_ISO,
)
from market_sim.config.scenarios import ScenarioConfig


def state_carbon_price(config: ScenarioConfig, year: int) -> float | None:
    """Return the ISO's state carbon-program allowance price, or ``None``.

    Looks up :data:`STATE_CARBON_PRICE_BY_ISO` — the CA cap-and-trade
    (CARB) quarterly-auction settlement average for CAISO, and the RGGI
    quarterly-auction clearing-price average for NYISO and NEISO (all six
    New England states are RGGI members), 2023-2025 — so a backcast
    charges every in-state fossil unit the measured allowance cost without
    any per-scenario configuration. Returns ``None`` (caller falls through
    to the scenario carbon path) when ``config.state_carbon_pricing`` is
    off, the ISO has no registered program, or the year is outside the
    measured series (forward years need an allowance-price *trajectory*,
    which is deliberately not seeded here).

    Args:
        config: Scenario config supplying ``iso`` and the
            ``state_carbon_pricing`` toggle.
        year: Simulation year.

    Returns:
        The allowance price in $/tCO2, or ``None`` when not applicable.
    """
    if not getattr(config, "state_carbon_pricing", True):
        return None
    program = STATE_CARBON_PRICE_BY_ISO.get(config.iso)
    if program is None or year not in program:
        return None
    return float(program[year])


def resolve_carbon_price(config: ScenarioConfig, year: int) -> float:
    """Resolve the scalar carbon price ($/tCO2) for a given year.

    Thin, backward-compatible wrapper over the unified carbon-program resolver
    (:func:`market_sim.policy.cap_and_trade.resolve_carbon_program`); returns
    the resolution's ``.price_adder`` (the exogenous allowance-price channel).
    Precedence:

    1. A nonzero ``config.carbon_price`` scenario override is returned directly
       (flat trajectory), unchanged.
    2. The ISO's cap-and-trade program adder: the **measured** CARB/RGGI
       auction average in backcast years, or the **projected** program price in
       forecast years (the EM-6 seam fix — forecast carbon is no longer zero
       for a program ISO). CAISO/NYISO/NEISO carry a program; ERCOT/MISO do not.
    3. Fall through to ``config.carbon_price_path`` in
       :data:`CARBON_PRICE_PATHS` (linear-interpolated across knot years,
       nearest-endpoint clamp outside the range) when no program adder applies.

    **Final additive stage** (capx-D26, outside and after the precedence
    chain): ``config.carbon_price_delta`` is added to whatever the chain
    resolved. It exists so a paired instrument arm can construct a genuine
    carbon-price *increase over the resolved base trajectory* — under
    precedence (1) alone, a "high-carbon" arm on a program ISO silently
    REPLACED an escalating program trajectory with a flat value, i.e. a cut
    (the D23 premise inversion,
    ``docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md``). The
    default 0.0 is an exact no-op on every path; the field is forecast-only
    (``ScenarioConfig.__post_init__`` rule-13 guard) and never armed in a
    keeper or golden posture. The precedence semantics above are unchanged
    for every consumer at the default.

    The scalar returned here is the ISO-wide allowance price used by the
    capacity-evolution screen and the CARB border adder; the fractional-
    membership weighting for a partial-footprint program (PJM) is applied at the
    marginal-cost assembly seam (``data/fleet.py::assemble_mc``), not here.

    Args:
        config: Scenario config supplying the flat carbon price and the
            carbon path name.
        year: Simulation year.

    Returns:
        The carbon price in $/tCO2.
    """
    delta = float(getattr(config, "carbon_price_delta", 0.0) or 0.0)
    return _base_carbon_price(config, year) + delta


def _base_carbon_price(config: ScenarioConfig, year: int) -> float:
    """The precedence chain of :func:`resolve_carbon_price`, without the
    additive ``carbon_price_delta`` stage (see its docstring for the order)."""
    if config.carbon_price != 0:
        return float(config.carbon_price)

    # Program adder (measured backcast / projected forecast). Import here to
    # avoid a circular import at module load (cap_and_trade imports scenarios).
    from market_sim.policy.cap_and_trade import resolve_carbon_program

    resolution = resolve_carbon_program(config, year)
    if resolution is not None and resolution.price_adder:
        return float(resolution.price_adder)

    path = CARBON_PRICE_PATHS.get(config.carbon_price_path)
    if path is None:
        return 0.0

    knots = sorted(path)
    if year <= knots[0]:
        return float(path[knots[0]])
    if year >= knots[-1]:
        return float(path[knots[-1]])

    for lo, hi in zip(knots, knots[1:]):
        if lo <= year <= hi:
            frac = (year - lo) / (hi - lo)
            return float(path[lo] + frac * (path[hi] - path[lo]))
    return float(path[knots[-1]])
