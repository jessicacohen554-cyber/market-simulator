"""Shared test fixtures/builders for the LCE portfolio tests.

Keeps tests trivial-case-first and fast: a 24-hour horizon and hand-built
resource arrays, so no external data or 8760 solves are needed.
"""

from pathlib import Path

import numpy as np

from lce_portfolio.config import HOURS_PER_YEAR
from lce_portfolio.resources import ResourceArrays

# Committed real-CF fixture shared by test_profiles_real.py and any other test
# that needs the real-data profile path without touching the market-sim tree.
FIXTURE_PROFILES_DIR = Path(__file__).parent / "fixtures" / "profiles"


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


def cross_feature_system(T: int = HOURS_PER_YEAR):
    """5-resource hand-built system spanning every PP-02b LP extension at once.

    ``solar`` (generation) + ``split_ldes`` (power/energy-split storage,
    ADR 0006) + ``nuclear_existing``/``hydro_existing`` (going-forward PPA,
    ADR 0008; hydro also monthly-budget-flagged) + ``battery`` (fixed-duration
    storage). Hand-built rather than loaded from the real cost/caps CSVs so the
    coefficient scale stays small and IPM-friendly (the real ATB-scale
    coefficients combined with >=2 storage techs at full 8760 take 20-35s per
    solve — see PP-07 final report). Returns ``(resources, cf, load, lmp)``.
    Requires ``T == HOURS_PER_YEAR`` when hydro's monthly budget constraint is
    exercised (the LP raises otherwise); the default is the full calendar.
    """
    res = ResourceArrays(
        names=["solar", "split_ldes", "nuclear_existing", "hydro_existing", "battery"],
        is_storage=np.array([False, True, False, False, True]),
        is_split=np.array([False, True, False, False, False]),
        fixed_mwyr=np.array([100.0, 100.0, 0.0, 0.0, 50.0]),
        cost_energy_mwhyr=np.array([0.0, 10.0, 0.0, 0.0, 0.0]),
        vom=np.array([0.0, 0.0, 20.0, 25.0, 0.0]),
        cap_max_mw=np.array([1e5, 1e5, 2400.0, 300.0, 1e5]),
        cap_min_mw=np.array([0.0, 50.0, 0.0, 0.0, 0.0]),
        cf_assumed=np.array([1.0, 0.0, 1.0, 1.0, 0.0]),
        duration_h=np.array([0.0, 0.0, 0.0, 0.0, 4.0]),
        duration_min_h=np.array([0.0, 4.0, 0.0, 0.0, 0.0]),
        duration_max_h=np.array([0.0, 100.0, 0.0, 0.0, 0.0]),
        rte=np.array([1.0, 1.0, 1.0, 1.0, 0.9]),
        is_existing=np.array([False, False, True, True, False]),
        is_budget_hydro=np.array([False, False, False, True, False]),
    )
    hours = np.arange(T)
    hod = hours % 24
    cf = np.zeros((5, T))
    cf[0] = np.clip(np.sin((hod - 6) / 12.0 * np.pi), 0, None)  # solar diurnal
    cf[2] = 1.0  # nuclear_existing: always available
    cf[3] = 1.0  # hydro_existing: budget constraint governs, not CF
    load = 200.0 + 50.0 * np.clip(np.sin((hod - 8) / 24.0 * 2 * np.pi), 0, None)
    lmp = np.full(T, 40.0)
    return res, cf, load, lmp
