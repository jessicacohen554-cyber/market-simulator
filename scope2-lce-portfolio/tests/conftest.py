"""Shared test fixtures/builders for the LCE portfolio tests.

Keeps tests trivial-case-first and fast: a 24-hour horizon and hand-built
resource arrays, so no external data or 8760 solves are needed.
"""

import numpy as np

from lce_portfolio.resources import ResourceArrays


def solar_only(fixed_mwyr: float = 1000.0) -> ResourceArrays:
    """One generation resource ('solar'), no storage."""
    return ResourceArrays(
        names=["solar"],
        is_storage=np.array([False]),
        fixed_mwyr=np.array([fixed_mwyr]),
        vom=np.array([0.0]),
        cap_max_mw=np.array([1e6]),
        cap_min_mw=np.array([0.0]),
        cf_assumed=np.array([0.33]),
        duration_h=np.array([0.0]),
        rte=np.array([1.0]),
    )


def solar_plus_battery(
    fixed_solar: float = 1000.0, fixed_batt: float = 2000.0
) -> ResourceArrays:
    """One solar resource plus one 4-hour battery."""
    return ResourceArrays(
        names=["solar", "battery"],
        is_storage=np.array([False, True]),
        fixed_mwyr=np.array([fixed_solar, fixed_batt]),
        vom=np.array([0.0, 0.0]),
        cap_max_mw=np.array([1e6, 1e6]),
        cap_min_mw=np.array([0.0, 0.0]),
        cf_assumed=np.array([0.33, 0.0]),
        duration_h=np.array([0.0, 4.0]),
        rte=np.array([1.0, 0.9]),
    )


def daytime_solar_cf(n_res: int, T: int = 24, day=range(8, 16)) -> np.ndarray:
    """CF matrix: resource 0 = 1.0 during daytime hours, 0 otherwise; rest 0."""
    cf = np.zeros((n_res, T))
    cf[0, list(day)] = 1.0
    return cf
