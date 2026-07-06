"""Scope 2 Hourly LCE Portfolio Optimization Tool.

A self-contained, vendored decision tool that selects a portfolio of clean &
low-carbon energy (LCE) resources plus storage to match a company/facility 8760
load hour-by-hour at the lowest cost premium above wholesale energy prices.

This package is deliberately independent of ``market_sim``: it never imports the
market simulator. Any reused loader logic is copied under
:mod:`lce_portfolio.vendored` with re-sync notes. See ``PLAN.md`` and ``docs/``
for the design (the executed build-prompt history lives in git history).
"""

__version__ = "0.1.0"

from lce_portfolio.config import PortfolioConfig

__all__ = ["PortfolioConfig", "__version__"]
