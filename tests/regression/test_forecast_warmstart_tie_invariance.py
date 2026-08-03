"""Retirement-screen tie-invariance to marginal-tie dispatch reshuffles.

Warm-start backlog #4 (docs/cross-year-warmstart.md "Why the forecast path is
not wired"): cross-year LP warm-start reshuffles per-unit dispatch among units
tied at the marginal price. The LP is genuinely indifferent — objective, every
zonal price and TOTAL generation stay bit-identical — but the split among tied
units moves. On the forecast path that reshuffle used to feed the economic
retirement screen (``capacity_evolution/retirements.apply_economic_retirements``)
via per-unit REALIZED generation, so a wall-clock lever (warm-start) could tip a
retire/keep decision and change the next year's fleet. That is why forecast
cross-year warm-start was blocked (the ``ScenarioConfig.xyear_cache`` flag stays
default-off until an identical-trajectory A/B, owner gate D-9).

The screen's net-revenue MARGIN is already the basis-independent ATTAINABLE
margin (``max(0, price - mc, reserve) x pmax x availability`` — prices are LP
duals, bit-identical under warm start). Backlog #4 closes the one remaining
realized-dispatch reader: the attribute-revenue term (EAC / RPS / §45U), which
used to be credited on REALIZED annual generation, is now credited on the
ATTAINABLE in-merit generation (``cap x 1[price > mc]``), a function of
prices/mc/capacity only.

This test pins that the retire/keep decision is invariant to a
realized-generation reshuffle. The two dispatches below differ ONLY in the
nuclear unit's realized generation (same prices, mc and capacity) — the cold vs
warm marginal-tie reshuffle. Before the fix the screen returned loss counters
``{'N0': 1}`` (low/cold, unit failing toward retirement) vs ``{'N0': 0}``
(high/warm, unit surviving); after the fix both return ``{'N0': 0}``.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity_evolution.retirements import apply_economic_retirements

_T = 8760


def _nuclear(unit_id: str = "N0", pmax: float = 1000.0) -> Generator:
    """A minimal nuclear Generator the retirement screen can price."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="Z0",
        fuel_type="nuclear",
        pmax_mw=pmax,
        heat_rate=10.0,
    )


def _screen(fleet, arrays, realized_mw, prices, mc, config):
    """Run the economic-retirement screen with a flat realized dispatch."""
    dispatch = SimpleNamespace(dispatch=np.full((len(fleet), _T), realized_mw))
    # A fresh fleet list + empty loss dict each call so the two dispatches are
    # scored from the SAME entering state (the reshuffle is the only difference).
    return apply_economic_retirements(
        list(fleet),
        arrays,
        dispatch,
        prices,
        config,
        {},
        peak_demand=0.0,
        mc=mc,
        year=2035,
    )


def test_retirement_screen_invariant_to_dispatch_reshuffle():
    """A marginal-tie realized-generation reshuffle must not tip retire/keep.

    Same prices/mc/capacity, two different realized nuclear generations (the
    cold vs warm alternate-optima split). The attainable-generation attribute
    reader (backlog #4) makes the retire/keep decision — survivors AND the loss
    counter — identical; the pre-fix realized reader returned {'N0': 1} vs
    {'N0': 0}.
    """
    prices = np.full((1, _T), 6.0)  # strictly in-merit (> mc) every hour
    mc = np.full((1, _T), 5.0)
    # eac_price_nuclear sized so the attribute term is decision-relevant: the
    # unit clears going-forward cost on attainable generation but a realized
    # reader would straddle it across the reshuffle (see module docstring).
    # retirement_rule="legacy" pinned (D-1 flipped the default to "pipeline"
    # 2026-08-02). The basis-independence invariant under test is rule-agnostic,
    # but it is asserted THROUGH the legacy loss counter, which the R-NEW
    # pipeline does not keep — unpinned, both sides collapse to {} and the
    # assertion passes vacuously instead of exercising the screen.
    config = ScenarioConfig(
        iso="ERCOT", eac_price_nuclear=15.0, retirement_rule="legacy"
    )
    fleet = [_nuclear()]
    arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=_T)

    # The reshuffle is real: the two dispatches carry different realized annual
    # generation for the SAME LP optimum (prices/total gen bit-identical).
    low_mw, high_mw = 400.0, 950.0
    assert low_mw != high_mw

    surv_cold, loss_cold, _ = _screen(fleet, arrays, low_mw, prices, mc, config)
    surv_warm, loss_warm, _ = _screen(fleet, arrays, high_mw, prices, mc, config)

    assert [g.unit_id for g in surv_cold] == [g.unit_id for g in surv_warm], (
        "warm-start dispatch reshuffle changed which units the retirement screen "
        "retired — the screen is basis-dependent (backlog #4 regression)"
    )
    assert loss_cold == loss_warm, (
        "warm-start dispatch reshuffle changed the retire/keep loss counter: "
        f"cold(realized={low_mw})={loss_cold} vs warm(realized={high_mw})="
        f"{loss_warm}. The attribute-revenue term must be credited on attainable "
        "in-merit generation, not marginal-tie realized dispatch (backlog #4)."
    )
    # At these numbers the attainable reader retains the unit; the pre-fix
    # realized reader retired the low-dispatch (cold) case → {'N0': 1}.
    assert loss_cold == {"N0": 0}


def test_attainable_attribute_generation_ignores_realized_dispatch():
    """The screen output is a function of prices/mc/capacity, not realized MW.

    Sweeps the realized nuclear generation across its whole feasible range and
    asserts every retire/keep outcome is identical — the attribute-revenue
    generation the screen credits is the basis-independent attainable in-merit
    quantity, so no realized value can move the decision.
    """
    prices = np.full((1, _T), 6.0)
    mc = np.full((1, _T), 5.0)
    # retirement_rule="legacy" pinned (D-1 flipped the default to "pipeline"
    # 2026-08-02). The basis-independence invariant under test is rule-agnostic,
    # but it is asserted THROUGH the legacy loss counter, which the R-NEW
    # pipeline does not keep — unpinned, both sides collapse to {} and the
    # assertion passes vacuously instead of exercising the screen.
    config = ScenarioConfig(
        iso="ERCOT", eac_price_nuclear=15.0, retirement_rule="legacy"
    )
    fleet = [_nuclear()]
    arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=_T)

    outcomes = set()
    for realized in (0.0, 200.0, 500.0, 800.0, 1000.0):
        _, loss, _ = _screen(fleet, arrays, realized, prices, mc, config)
        outcomes.add(tuple(sorted(loss.items())))
    assert len(outcomes) == 1, (
        "retire/keep outcome varied with realized dispatch across the sweep "
        f"{outcomes} — the screen is not tie-invariant (backlog #4)"
    )
