"""Regression tests for the Mode A build-size tiebreak (ADR 0019).

Reproduces the CAISO 5-ISO validation-memo finding
(``docs/validation-2026-07-05-5iso-backcast-extension.md``): Mode A's pure
``min grid_buy`` objective carries zero weight on ``build_mw``, so once
matching saturates at 100% *below* a resource's cap, every build level between
"just enough" and the cap ties on the objective, and the premium constraint's
slack can absorb a much larger build without the objective noticing. Without a
tiebreak the crossover-off IPM (ADR 0003) returns an arbitrary point on that
degenerate face — varying with irrelevant details like the resource cap itself
— instead of the smallest capacity that attains the same matching/premium.

``config.build_tiebreak_epsilon`` (default ``1e-6``, ADR 0019) fixes this by
adding a flat per-MW cost to ``build_mw`` in Mode A only, small enough to never
move a build level the LP pins for a real reason (see the sizing rationale in
``config.py`` / ADR 0019).
"""

import numpy as np
import pytest

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import build_and_solve
from lce_portfolio.resources import ResourceArrays
from lce_portfolio.sweep import run_sweep


def _degenerate_wind_system(
    cap_max_mw: float,
) -> tuple[ResourceArrays, np.ndarray, np.ndarray, np.ndarray]:
    """24h system engineered to reproduce the CAISO saturate-before-cap pattern.

    A single wind-like resource with a CF that never drops to zero (0.25 floor,
    peaking at 1.0) so 100% matching is achievable at a finite build (exactly
    ``load / cf_floor = 400`` MW here) well below ``cap_max_mw``. A duck-curve-
    like LMP (peaking at $100/MWh) and full excess resale
    (``excess_sale_fraction=1.0``) make additional build's excess-sale revenue
    rich enough that net cost stays inside even a tight premium budget all the
    way to the cap -- mirroring "CAISO's own LMP series ... makes a massive
    wind build's excess-sale revenue rich enough to keep net cost within even a
    $1/MWh premium band" from the validation memo.
    """
    T = 24
    hours = np.arange(T)
    cf = np.zeros((1, T))
    cf[0] = 0.25 + 0.75 * np.clip(np.sin((hours - 6) / 12.0 * np.pi), 0, None)
    load = np.full(T, 100.0)
    lmp = 40.0 + 60.0 * np.clip(np.sin((hours - 14) / 24.0 * 2 * np.pi), 0, None)
    res = ResourceArrays(
        names=["wind"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([30.0]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([cap_max_mw]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([0.4]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
    )
    return res, cf, load, lmp


MIN_SUFFICIENT_BUILD_MW = (
    400.0  # load(100) / cf_floor(0.25), the true "just enough" build
)


def test_no_tiebreak_is_degenerate_across_resource_caps() -> None:
    """Characterization test: with epsilon=0, the arbitrary corner solution
    build_mw varies with the (economically irrelevant) resource cap even
    though matching and the premium setpoint are identical -- the signature of
    a degenerate optimal face, not a real economic optimum."""
    builds = []
    for cap in (450.0, 1000.0, 2000.0):
        res, cf, load, lmp = _degenerate_wind_system(cap)
        cfg = PortfolioConfig(
            hours=24,
            mode="premium_cap",
            excess_sale_fraction=1.0,
            build_tiebreak_epsilon=0.0,
            premium_deltas=(1.0,),
        )
        r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1.0)
        assert r.status == "Optimal"
        assert r.matching_pct == 1.0
        builds.append(r.build_mw[0])
    # The raw (no-tiebreak) solution is not pinned to the true minimum -- it
    # drifts with the cap, confirming the degeneracy this test suite guards
    # against (this assertion would fail if a future solver/scaling change
    # happened to make IPM always return the minimum-norm vertex; if so, the
    # tiebreak is merely redundant, not wrong).
    assert len(set(np.round(builds, 3))) > 1


def test_tiebreak_selects_minimum_sufficient_build_regardless_of_cap() -> None:
    """With the ADR 0019 tiebreak on, build_mw locks to the smallest capacity
    that attains 100% matching, independent of how far away the cap sits --
    the direct fix for the CAISO onshore-wind saturate-to-cap finding."""
    for cap in (450.0, 1000.0, 2000.0, 20000.0):
        res, cf, load, lmp = _degenerate_wind_system(cap)
        cfg = PortfolioConfig(
            hours=24,
            mode="premium_cap",
            excess_sale_fraction=1.0,
            build_tiebreak_epsilon=1e-6,
            premium_deltas=(1.0,),
        )
        r = build_and_solve(cfg, res, load, lmp, cf, setpoint=1.0)
        assert r.status == "Optimal"
        assert r.matching_pct == pytest.approx(1.0, abs=1e-6)
        assert r.build_mw[0] == pytest.approx(MIN_SUFFICIENT_BUILD_MW, rel=1e-3)
        # Nowhere near the cap, however large the cap is (the degenerate
        # symptom: CAISO's committed frontier built 16,000-19,500 MW against a
        # 20,000 MW cap for a facility whose real need was far smaller).
        assert r.build_mw[0] < cap * 0.5 or cap <= MIN_SUFFICIENT_BUILD_MW * 2


def test_tiebreak_frontier_is_monotonic_and_non_degenerate() -> None:
    """Full Mode A sweep with the tiebreak on: matching is non-decreasing, the
    premium constraint is honored, and build_mw stays at the true minimum
    sufficient capacity across every setpoint once matching saturates --
    instead of the memo's "100% matching at every premium from $1/MWh up,
    building onshore wind to its ... cap" pattern."""
    cap = 20000.0  # mirrors CAISO onshore_wind's ADR 0009 cap, in miniature
    res, cf, load, lmp = _degenerate_wind_system(cap)
    cfg = PortfolioConfig(
        hours=24,
        mode="premium_cap",
        excess_sale_fraction=1.0,
        build_tiebreak_epsilon=1e-6,
        premium_deltas=(1.0, 2.0, 5.0, 7.0, 10.0, 15.0, 20.0),
    )
    sweep = run_sweep(cfg, res, load, lmp, cf)
    assert all(r.status == "Optimal" for r in sweep.results)

    matches = [r.matching_pct for r in sweep.results]
    for a, b in zip(matches, matches[1:]):
        assert b >= a - 1e-4

    tol = 1e-3
    for r in sweep.results:
        assert r.premium <= r.setpoint + tol

    # Every setpoint saturates at 100% matching (the premium band is generous
    # relative to the toy system's true cost) -- exactly the CAISO pattern --
    # but build_mw no longer drifts toward the cap at any of them.
    builds = [r.build_mw[0] for r in sweep.results]
    assert all(m == pytest.approx(1.0, abs=1e-6) for m in matches)
    for b in builds:
        assert abs(b - MIN_SUFFICIENT_BUILD_MW) < 1.0
        assert b < cap * 0.05


def _structurally_capped_solar_system() -> tuple[
    ResourceArrays, np.ndarray, np.ndarray, np.ndarray
]:
    """24h solar-only system that can *never* reach 100% matching (cf is zero
    for 16 of 24 hours, no storage) -- a genuine, non-degenerate premium/
    matching tradeoff at every setpoint, unlike ``_degenerate_wind_system``
    (whose cf floor lets it always saturate). Sized (fixed cost meaningfully
    high relative to the daily premium budget) so low premium caps genuinely
    bind and grid_buy is real, not a numerical zero.
    """
    T = 24
    cf = np.zeros((1, T))
    cf[0, 8:16] = 1.0  # 8 sun hours
    load = np.full(T, 100.0)
    lmp = np.full(T, 40.0)
    res = ResourceArrays(
        names=["solar"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([5000.0]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([500.0]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([0.33]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
    )
    return res, cf, load, lmp


def test_tiebreak_does_not_change_non_degenerate_optimum() -> None:
    """When a resource's own physics (not just the premium budget) already
    pins the optimum -- here, solar structurally cannot exceed 8/24 matching,
    so grid_buy is genuinely > 0 and the premium constraint does real work --
    the tiebreak changes matching_pct and premium by only a numerically
    negligible amount. It must not distort an already-pinned frontier point,
    which is the normal (non-degenerate) regime the other five ISOs exhibit."""
    res, cf, load, lmp = _structurally_capped_solar_system()
    for setpoint in (0.5, 1.0, 2.0, 5.0):
        cfg_off = PortfolioConfig(
            hours=24,
            mode="premium_cap",
            excess_sale_fraction=0.5,
            build_tiebreak_epsilon=0.0,
            premium_deltas=(setpoint,),
        )
        cfg_on = PortfolioConfig(
            hours=24,
            mode="premium_cap",
            excess_sale_fraction=0.5,
            build_tiebreak_epsilon=1e-6,
            premium_deltas=(setpoint,),
        )
        r_off = build_and_solve(cfg_off, res, load, lmp, cf, setpoint=setpoint)
        r_on = build_and_solve(cfg_on, res, load, lmp, cf, setpoint=setpoint)
        assert r_off.status == r_on.status == "Optimal"
        assert r_off.matching_pct < 1.0  # confirms the tradeoff is real, not saturated
        assert abs(r_off.matching_pct - r_on.matching_pct) < 1e-6
        assert abs(r_off.premium - r_on.premium) < 1e-3
        assert abs(r_off.build_mw[0] - r_on.build_mw[0]) < 1e-3


def test_build_tiebreak_epsilon_config_validation() -> None:
    """Negative epsilon is rejected like every other epsilon-shaped field."""

    PortfolioConfig(build_tiebreak_epsilon=0.0)  # disables it, must not raise
    with pytest.raises(ValueError, match="build_tiebreak_epsilon"):
        PortfolioConfig(build_tiebreak_epsilon=-1e-9)
