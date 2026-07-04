"""Parametric sweep driver over premium caps (Mode A) or matching targets (Mode B).

Solves one portfolio LP per setpoint and collects the resulting
matching%-vs-premium frontier plus the selected build mix. This is the object a
user reads: "for a $1 / $2 / $5 / $7 / $10 / $20 premium, how hourly-matched can
we get, and with what portfolio?"
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.lp import PortfolioResult, solve_with_charge_policy
from lce_portfolio.resources import ResourceArrays


@dataclass
class SweepResult:
    """Collected results of a full sweep for one ISO."""

    iso: str
    mode: str
    results: list[PortfolioResult]

    @property
    def frontier(self) -> list[tuple[float, float, float]]:
        """List of ``(setpoint, matching_pct, premium)`` across the sweep."""
        return [(r.setpoint, r.matching_pct, r.premium) for r in self.results]


def run_sweep(
    config: PortfolioConfig,
    resources: ResourceArrays,
    load: np.ndarray,
    lmp: np.ndarray,
    cf: np.ndarray,
    *,
    emission_rate: np.ndarray | None = None,
) -> SweepResult:
    """Run the sweep implied by ``config.mode`` and return a :class:`SweepResult`.

    Mode A sweeps ``config.premium_deltas``; Mode B sweeps
    ``config.matching_targets``. Each setpoint is an independent LP solve.

    Every solve goes through :func:`~lce_portfolio.lp.solve_with_charge_policy`,
    so the ADR 0018 ``excess_headroom_only`` cut loop is applied transparently
    (all other policies pass straight through to a single ``build_and_solve``).

    ``emission_rate`` (keyword-only) is the optional ``(T,)`` hourly
    fossil-only average grid CO2 rate (tCO2/MWh, ADR 0013) threaded to every
    solve; ``None`` leaves residual-carbon reporting off.
    """
    setpoints = (
        config.premium_deltas
        if config.mode == "premium_cap"
        else config.matching_targets
    )
    results = [
        solve_with_charge_policy(
            config, resources, load, lmp, cf, float(sp), emission_rate=emission_rate
        )
        for sp in setpoints
    ]
    return SweepResult(iso=config.iso, mode=config.mode, results=results)
