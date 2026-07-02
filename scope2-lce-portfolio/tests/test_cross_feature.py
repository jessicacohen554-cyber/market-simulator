"""Cross-feature integration tests.

Each earlier prompt pack tested its own feature (split storage, hydro budget,
additionality, strict hourly matching) against a 1-2 resource system. These
tests exercise how the accounting *composes* when several features are active
in the same solve: a split-storage tech, an existing (PPA) resource, a
monthly-budgeted existing resource, fixed-duration storage, and new
generation, all together.
"""

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve

from conftest import cross_feature_system


def _matching_identity(resources, load, r, additionality_only: bool) -> float:
    """Recompute matching_pct straight from ADR 0007/0008's definition.

    Under additionality (ADR 0008 as amended per audit LP-1), existing
    generation counts as unmatched only NET of the excess attributable to it
    (existing-first): exported existing energy is surplus, excluded entirely.
    """
    unmatched = float(r.grid_buy.sum())
    if additionality_only:
        existing_gen_t = r.gen[resources.is_existing].sum(axis=0)
        unmatched += float(np.clip(existing_gen_t - r.excess, 0.0, None).sum())
    return 1.0 - unmatched / float(load.sum())


def _net_cost_identity(resources, lmp, r, sale: float) -> float:
    """Recompute net_cost from its documented components (fixed + energy capex
    + vom + buys - sales)."""
    if r.split_names:
        split_idx = [r.resource_names.index(n) for n in r.split_names]
        energy_capex = float(
            resources.cost_energy_mwhyr[split_idx] @ r.build_energy_mwh
        )
    else:
        energy_capex = 0.0
    fixed = float(resources.fixed_mwyr @ r.build_mw)
    vom = float((resources.vom[:, None] * r.gen).sum())
    buys = float(lmp @ r.grid_buy)
    sales = sale * float(lmp @ r.excess)
    return fixed + energy_capex + vom + buys - sales


def _solve(additionality_only: bool, *, iso: str = "ERCOT", T: int | None = None):
    res, cf, load, lmp = (
        cross_feature_system() if T is None else cross_feature_system(T)
    )
    cfg = PortfolioConfig(
        iso=iso,
        hours=cf.shape[1],
        mode="premium_cap",
        excess_sale_fraction=0.5,
        additionality_only=additionality_only,
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=15.0)
    return cfg, res, load, lmp, r


def test_cross_feature_matching_and_cost_identities_additionality_off() -> None:
    """All 5 features active at once (additionality off): identities hold exactly.

    Existing (nuclear/hydro) generation counts toward matching here, so it
    should actually be dispatched. Kept at the full 8760-hour calendar (ERCOT,
    which has a real hydro-budget entry) as the one canonical full-year solve
    exercising all 5 composed features together, including the monthly hydro
    budget (ADR 0008) — lp.py requires T == HOURS_PER_YEAR whenever a
    budget-flagged resource is active for a known-budget ISO.
    """
    cfg, res, load, lmp, r = _solve(additionality_only=False)
    assert r.status == "Optimal"
    assert r.split_names == ["split_ldes"]
    assert r.build_energy_mwh.size == 1  # split storage was actually sized

    expected_matching = _matching_identity(res, load, r, additionality_only=False)
    assert np.isclose(r.matching_pct, expected_matching, rtol=1e-9, atol=1e-9)

    expected_net_cost = _net_cost_identity(res, lmp, r, cfg.excess_sale_fraction)
    assert np.isclose(expected_net_cost, r.net_cost, rtol=1e-6)

    existing_gen = float(r.gen[res.is_existing].sum())
    assert existing_gen > 0.0  # nuclear/hydro actually dispatched


def test_cross_feature_matching_and_cost_identities_additionality_on() -> None:
    """Same 5-feature system with additionality on: identities still hold exactly.

    The dispatch is re-optimized (existing generation now costs matching
    rather than helping it), so the numeric matching level need not match the
    off case — only the accounting identity is asserted here (both identities
    are generic accounting formulas, not budget-specific values). Uses a
    240-hour (10-day) horizon on the SAMPLE ISO (no hydro-budget table entry,
    so ADR 0008's monthly budget constraint is skipped and lp.py's
    T == HOURS_PER_YEAR requirement doesn't apply) rather than the full 8760 —
    the additionality_off test above already covers the full-year,
    budget-active combination once.
    """
    cfg, res, load, lmp, r = _solve(additionality_only=True, iso="SAMPLE", T=240)
    assert r.status == "Optimal"

    expected_matching = _matching_identity(res, load, r, additionality_only=True)
    assert np.isclose(r.matching_pct, expected_matching, rtol=1e-9, atol=1e-9)

    expected_net_cost = _net_cost_identity(res, lmp, r, cfg.excess_sale_fraction)
    assert np.isclose(expected_net_cost, r.net_cost, rtol=1e-6)


# --- Mode B strict hourly matching with split storage (item 2) -------------


def _solar_split_system(T: int, duration_max_h: float = 100.0):
    """Solar (day-only) + one power/energy-split storage tech."""
    from lce_portfolio.resources import ResourceArrays

    return ResourceArrays(
        names=["solar", "split"],
        is_storage=np.array([False, True]),
        is_split=np.array([False, True]),
        fixed_mwyr=np.array([1.0, 50.0]),
        cost_energy_mwhyr=np.array([0.0, 5.0]),
        vom=np.array([0.0, 0.0]),
        cap_max_mw=np.array([1e6, 1e6]),
        cap_min_mw=np.array([0.0, 0.0]),
        cf_assumed=np.array([1.0, 0.0]),
        duration_h=np.array([0.0, 0.0]),
        duration_min_h=np.array([0.0, 4.0]),
        duration_max_h=np.array([0.0, duration_max_h]),
        rte=np.array([1.0, 1.0]),
    )


def test_strict_hourly_matching_with_split_storage_honors_every_hour() -> None:
    """Mode B strict per-hour matching: ``grid_buy[t] <= (1-target)*load[t]``
    holds for *every* hour (not just the annual sum) with split storage active.

    Two-day (48h) horizon: solar available the first 12h of each day, load
    flat every hour, so the trough hours must be bridged by the split-storage
    tech every single night, not just on average across the two days.
    """
    T = 48
    res = _solar_split_system(T)
    cf = np.zeros((2, T))
    day_hours = [h for h in range(T) if h % 24 < 12]
    cf[0, day_hours] = 1.0
    load = np.full(T, 10.0)
    lmp = np.full(T, 50.0)
    target = 0.6
    cfg = PortfolioConfig(
        hours=T,
        mode="matching_target",
        strict_hourly_matching=True,
        excess_sale_fraction=0.0,
    )
    r = build_and_solve(cfg, res, load, lmp, cf, setpoint=target)
    assert r.status == "Optimal"
    assert "split" in r.split_names  # split-storage machinery actually engaged

    tol = 1e-6
    per_hour_cap = (1.0 - target) * load
    assert np.all(r.grid_buy <= per_hour_cap + tol)
    # the binding hours are the ones that matter most (night, cap tightest).
    assert r.grid_buy.max() <= per_hour_cap.max() + tol
